import pandas_ta as ta
import math


class TradeSignalBuilder:
    def __init__(self, rr_min=2.0, shark_min_score=70):
        self.rr_min = rr_min
        self.shark_min_score = shark_min_score

    # ==================================================
    # UTILS
    # ==================================================
    def _safe_float(self, v):
        if v is None or isinstance(v, bool):
            return None
        if isinstance(v, (int, float)) and not math.isnan(v):
            return float(v)
        return None

    # ==================================================
    # VALIDATION
    # ==================================================
    def _validate(self, df, strategy_results):
        if df is None or df.empty:
            return False, "DataFrame rỗng"

        if not isinstance(strategy_results, dict):
            return False, "Strategy results không hợp lệ"

        required = {"time", "open", "high", "low", "close", "volume"}
        if not required.issubset(df.columns):
            return False, f"Thiếu cột: {required - set(df.columns)}"

        if len(df) < 50:
            return False, "Không đủ nến"

        return True, None

    # ==================================================
    # INDICATORS
    # ==================================================
    def _apply_indicators(self, df):
        df["ema10"] = ta.ema(df["close"], 10)
        df["ema21"] = ta.ema(df["close"], 21)
        df["atr"] = ta.atr(df["high"], df["low"], df["close"], 14)
        return df

    # ==================================================
    # CONTEXT
    # ==================================================
    def _context_score(self, df, debug, reasons):
        score = 0
        last = df.iloc[-1]

        ema10 = self._safe_float(last["ema10"])
        ema21 = self._safe_float(last["ema21"])
        atr = self._safe_float(last["atr"])

        if ema10 and ema21 and atr:
            if ema10 > ema21:
                score += 10
                reasons.append("EMA bullish")
                debug["ema"] = "bullish"
            elif abs(ema10 - ema21) < atr * 0.2:
                score += 3
                reasons.append("EMA flat")
                debug["ema"] = "flat"

        # Drift
        recent = df.tail(30)
        move = recent["close"].iloc[-1] - recent["close"].iloc[0]
        rng = recent["high"].max() - recent["low"].min()

        if rng > 0 and move / rng > 0.6:
            score += 5
            reasons.append("Upward drift")
            debug["drift"] = True

        return score

    # ==================================================
    # SETUPS
    # ==================================================
    def _detect_setups(self, strategy_results, debug, reasons):
        score = 0
        entry = None

        if strategy_results.get("smc", {}).get("signals"):
            score += 20
            reasons.append("SMC BOS")
            debug["smc"] = True

        ob = strategy_results.get("order_block", {}).get("signals", [])
        if ob:
            zone = ob[-1].get("zone", {})
            if zone.get("low") and zone.get("high"):
                entry = round((zone["low"] + zone["high"]) / 2, 2)
                score += 20
                reasons.append("Order Block")
                debug["order_block"] = True

        if strategy_results.get("wyckoff", {}).get("signals"):
            score += 15
            reasons.append("Wyckoff")
            debug["wyckoff"] = True

        return score, entry

    # ==================================================
    # RISK
    # ==================================================
    def _risk(self, entry, last, reasons, debug):
        atr = self._safe_float(last["atr"])
        if not atr:
            return None

        sl = round(entry - atr * 1.2, 2)
        tp = round(entry + atr * 2.5, 2)

        rr = (tp - entry) / (entry - sl) if entry > sl else 0
        debug["rr"] = round(rr, 2)

        if rr < self.rr_min:
            reasons.append("RR không đạt")
            return None

        return sl, tp, rr

    # ==================================================
    # MAIN
    # ==================================================
    def build(self, df, strategy_results):
        ok, error = self._validate(df, strategy_results)
        if not ok:
            return {
                "action": "no_trade",
                "reason": error,
                "confidence": 0,
                "shark_score": 0,
            }

        df = self._apply_indicators(df.copy())
        last = df.iloc[-1]

        debug = {}
        reasons = []
        shark_score = 0

        # CONTEXT
        shark_score += self._context_score(df, debug, reasons)

        # SETUPS
        setup_score, entry = self._detect_setups(strategy_results, debug, reasons)
        shark_score += setup_score

        if setup_score == 0:
            return {
                "action": "no_trade",
                "bias": "neutral",
                "reason": "No structure / No setup",
                "confidence": round(shark_score / 100, 2),
                "shark_score": shark_score,
                "debug": debug,
            }

        if entry is None:
            entry = float(last["close"])

        risk = self._risk(entry, last, reasons, debug)
        if not risk:
            return {
                "action": "no_trade",
                "bias": "neutral",
                "reason": "RR không đạt",
                "confidence": round(shark_score / 100, 2),
                "shark_score": shark_score,
                "debug": debug,
            }

        sl, tp, rr = risk
        shark_score += 2

        return {
            "action": "buy",
            "bias": "bullish",
            "entry": entry,
            "stop_loss": sl,
            "take_profit": tp,
            "rr": round(rr, 2),
            "confidence": round(min(shark_score / 100, 0.95), 2),
            "shark_score": shark_score,
            "reasons": reasons,
            "debug": debug,
        }
