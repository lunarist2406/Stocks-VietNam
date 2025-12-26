# services/signal_builder.py

class SignalBuilder:

    @staticmethod
    def no_trade(reason, interval):
        return {
            "bias": "neutral",
            "action": "no_trade",
            "confidence": 0.05,
            "reason": reason,
            "valid_for": interval
        }

    @staticmethod
    def from_strategies(results):
        total_signals = sum(len(v.get("signals", [])) for v in results.values())

        if total_signals == 0:
            return {
                "bias": "neutral",
                "action": "no_trade",
                "confidence": 0.1,
                "reason": "No structure / No confirmation"
            }

        # mở rộng sau: scoring, weighting
        return {
            "bias": "long",
            "action": "watch",
            "confidence": min(total_signals * 0.25, 1)
        }
