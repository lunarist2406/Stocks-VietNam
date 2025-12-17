# src/strategies/order_block.py

from src.strategies.base import BaseStrategy

class OrderBlockStrategy(BaseStrategy):
    name = "order_block"

    def apply(self, df, volume_threshold_multiplier=1.0):
        """
        Detect Bullish Order Blocks
        
        Args:
            df: OHLCV DataFrame
            volume_threshold_multiplier: Volume must be > avg * this multiplier
        
        Returns:
            dict with signals and meta
        """
        try:
            # Validate
            valid, error = self._validate_dataframe(df)
            if not valid:
                return {"signals": [], "meta": {"error": error}}

            if len(df) < 20:
                return {"signals": [], "meta": {"error": "Cần ít nhất 20 nến"}}

            df = df.copy()

            # Calculate BOS (Break of Structure)
            # Bullish BOS: close breaks previous high
            df["bos"] = df["close"] > df["high"].shift(1)

            # Calculate volume average
            df["vol_avg"] = df["volume"].rolling(20, min_periods=1).mean()

            # Bullish Order Block conditions:
            # 1. Bearish candle (close < open)
            # 2. Next candle has BOS
            # 3. Volume above average
            conditions = (
                (df["close"] < df["open"]) &           # Bearish candle
                (df["bos"].shift(-1) == True) &        # Next candle breaks high
                (df["volume"] > df["vol_avg"] * volume_threshold_multiplier)  # High volume
            )

            # Get potential order blocks
            ob_df = df[conditions].tail(3)

            # Remove rows with NaN in critical fields
            ob_df = ob_df.dropna(subset=["time", "open", "low"])

            zones = []
            for _, row in ob_df.iterrows():
                # Order Block zone: from low to open of the bearish candle
                zone_low = float(row["low"])
                zone_high = float(row["open"])
                
                # Skip invalid zones
                if zone_low >= zone_high or pd.isna(zone_low) or pd.isna(zone_high):
                    continue

                zones.append({
                    "type": "bullish_order_block",
                    "time": row["time"].isoformat() if hasattr(row["time"], 'isoformat') else str(row["time"]),
                    "zone": {
                        "low": round(zone_low, 2),
                        "high": round(zone_high, 2)
                    },
                    "volume": int(row["volume"]),
                    "volume_avg": round(float(row["vol_avg"]), 2)
                })

            return {
                "signals": zones,
                "meta": {
                    "count": len(zones),
                    "strategy": "order_block",
                    "candles_analyzed": len(df),
                    "volume_threshold": volume_threshold_multiplier
                }
            }

        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                "signals": [],
                "meta": {"error": f"OrderBlock error: {str(e)}"}
            }