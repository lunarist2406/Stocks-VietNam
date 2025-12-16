# services/strategy_engine.py
from src.strategies.order_block import OrderBlockStrategy
from src.strategies.wyckoff import WyckoffStrategy
from src.strategies.smc import SMCStrategy

STRATEGY_MAP = {
    "order_block": OrderBlockStrategy,
    "wyckoff": WyckoffStrategy,
    "smc": SMCStrategy,
}


class StrategyEngine:
    def __init__(self, strategies=None, block_threshold=10000):
        self.strategies = []

        if not strategies:
            return

        # Chuẩn hoá input: cho phép chuỗi hoặc list
        if isinstance(strategies, str):
            strategies = [s.strip() for s in strategies.split(",") if s.strip()]

        for s in strategies:
            StrategyClass = STRATEGY_MAP.get(s)
            if StrategyClass:
                # order_block cần threshold riêng
                if s == "order_block":
                    self.strategies.append(StrategyClass(block_threshold))
                else:
                    self.strategies.append(StrategyClass())

    def run(self, df):
        return {strategy.name: strategy.apply(df) for strategy in self.strategies}
