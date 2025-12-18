import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pandas as pd
from src.services.trade.trade_signal_builder import TradeSignalBuilder

# Fake OHLCV data
df = pd.DataFrame({
    "time": pd.date_range("2025-01-01", periods=60, freq="5min"),
    "open":  [10 + i*0.01 for i in range(60)],
    "high":  [10.1 + i*0.01 for i in range(60)],
    "low":   [9.9 + i*0.01 for i in range(60)],
    "close": [10 + i*0.01 for i in range(60)],
    "volume": [5000 + i*200 for i in range(60)],
})

# Fake strategy results (MATCH ENGINE OUTPUT)
strategy_results = {
    "smc": [
        {"bos": True, "time": df.iloc[-1]["time"]}
    ],
    "order_block": [
        {
            "time": df.iloc[-5]["time"],
            "low": df.iloc[-5]["low"],
            "high": df.iloc[-5]["high"],
            "volume": 15000
        }
    ],
    "wyckoff": [
        {"spring": True, "time": df.iloc[-10]["time"]}
    ]
}

builder = TradeSignalBuilder(rr_min=1.5)
signal = builder.build(df, strategy_results)

print("\n=== TRADE SIGNAL ===")
print(signal)
