# services/strategy_engine.py

from src.services.market_state import MarketStateService
from src.services.signal_builder import SignalBuilder
from src.strategies.registry import STRATEGY_REGISTRY


class StrategyEngine:
    def __init__(self):
        self.market_state_service = MarketStateService()

    def run(self, df, strategies, interval="1T"):
        # 🔧 NORMALIZE STRATEGIES
        if isinstance(strategies, str):
            strategies = [{"name": strategies}]
        elif isinstance(strategies, list):
            normalized = []
            for s in strategies:
                if isinstance(s, str):
                    normalized.append({"name": s})
                elif isinstance(s, dict):
                    normalized.append(s)
            strategies = normalized

        market_state = self.market_state_service.analyze(df)

        if not market_state["tradable"]:
            return {
                "market_state": market_state,
                "signal": SignalBuilder.no_trade(
                    market_state["description"], interval
                ),
                "signals": {},
                "suggestion": {
                    "try_timeframes": ["5T", "15T", "1H"],
                    "reason": "1T noise quá lớn"
                }
            }

        results = {}

        for item in strategies:
            name = item.get("name")
            if not name:
                continue

            inputs = item.get("inputs", {})
            StrategyClass = STRATEGY_REGISTRY.get(name)

            if not StrategyClass:
                continue

            try:
                strategy = StrategyClass()
                results[name] = strategy.apply(df, inputs)
            except Exception as e:
                results[name] = {
                    "signals": [],
                    "plots": [],
                    "meta": {
                        "strategy": name,
                        "error": str(e),
                        "count": 0
                    }
                }

        final_signal = SignalBuilder.from_strategies(results)

        return {
            "market_state": market_state,
            "signal": final_signal,
            "signals": results
        }
    def __init__(self):
        self.market_state_service = MarketStateService()

    def run(self, df, strategies, interval="1T"):
        market_state = self.market_state_service.analyze(df)

        results = {}

        # 🚨 MARKET KHÔNG ĐÁNG TRADE
        if not market_state["tradable"]:
            return {
                "market_state": market_state,
                "signal": SignalBuilder.no_trade(
                    market_state["description"], interval
                ),
                "signals": {},
                "suggestion": {
                    "try_timeframes": ["5T", "15T", "1H"],
                    "reason": "1T noise quá lớn"
                }
            }

        # ✅ MARKET OK → CHẠY STRATEGY
        for item in strategies:
            name = item.get("name")
            if not name:
                continue

            inputs = item.get("inputs", {})


            StrategyClass = STRATEGY_REGISTRY.get(name)
            if not StrategyClass:
                continue

            try:
                strategy = StrategyClass()
                results[name] = strategy.apply(df, inputs)
            except Exception as e:
                results[name] = {
                    "signals": [],
                    "plots": [],
                    "meta": {
                        "strategy": name,
                        "error": str(e),
                        "count": 0
                    }
                }


        final_signal = SignalBuilder.from_strategies(results)

        return {
            "market_state": market_state,
            "signal": final_signal,
            "signals": results
        }
