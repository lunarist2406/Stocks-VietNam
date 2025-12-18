import pandas as pd
import pandas_ta as ta
from src.strategies.base import BaseStrategy

class WyckoffStrategy(BaseStrategy):
    name = "wyckoff"

    def apply(self, df, range_window=50):
        valid, error = self._validate_dataframe(df)
        if not valid or len(df) < range_window:
            return {"signals": [], "meta": {"error": error}}

        df = df.copy()

        df["range_low"] = df["low"].rolling(range_window).min()
        df["ema50"] = ta.ema(df["close"], length=50)
        df["rvol"] = df["volume"] / ta.sma(df["volume"], length=20)

        spring = (
            (df["low"] < df["range_low"].shift(1)) &
            (df["close"] > df["range_low"].shift(1)) &
            (df["rvol"] > 1.8) &
            (df["close"] > df["ema50"])
        )

        springs_df = df[spring].tail(3)

        signals = []
        for _, row in springs_df.iterrows():
            signals.append({
                "type": "wyckoff_spring",
                "time": row["time"].isoformat(),
                "close": round(row["close"], 2),
                "range_low": round(row["range_low"], 2),
                "rvol": round(row["rvol"], 2)
            })

        return {
            "signals": signals,
            "meta": {
                "count": len(signals),
                "strategy": self.name
            }
        }
