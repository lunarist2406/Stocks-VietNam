# src/strategies/smc.py

from src.strategies.base import BaseStrategy

class SMCStrategy(BaseStrategy):
    name = "smc"

    def apply(self, df, window=3):
        """
        Detect Break of Structure (BOS) using Smart Money Concepts
        
        Args:
            df: OHLCV DataFrame
            window: Window for swing high/low detection
        
        Returns:
            dict with signals and meta
        """
        try:
            # Validate
            valid, error = self._validate_dataframe(df)
            if not valid:
                return {"signals": [], "meta": {"error": error}}

            min_candles = window * 2 + 1
            if len(df) < min_candles:
                return {"signals": [], "meta": {"error": f"Cần ít nhất {min_candles} nến"}}

            df = df.copy()

            # Detect swing highs and lows
            # Swing high: highest point in window
            df["swing_high"] = (
                df["high"] == df["high"].rolling(window * 2 + 1, center=True, min_periods=1).max()
            )
            
            # Swing low: lowest point in window
            df["swing_low"] = (
                df["low"] == df["low"].rolling(window * 2 + 1, center=True, min_periods=1).min()
            )

            # Bullish BOS: close breaks above previous swing high
            df["bos"] = (
                (df["close"] > df["high"].shift(1)) &
                (df["swing_high"].shift(1) == True)
            )

            # Get BOS signals
            signals_df = df[df["bos"] == True].tail(3)
            
            # Remove NaN rows
            signals_df = signals_df.dropna(subset=["time", "close"])

            signals = []
            for _, row in signals_df.iterrows():
                signals.append({
                    "type": "bullish_bos",
                    "time": row["time"].isoformat() if hasattr(row["time"], 'isoformat') else str(row["time"]),
                    "open": round(float(row["open"]), 2),
                    "high": round(float(row["high"]), 2),
                    "low": round(float(row["low"]), 2),
                    "close": round(float(row["close"]), 2),
                    "volume": int(row["volume"])
                })

            return {
                "signals": signals,
                "meta": {
                    "type": "bullish_bos",
                    "count": len(signals),
                    "strategy": "smc",
                    "window": window,
                    "candles_analyzed": len(df)
                }
            }

        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                "signals": [],
                "meta": {"error": f"SMC error: {str(e)}"}
            }

