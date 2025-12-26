# services/market_state.py
import pandas_ta as ta


class MarketStateService:
    def analyze(self, df):
        atr = ta.atr(df["high"], df["low"], df["close"], length=14)
        atr_pct = atr.iloc[-1] / df["close"].iloc[-1]

        price_range = (df["high"].max() - df["low"].min()) / df["close"].mean()
        rel_vol = df["volume"].iloc[-20:].mean() / df["volume"].mean()

        if atr_pct < 0.003 and price_range < 0.01:
            return {
                "type": "low_volatility",
                "tradable": False,
                "description": "Sideway – liquidity thấp – không phù hợp trade"
            }

        return {
            "type": "normal",
            "tradable": True
        }
