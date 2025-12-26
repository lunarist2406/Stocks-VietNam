import pandas_ta as ta
from src.strategies.base import BaseStrategy


class OrderBlockStrategy(BaseStrategy):
    name = "order_block"

    def apply(self, df, inputs=None):
        inputs = inputs or {}

        volume_mult = inputs.get("volume_mult", 1.5)
        bos_lookback = inputs.get("bos_lookback", 5)
        wick_ratio = inputs.get("wick_ratio", 0.6)

        valid, error = self._validate_dataframe(df)
        if not valid or len(df) < 200:
            return {
                "signals": [],
                "plots": [],
                "meta": {"error": error}
            }

        df = df.copy()

        # =========================
        # Indicators
        # =========================
        df["ema50"] = ta.ema(df["close"], 50)
        df["ema200"] = ta.ema(df["close"], 200)
        df["rvol"] = df["volume"] / ta.sma(df["volume"], 20)

        prev_high = df["high"].rolling(bos_lookback).max().shift(1)
        df["bos"] = df["close"] > prev_high

        body = (df["close"] - df["open"]).abs()
        wick = df["high"] - df[["close", "open"]].max(axis=1)

        # =========================
        # Conditions
        # =========================
        cond = (
            (df["close"] < df["open"]) &                # bearish OB candle
            df["bos"].shift(-1).fillna(False) &         # BOS sau đó
            (df["rvol"] > volume_mult) &
            (df["ema50"] > df["ema200"]) &              # uptrend
            (wick < body * wick_ratio)
        )

        signals = []
        for _, row in df[cond].tail(3).iterrows():
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
            "plots": [
                {"type": "line", "column": "ema50"},
                {"type": "line", "column": "ema200"}
            ],
            "meta": {
                "strategy": self.name,
                "inputs": inputs,
                "count": len(signals),
                "notes": [] if signals else [
                    "No compressed order block",
                    "Volume not expanding",
                    "Trend not bullish"
                ]
            }
        }
