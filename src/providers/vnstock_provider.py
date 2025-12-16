from vnstock import Vnstock
from src.config import Config 

class VnStockProvider:
    def __init__(self, source=Config.DEFAULT_SOURCE):
        self.source = source
        self.client = Vnstock()

    def intraday(self, symbol, limit):
        try:
            df = self.client.stock(
                symbol=symbol, source=self.source
            ).quote.intraday(
                symbol=symbol,
                page_size=limit,
                show_log=False
            )
            if df is None or df.empty:
                return {
                    "error": f"Không có dữ liệu intraday cho {symbol} (limit={limit})"
                }
            return df
        except Exception as e:
            print(f"[Intraday Error] {symbol}: {e}")
            return {"error": str(e)}

    def history(self, symbol, start, end, interval):
        try:
            df = self.client.stock(
                symbol=symbol, source=self.source
            ).quote.history(
                start=start,
                end=end,
                interval=interval
            )
            if df is None or df.empty:
                return {
                    "error": f"Không có dữ liệu lịch sử cho {symbol} từ {start} đến {end} (interval={interval})"
                }
            return df
        except Exception as e:
            print(f"[History Error] {symbol} ({start} → {end}, {interval}): {e}")
            return {"error": str(e)}
