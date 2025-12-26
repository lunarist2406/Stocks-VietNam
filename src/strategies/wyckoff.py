import pandas_ta as ta
from src.strategies.base import BaseStrategy


class WyckoffStrategy(BaseStrategy):
    name = "wyckoff"

    def apply(self, df, inputs=None):
        inputs = inputs or {}

        window = inputs.get("range_window", 30)
        rvol_thres = inputs.get("rvol", 1.5)

        valid, error = self._validate_dataframe(df)
        if not valid or len(df) < window:
            return {
                "signals": [],
                "plots": [],
                "meta": {"error": error}
            }

        df = df.copy()

        # =========================
        # Indicators
        # =========================
        df["range_low"] = df["low"].rolling(window).min()
        df["ema50"] = ta.ema(df["close"], 50)
        df["rvol"] = df["volume"] / ta.sma(df["volume"], 20)

        # =========================
        # Spring (relaxed)
        # =========================
        spring = (
            (df["low"] < df["range_low"].shift(1) * 1.001) &
            (df["close"] > df["range_low"].shift(1)) &
            (df["rvol"] > rvol_thres) &
            (df["close"] > df["ema50"])
        )

        signals = []
        for _, row in df[spring].tail(3).iterrows():
            signals.append({
                "type": "wyckoff_spring",
                "time": row["time"].isoformat(),
                "close": round(row["close"], 2),
                "range_low": round(row["range_low"], 2),
                "rvol": round(row["rvol"], 2)
            })

        return {
            "signals": signals,
            "plots": [
                {"type": "line", "column": "range_low"},
                {"type": "line", "column": "ema50"}
            ],
            "meta": {
                "strategy": self.name,
                "inputs": inputs,
                "count": len(signals),
                "notes": [] if signals else [
                    "No spring detected",
                    "Volume not confirming",
                    "Below EMA50"
                ]
            }
        }
