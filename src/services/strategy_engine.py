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
    def __init__(self):
        """Engine không cần strategies lúc khởi tạo"""
        pass

    def run(self, df, strategies):
        """
        Chạy strategies trên DataFrame
        
        Args:
            df: DataFrame với OHLCV data
            strategies: str hoặc list, ví dụ "smc,order_block,wyckoff"
        
        Returns:
            dict: {strategy_name: {signals: ..., meta: ...}}
        """
        # Normalize strategies input
        if isinstance(strategies, str):
            strategies = [s.strip() for s in strategies.split(",") if s.strip()]
        
        if not strategies:
            print("[StrategyEngine] Không có strategies được chỉ định")
            return {}

        results = {}

        for s in strategies:
            StrategyClass = STRATEGY_MAP.get(s)
            
            if not StrategyClass:
                print(f"[StrategyEngine] Strategy '{s}' không tồn tại")
                continue

            try:
                strategy = StrategyClass()
                output = strategy.apply(df)

                # Bỏ strategy không có signal
                if not output:
                    print(f"[StrategyEngine] {s}: output = None")
                    continue
                
                if not output.get("signals"):
                    print(f"[StrategyEngine] {s}: không có signals")
                    continue

                results[strategy.name] = {
                    "signals": output["signals"],
                    "meta": output.get("meta", {})
                }
                
                print(f"[StrategyEngine] {s}: OK ✓")

            except Exception as e:
                print(f"[StrategyEngine] {s}: ERROR - {e}")
                import traceback
                traceback.print_exc()
                continue

        return results