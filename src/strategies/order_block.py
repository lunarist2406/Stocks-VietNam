from src.strategies.base import BaseStrategy

class OrderBlockStrategy(BaseStrategy):
    name = "order_block"

    def __init__(self, threshold):
        self.threshold = threshold

    def apply(self, df):
        blocks = df[df["volume"] >= self.threshold]
        return blocks.to_dict("records")
