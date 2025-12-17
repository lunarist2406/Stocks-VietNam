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
    def __init__(self, strategies=None):
        self.strategies = []

        if not strategies:
            return

        # normalize input
        if isinstance(strategies, str):
            strategies = [s.strip() for s in strategies.split(",") if s.strip()]

        for s in strategies:
            StrategyClass = STRATEGY_MAP.get(s)
            if StrategyClass:
                self.strategies.append(StrategyClass())

    def run(self, df):
        results = {}

        for strategy in self.strategies:
            output = strategy.apply(df)

            # bỏ strategy không có signal
            if not output or not output.get("signals"):
                continue

            results[strategy.name] = {
                "signals": output["signals"],
                "meta": output.get("meta", {})
            }

        return results
