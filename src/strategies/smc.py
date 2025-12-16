from src.strategies.base import BaseStrategy

class SMCStrategy(BaseStrategy):
    name = "smc"

    def apply(self, df):
        df["bos"] = (df["price"] > df["price"].shift(1)) & \
                    (df["volume"] > df["volume"].rolling(20).mean())
        return df[df["bos"]].tail(5).to_dict("records")
