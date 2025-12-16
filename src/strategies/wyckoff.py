from src.strategies.base import BaseStrategy

class WyckoffStrategy(BaseStrategy):
    name = "wyckoff"

    def apply(self, df):
        df["price_change"] = df["price"].diff()
        spring = df[(df["price_change"] < 0) & (df["volume"] > df["volume"].mean())]
        return spring.tail(5).to_dict("records")
