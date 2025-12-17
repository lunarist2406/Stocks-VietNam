# src/strategies/wyckoff.py

from src.strategies.base import BaseStrategy

class WyckoffStrategy(BaseStrategy):
    name = "wyckoff"

    def apply(self, df, range_window=50, volume_threshold_multiplier=1.0):
        """
        Detect Wyckoff Spring pattern
        
        A spring occurs when:
        1. Price briefly dips below range low
        2. Then closes back above range low
        3. Volume is above average (showing absorption)
        
        Args:
            df: OHLCV DataFrame
            range_window: Window to calculate range low
            volume_threshold_multiplier: Volume threshold
        
        Returns:
            dict with signals and meta
        """
        try:
            # Validate
            valid, error = self._validate_dataframe(df)
            if not valid:
                return {"signals": [], "meta": {"error": error}}

            if len(df) < range_window:
                return {"signals": [], "meta": {"error": f"Cần ít nhất {range_window} nến"}}

            df = df.copy()

            # Calculate range low (support level)
            df["range_low"] = df["low"].rolling(range_window, min_periods=1).min()
            
            # Calculate volume average
            df["vol_avg"] = df["volume"].rolling(20, min_periods=1).mean()

            # Spring conditions:
            # 1. Low dips below previous range low (tests support)
            # 2. Close recovers above previous range low (rejection)
            # 3. Volume above average (absorption)
            df["spring"] = (
                (df["low"] < df["range_low"].shift(1)) &
                (df["close"] > df["range_low"].shift(1)) &
                (df["volume"] > df["vol_avg"] * volume_threshold_multiplier)
            )

            # Get spring signals
            springs_df = df[df["spring"] == True].tail(3)
            
            # Remove NaN rows
            springs_df = springs_df.dropna(subset=["time", "close", "range_low"])

            signals = []
            for idx, row in springs_df.iterrows():
                range_low_value = float(row["range_low"])
                close_value = float(row["close"])
                
                # Skip invalid data
                if pd.isna(range_low_value) or pd.isna(close_value):
                    continue

                signals.append({
                    "type": "wyckoff_spring",
                    "time": row["time"].isoformat() if hasattr(row["time"], 'isoformat') else str(row["time"]),
                    "entry_hint": round(close_value, 2),
                    "range_low": round(range_low_value, 2),
                    "low": round(float(row["low"]), 2),
                    "close": round(close_value, 2),
                    "volume": int(row["volume"]),
                    "volume_avg": round(float(row["vol_avg"]), 2)
                })

            return {
                "signals": signals,
                "meta": {
                    "count": len(signals),
                    "strategy": "wyckoff",
                    "range_window": range_window,
                    "volume_threshold": volume_threshold_multiplier,
                    "candles_analyzed": len(df)
                }
            }

        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                "signals": [],
                "meta": {"error": f"Wyckoff error: {str(e)}"}
            }