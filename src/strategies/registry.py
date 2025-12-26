# strategies/registry.py

from src.strategies.smc import SMCStrategy
from src.strategies.order_block import OrderBlockStrategy
from src.strategies.wyckoff import WyckoffStrategy

STRATEGY_REGISTRY = {
    cls.name: cls
    for cls in [
        SMCStrategy,
        OrderBlockStrategy,
        WyckoffStrategy
    ]
}
