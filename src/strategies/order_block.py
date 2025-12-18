import pandas as pd
import pandas_ta as ta
from src.strategies.base import BaseStrategy

class OrderBlockStrategy(BaseStrategy):
    name = "order_block"

    def apply(self, df, volume_threshold_multiplier=1.5):
        valid, error = self._validate_dataframe(df)
        if not valid or len(df) < 50:
            return {"signals": [], "meta": {"error": error}}

        df = df.copy()

        # Trend filter
        df["ema50"] = ta.ema(df["close"], length=50)
        df["ema200"] = ta.ema(df["close"], length=200)

        # Volume
        df["rvol"] = df["volume"] / ta.sma(df["volume"], length=20)

        # Structure
        df["bos"] = df["close"] > df["high"].rolling(5).max().shift(1)

        # Anti pull-up candle
        body = (df["close"] - df["open"]).abs()
        wick = df["high"] - df[["close", "open"]].max(axis=1)

        conditions = (
            (df["close"] < df["open"]) &                      # bearish candle
            (df["bos"].shift(-1)) &
            (df["rvol"] > volume_threshold_multiplier) &
            (df["ema50"] > df["ema200"]) &                    # uptrend only
            (wick < body * 0.4)                                # anti xả
        )

        ob_df = df[conditions].tail(3)

        signals = []
        for _, row in ob_df.iterrows():
            signals.append({
                "type": "bullish_order_block",
                "time": row["time"].isoformat(),
                "zone": {
                    "low": round(row["low"], 2),
                    "high": round(row["open"], 2)
                },
                "rvol": round(row["rvol"], 2)
            })

        return {
            "signals": signals,
            "meta": {
                "count": len(signals),
                "strategy": self.name
            }
        }
