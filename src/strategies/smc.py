import pandas as pd
import pandas_ta as ta
from src.strategies.base import BaseStrategy

class SMCStrategy(BaseStrategy):
    name = "smc"

    def apply(self, df, window=3):
        valid, error = self._validate_dataframe(df)
        if not valid or len(df) < 60:
            return {"signals": [], "meta": {"error": error}}

        df = df.copy()

        df["vwap"] = ta.vwap(df["high"], df["low"], df["close"], df["volume"])
        df["rvol"] = df["volume"] / ta.sma(df["volume"], length=20)

        # Strong BOS
        df["bos"] = df["close"] > df["high"].rolling(20).max().shift(1)

        # Anti fake breakout
        body = (df["close"] - df["open"]).abs()
        wick = df["high"] - df[["close", "open"]].max(axis=1)

        signals_df = df[
            (df["bos"]) &
            (df["rvol"] > 1.8) &
            (df["close"] > df["vwap"]) &
            (wick < body * 0.3)
        ].tail(3)

        signals = []
        for _, row in signals_df.iterrows():
            signals.append({
                "type": "bos_confirmed",
                "time": row["time"].isoformat(),
                "close": round(row["close"], 2),
                "vwap": round(row["vwap"], 2),
                "rvol": round(row["rvol"], 2)
            })

        return {
            "signals": signals,
            "meta": {
                "count": len(signals),
                "strategy": self.name
            }
        }
