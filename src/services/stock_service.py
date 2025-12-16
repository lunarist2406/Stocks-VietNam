from datetime import timedelta, datetime
from src.providers.vnstock_provider import VnStockProvider
from src.utils.df_utils import normalize_df_time, filter_by_time
from src.utils.time_utils import normalize_range
from src.utils.market_time_utils import is_market_open
from src.services.strategy_engine import StrategyEngine


class StockService:
    def __init__(self):
        self.provider = VnStockProvider()

    # =====================================================
    # 1. SNAPSHOT – GIÁ HIỆN TẠI
    # =====================================================
    def snapshot(self, symbol: str):
        try:
            df = self.provider.intraday(symbol, limit=1)
            if df is None or df.empty:
                return {"error": f"Không có dữ liệu intraday cho {symbol}"}

            df = normalize_df_time(df)
            return df.iloc[-1].to_dict()
        except Exception as e:
            return {"error": f"Snapshot error: {e}"}

    # =====================================================
    # 2. HISTORY – DỮ LIỆU LỊCH SỬ
    # =====================================================
    def history(self, symbol: str, start: str, end: str, interval: str):
        try:
            start_dt, end_dt = normalize_range(start, end)

            # Nếu intraday nhưng khoảng thời gian quá khứ xa thì fallback sang daily
            if interval in ("1m", "1h"):
                days_diff = (datetime.now().date() - start_dt.date()).days
                if days_diff > 2:
                    interval = "1d"

            # Nếu intraday thì chỉ lấy trong khung giờ giao dịch
            if interval in ("1m", "1h"):
                start_dt = start_dt.replace(hour=9, minute=0, second=0)
                end_dt = end_dt.replace(hour=15, minute=0, second=0)

            # Gọi provider
            if interval == "1d":
                df = self.provider.history(symbol, start_dt.date().isoformat(), end_dt.date().isoformat(), "1d")
            else:
                limit = 2000 if interval == "1m" else 1000
                df = self.provider.intraday(symbol, limit=limit)

            if df is None or df.empty:
                return {
                    "symbol": symbol,
                    "interval": interval,
                    "from": start_dt.isoformat(),
                    "to": end_dt.isoformat(),
                    "records": [],
                    "note": f"Không có dữ liệu cho {symbol} từ {start_dt} đến {end_dt} (interval={interval})"
                }

            df = normalize_df_time(df)
            df = filter_by_time(df, start_dt, end_dt)

            return {
                "symbol": symbol,
                "interval": interval,
                "from": start_dt.isoformat(),
                "to": end_dt.isoformat(),
                "records": df.to_dict("records")
            }
        except Exception as e:
            return {"error": f"History error: {e}"}

    # =====================================================
    # 3. TICK + STRATEGY ENGINE
    # =====================================================
    def tick(self, symbol: str, start: str, end: str,
             limit=1000, block_threshold=10000, strategies=None):
        try:
            start_dt, end_dt = normalize_range(start, end)

            df = self.provider.intraday(symbol, limit=limit)
            if df is None or df.empty:
                return {"error": f"Không có dữ liệu intraday cho {symbol}"}

            df = normalize_df_time(df)
            df = filter_by_time(df, start_dt, end_dt)

            if df.empty:
                return {"error": f"No tick data for {symbol} between {start_dt} and {end_dt}"}

            # Phát hiện order block
            order_blocks = df[df["volume"] >= block_threshold].to_dict("records")

            result = {
                "symbol": symbol,
                "from": start_dt.isoformat(),
                "to": end_dt.isoformat(),
                "records": df.to_dict("records"),
                "order_blocks": order_blocks,
                "block_threshold": block_threshold
            }

            if strategies:
                engine = StrategyEngine(strategies=strategies, block_threshold=block_threshold)
                result["signals"] = engine.run(df)

            return result
        except Exception as e:
            return {"error": f"Tick error: {e}"}

    # =====================================================
    # 4. LAST MINUTES – SCALPING MODE (Realtime)
    # =====================================================
    def last_minutes(self, symbol: str, minutes=5, limit=300, strategies=None):
        try:
            ok, msg = is_market_open(datetime.now())
            if not ok:
                return {"error": msg}

            df = self.provider.intraday(symbol, limit=limit)
            if df is None or df.empty:
                return {"error": f"Không có dữ liệu intraday cho {symbol}"}

            df = normalize_df_time(df)

            latest_time = df["time"].max()
            start_time = latest_time - timedelta(minutes=minutes)

            df = df[df["time"] >= start_time]

            if df.empty:
                return {"error": f"No data for {symbol} in last {minutes} minutes"}

            result = {
                "symbol": symbol,
                "from": start_time.isoformat(),
                "to": latest_time.isoformat(),
                "records": df.to_dict("records")
            }

            if strategies:
                engine = StrategyEngine(strategies=strategies)
                result["signals"] = engine.run(df)

            return result
        except Exception as e:
            return {"error": f"Last minutes error: {e}"}
