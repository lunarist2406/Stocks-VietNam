# src/services/trade_signal_builder.py

import pandas_ta as ta


class TradeSignalBuilder:
    def __init__(self, rr_min=2.0, shark_min_score=70):
        self.rr_min = rr_min
        self.shark_min_score = shark_min_score

    # ==================================================
    # VALIDATION
    # ==================================================
    def _validate_inputs(self, df, strategy_results):
        if df is None or df.empty:
            return False, "DataFrame rỗng"
        if not isinstance(strategy_results, dict):
            return False, "Strategy results không hợp lệ"
        required_cols = ["time", "open", "high", "low", "close", "volume"]
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            return False, f"Thiếu cột: {', '.join(missing)}"
        if len(df) < 50:
            return False, "Cần ít nhất 50 nến"
        return True, None

    # ==================================================
    # INDICATORS
    # ==================================================
    def _apply_indicators(self, df):
        df["ema10"] = ta.ema(df["close"], length=10)
        df["ema21"] = ta.ema(df["close"], length=21)
        df["atr"] = ta.atr(df["high"], df["low"], df["close"], length=14)
        df["rsi"] = ta.rsi(df["close"], length=14)
        return df

    # ==================================================
    # STRATEGY HELPERS
    # ==================================================
    def _has_signals(self, strategy_results, key):
        block = strategy_results.get(key)
        if not isinstance(block, dict):
            return False
        signals = block.get("signals")
        if signals is None:
            return False
        if hasattr(signals, "empty"):
            return not signals.empty
        if isinstance(signals, list):
            return len(signals) > 0
        return False

    # ==================================================
    # MAIN BUILDER
    # ==================================================
    def build(self, df, strategy_results):
        valid, error = self._validate_inputs(df, strategy_results)
        if not valid:
            return {"error": error, "shark_score": 0, "reasons": [], "debug": {}}

        df = self._apply_indicators(df.copy())
        last = df.iloc[-1]

        reasons = []
        debug = {}
        shark_score = 0
        bias = "neutral"

        # ==================================================
        # 1. EMA CONTEXT (context score, không quyết định)
        # ==================================================
        ema10 = float(last["ema10"])
        ema21 = float(last["ema21"])

        ema_diff = abs(ema10 - ema21)

        if ema10 > ema21:
            shark_score += 10
            bias = "bullish"
            reasons.append("EMA10 > EMA21 (bullish context)")
            debug["ema"] = {
                "ema10": round(ema10, 2),
                "ema21": round(ema21, 2),
                "pass": True,
                "score": 10,
            }
        elif ema_diff < last["atr"] * 0.2:
            shark_score += 3
            reasons.append("EMA flat nhưng có drift")
            debug["ema"] = {
                "ema10": round(ema10, 2),
                "ema21": round(ema21, 2),
                "pass": True,
                "score": 3,
            }
        else:
            debug["ema"] = {
                "ema10": round(ema10, 2),
                "ema21": round(ema21, 2),
                "pass": False,
                "score": 0,
            }

        # ==================================================
        # 1.5 DRIFT CONTEXT (sideway / accumulation)
        # ==================================================
        lookback = 30
        recent = df.tail(lookback)

        price_change = recent["close"].iloc[-1] - recent["close"].iloc[0]
        range_size = recent["high"].max() - recent["low"].min()

        if price_change > 0 and price_change / max(range_size, 1e-6) > 0.6:
            shark_score += 5
            if bias == "neutral":
                bias = "bullish"
            reasons.append("Giá có upward drift (low volatility)")
            debug["drift"] = {
                "pass": True,
                "price_change": round(price_change, 4),
                "range": round(range_size, 4),
                "ratio": round(price_change / max(range_size, 1e-6), 2),
                "score": 5,
            }
        else:
            debug["drift"] = {
                "pass": False,
                "price_change": round(price_change, 4),
                "range": round(range_size, 4),
            }


        # ==================================================
        # 2. SETUP DETECTION (phải có ít nhất 1 setup)
        # ==================================================
        has_setup = False
        entry = None

        # --- SMC ---
        if self._has_signals(strategy_results, "smc"):
            shark_score += 20
            has_setup = True
            reasons.append("BOS confirmed (SMC)")
            debug["smc"] = {"pass": True, "score": 20}
        else:
            debug["smc"] = {"pass": False, "score": 0}

        # --- Order Block ---
        ob = strategy_results.get("order_block", {})
        ob_signals = ob.get("signals", [])

        if ob_signals:
            last_ob = ob_signals[-1]
            zone = last_ob.get("zone", {})
            zl, zh = zone.get("low"), zone.get("high")

            if zl and zh:
                entry = round((zl + zh) / 2, 2)
                shark_score += 20
                has_setup = True
                reasons.append("Order Block hợp lệ")
                debug["order_block"] = {
                    "pass": True, "score": 20, "zone_low": zl, "zone_high": zh
                }
            else:
                debug["order_block"] = {"pass": False, "score": 0}
        else:
            debug["order_block"] = {"pass": False, "score": 0}

        # --- Wyckoff ---
        if self._has_signals(strategy_results, "wyckoff"):
            shark_score += 15
            has_setup = True
            reasons.append("Wyckoff Spring / Absorption")
            debug["wyckoff"] = {"pass": True, "score": 15}
        else:
            debug["wyckoff"] = {"pass": False, "score": 0}

        # ❌ Không có setup thì dừng sớm
        if not has_setup:
            return {
                "bias": bias,
                "shark_score": shark_score,
                "confidence": round(min(shark_score / 100, 0.95), 2),
                "reasons": reasons or ["Không có setup hợp lệ"],
                "note": "No trade – thiếu setup",
                "debug": debug,
            }

        # Nếu không có OB thì fallback entry = close
        if entry is None:
            entry = float(last["close"])

        # ==================================================
        # 3. RISK MODEL + RR GATE
        # ==================================================
        atr = float(last["atr"])
        sl = round(entry - atr * 1.2, 2)
        tp = round(entry + atr * 2.5, 2)

        risk = entry - sl
        reward = tp - entry
        rr = reward / risk if risk > 0 else 0

        debug["rr"] = {"rr": rr}

        if rr < self.rr_min:
            reasons.append(f"RR không đạt ({rr:.2f})")
            return {
                "bias": bias,
                "entry": entry,
                "stop_loss": sl,
                "take_profit": tp,
                "rr": round(rr, 2),
                "shark_score": shark_score,
                "confidence": round(min(shark_score / 100, 0.95), 2),
                "reasons": reasons,
                "note": "No trade – RR không đạt",
                "debug": debug,
            }

        shark_score += 2  # RR chỉ là bonus nhỏ
        reasons.append(f"RR đạt ({rr:.2f})")

        # ==================================================
        # 4. RSI CONTEXT (mềm hơn)
        # ==================================================
        rsi = float(last["rsi"])
        if 45 <= rsi <= 65:
            shark_score += 5
            reasons.append("RSI ổn định (drift)")
            debug["rsi"] = {"rsi": rsi, "pass": True, "score": 5}
        else:
            debug["rsi"] = {"rsi": rsi, "pass": False, "score": 0}

        # ==================================================
        # FINAL
        # ==================================================
        return {
            "bias": bias,
            "entry": entry,
            "stop_loss": sl,
            "take_profit": tp,
            "rr": round(rr, 2),
            "shark_score": shark_score,
            "confidence": round(min(shark_score / 100, 0.95), 2),
            "reasons": reasons,
            "meta": {
                "ema10": round(ema10, 2),
                "ema21": round(ema21, 2),
                "atr": round(atr, 2),
                "rsi": round(rsi, 2),
            },
            "note": (
                "Đạt ngưỡng" if shark_score >= self.shark_min_score
                else f"Chưa đạt ngưỡng {self.shark_min_score}, hiện tại {shark_score}"
            ),
            "debug": debug,
        }
