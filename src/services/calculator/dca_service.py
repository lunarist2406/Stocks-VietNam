# src/services/dca_service.py
from typing import Optional, Dict
from src.providers.xnoapi_provider import XnoAPIProvider

class DCAService:
    def __init__(self, provider: Optional[XnoAPIProvider] = None):
        self.provider = provider or XnoAPIProvider()

    def calculate_dca(
        self,
        symbol: str,
        current_qty: int,
        current_price: Optional[float] = None,
        additional_qty: int = 0,
        additional_price: Optional[float] = None
    ) -> Dict[str, float]:
        """
        Tính DCA dựa vào giá intraday từ XnoAPI nếu không có giá nhập tay.
        """
        # Lấy giá intraday nếu không truyền
        if current_price is None:
            df = self.provider.intraday(symbol, limit=1)
            if df is None or df.empty:
                raise ValueError(f"Không lấy được giá intraday cho {symbol}")
            current_price = float(df['close'].iloc[-1])

        if additional_price is None:
            df = self.provider.intraday(symbol, limit=1)
            if df is None or df.empty:
                raise ValueError(f"Không lấy được giá intraday cho {symbol}")
            additional_price = float(df['close'].iloc[-1])
        else:
            # Tự scale nếu user nhập giá thấp quá
            if current_price > 1000 and additional_price < 1000:
                factor = round(current_price / additional_price)
                additional_price *= factor

        total_cost = current_qty * current_price + additional_qty * additional_price
        total_qty = current_qty + additional_qty
        dca = 0 if total_qty == 0 else total_cost / total_qty

        return {
            "symbol": symbol,
            "current_qty": current_qty,
            "additional_qty": additional_qty,
            "total_qty": total_qty,
            "current_price": current_price,
            "additional_price": additional_price,
            "total_cost": total_cost,
            "dca": round(dca, 2)
        }
