import pandas_ta as ta
from src.strategies.base import BaseStrategy


class SMCStrategy(BaseStrategy):
    name = "smc"

    def apply(self, df, inputs=None):
        inputs = inputs or {}

        rvol_thres = inputs.get("rvol", 1.5)
        bos_window = inputs.get("bos_window", 8)
        bos_strength = inputs.get("bos_strength", 0.0015)  # 0.15%
        wick_ratio = inputs.get("wick_ratio", 0.6)

        valid, error = self._validate_dataframe(df)
        if not valid or len(df) < 60:
            return {
                "signals": [],
                "plots": [],
                "meta": {"error": error}
            }

        df = df.copy().sort_values("time")

        # =========================
        # Indicators
        # =========================
        df["vwap"] = ta.vwap(
            df["high"], df["low"], df["close"], df["volume"]
        )

        df["rvol"] = df["volume"] / ta.sma(df["volume"], 20)

        prev_high = df["high"].rolling(bos_window).max().shift(1)
        df["bos"] = ((df["close"] - prev_high) / df["close"]) > bos_strength

        body = (df["close"] - df["open"]).abs()
        wick = df["high"] - df[["close", "open"]].max(axis=1)

        # =========================
        # Conditions
        # =========================
        cond = (
            df["bos"].fillna(False) &
            (df["rvol"] > rvol_thres) &
            (df["vwap"].notna()) &
            (df["close"] > df["vwap"]) &
            (wick < body * wick_ratio)
        )

        signals = []
        for _, row in df[cond].tail(3).iterrows():
            signals.append({
                "type": "bos_confirmed",
                "time": row["time"].isoformat(),
                "close": round(row["close"], 2),
                "vwap": round(row["vwap"], 2),
                "rvol": round(row["rvol"], 2)
            })

        return {
            "signals": signals,
            "plots": [
                {"type": "line", "column": "vwap"}
            ],
            "meta": {
                "strategy": self.name,
                "inputs": inputs,
                "count": len(signals),
                "notes": [] if signals else [
                    "No micro BOS",
                    "Price below VWAP",
                    "Relative volume weak"
                ]
            }
        }
