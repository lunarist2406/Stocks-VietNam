# src/services/trade_signal_builder.py

import pandas as pd


class TradeSignalBuilder:
    """
    Build final trade signal từ output StrategyEngine
    
    Flow:
    1. Xác định bias từ SMC (BOS)
    2. Entry từ Order Block
    3. TP từ structure
    4. Validate RR
    5. Optional: Wyckoff tăng confidence
    """

    def __init__(self, rr_min=2.0):
        self.rr_min = rr_min

    def _validate_inputs(self, df, strategy_results):
        """Validate inputs"""
        if df is None or df.empty:
            return False, "DataFrame rỗng"
        
        if not strategy_results or not isinstance(strategy_results, dict):
            return False, "Strategy results không hợp lệ"
        
        required_cols = ["time", "open", "high", "low", "close", "volume"]
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            return False, f"Thiếu cột: {', '.join(missing)}"
        
        if len(df) < 20:
            return False, "Cần ít nhất 20 nến để phân tích"
        
        return True, None

    def build(self, df, strategy_results):
        """
        Build trade signal từ strategy results
        
        Args:
            df: DataFrame với OHLCV data
            strategy_results: Output của StrategyEngine.run(df)
        
        Returns:
            dict: Trade signal hoặc None nếu không có setup
        """
        # Validate
        valid, error = self._validate_inputs(df, strategy_results)
        if not valid:
            print(f"[TradeSignal] Validation failed: {error}")
            return None

        df = df.copy()
        reasons = []
        bias = None
        entry = sl = tp = None

        # ==================================================
        # 1. Xác định bias từ SMC (BOS)
        # ==================================================
        smc = strategy_results.get("smc")
        if smc and smc.get("signals"):
            bias = "bullish"
            reasons.append("BOS confirmed (SMC)")
        else:
            print("[TradeSignal] No SMC bias detected")
            return None

        # ==================================================
        # 2. Entry từ Order Block
        # ==================================================
        ob = strategy_results.get("order_block")
        if not ob or not ob.get("signals"):
            print("[TradeSignal] No Order Block found")
            return None

        last_ob = ob["signals"][-1]
        zone = last_ob.get("zone")
        
        if not zone or "low" not in zone or "high" not in zone:
            print("[TradeSignal] Invalid Order Block zone")
            return None

        entry = (zone["low"] + zone["high"]) / 2
        sl = zone["low"]
        reasons.append("Bullish Order Block")

        # ==================================================
        # 3. TP từ cấu trúc giá gần nhất
        # ==================================================
        try:
            # Tìm recent high trong 20 nến gần nhất
            recent_high = df["high"].rolling(20, min_periods=1).max().iloc[-1]
            
            # Nếu recent high quá gần entry, tìm xa hơn
            if recent_high < entry * 1.02:  # Phải cao hơn entry ít nhất 2%
                recent_high = df["high"].rolling(50, min_periods=1).max().iloc[-1]
            
            tp = recent_high
            
        except Exception as e:
            print(f"[TradeSignal] Error calculating TP: {e}")
            return None

        # ==================================================
        # 4. RR check
        # ==================================================
        risk = entry - sl
        reward = tp - entry

        if risk <= 0:
            print("[TradeSignal] Invalid risk (entry <= SL)")
            return None

        if reward <= 0:
            print("[TradeSignal] Invalid reward (TP <= entry)")
            return None

        rr = reward / risk
        
        if rr < self.rr_min:
            print(f"[TradeSignal] RR too low: {rr:.2f} < {self.rr_min}")
            return None

        # ==================================================
        # 5. Optional: Wyckoff tăng confidence
        # ==================================================
        wyckoff = strategy_results.get("wyckoff")
        confidence = 0.6

        if wyckoff and wyckoff.get("signals"):
            confidence += 0.15
            reasons.append("Wyckoff Spring")

        # ==================================================
        # 6. Build final signal
        # ==================================================
        return {
            "bias": bias,
            "entry": round(float(entry), 2),
            "stop_loss": round(float(sl), 2),
            "take_profit": round(float(tp), 2),
            "risk": round(float(risk), 2),
            "reward": round(float(reward), 2),
            "rr": round(float(rr), 2),
            "confidence": round(min(confidence, 0.95), 2),
            "reasons": reasons,
            "meta": {
                "candles_analyzed": len(df),
                "recent_high": round(float(recent_high), 2),
                "ob_zone": {
                    "low": round(float(zone["low"]), 2),
                    "high": round(float(zone["high"]), 2)
                }
            }
        }