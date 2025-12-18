from datetime import timedelta, datetime
from src.providers.vnstock_provider import VnStockProvider
from src.utils.df_utils import normalize_df_time, filter_by_time
from src.utils.time_utils import normalize_range
from src.utils.market_time_utils import is_market_open
from src.services.strategy_engine import StrategyEngine


class StockService:
    """
    StockService chịu trách nhiệm:
    - Lấy dữ liệu từ provider
    - Normalize & filter dữ liệu
    - Gọi StrategyEngine khi cần

    ❌ KHÔNG chứa logic trade
    ❌ KHÔNG phán đoán chiến lược
    """

    REQUIRED_COLUMNS = ["time", "open", "high", "low", "close", "volume"]

    def __init__(self):
        self.provider = VnStockProvider()
    
    def intraday(self, symbol, limit=500, interval="5T"):
        """
        Proxy intraday từ provider
        """
        return self.provider.intraday(
            symbol=symbol,
            limit=limit,
            interval=interval
        )    
    
    def _validate_dataframe(self, df, symbol: str):
        """Validate DataFrame has required columns and data"""
        if df is None or df.empty:
            return False, f"Không có dữ liệu cho {symbol}"
        
        missing_cols = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]
        if missing_cols:
            return False, f"Thiếu cột dữ liệu: {', '.join(missing_cols)}"
        
        return True, None

    # =====================================================
    # 1. SNAPSHOT – GIÁ HIỆN TẠI
    # =====================================================
    def snapshot(self, symbol: str):
        try:
            # Get recent ticks and build 1-minute candle
            df = self.provider.intraday(symbol, limit=100, interval='1T')
            
            # Validate trước khi normalize
            valid, error = self._validate_dataframe(df, symbol)
            if not valid:
                return {"error": error}

            df = normalize_df_time(df)
            
            # Validate lại sau normalize
            if df.empty:
                return {"error": f"Không có dữ liệu sau khi normalize cho {symbol}"}

            latest = df.iloc[-1]
            return {
                "symbol": symbol,
                "time": latest["time"].isoformat(),
                "price": float(latest["close"]),
                "volume": int(latest["volume"])
            }
        except Exception as e:
            return {"error": f"Snapshot error: {str(e)}"}

    # =====================================================
    # 2. HISTORY – DỮ LIỆU LỊCH SỬ (CHART)
    # =====================================================
    def history(self, symbol: str, start: str, end: str, interval: str):
        try:
            start_dt, end_dt = normalize_range(start, end)

            # fallback intraday -> daily nếu quá xa
            if interval in ("1m", "1h"):
                days_diff = (datetime.now().date() - start_dt.date()).days
                if days_diff > 2:
                    interval = "1d"

            # intraday giới hạn giờ giao dịch
            if interval in ("1m", "1h"):
                start_dt = start_dt.replace(hour=9, minute=0, second=0)
                end_dt = end_dt.replace(hour=15, minute=0, second=0)

            # gọi provider
            if interval == "1d":
                df = self.provider.history(
                    symbol,
                    start_dt.date().isoformat(),
                    end_dt.date().isoformat(),
                    "1d"
                )
            else:
                # Map interval to pandas resample format
                interval_map = {
                    "1m": "1T",
                    "1h": "1H"
                }
                limit = 2000 if interval == "1m" else 1000
                df = self.provider.intraday(
                    symbol, 
                    limit=limit,
                    interval=interval_map.get(interval, "1T")
                )

            # Validate
            valid, error = self._validate_dataframe(df, symbol)
            if not valid:
                return {
                    "symbol": symbol,
                    "interval": interval,
                    "from": start_dt.isoformat(),
                    "to": end_dt.isoformat(),
                    "records": []
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
            return {"error": f"History error: {str(e)}"}

    # =====================================================
    # 3. TICK + STRATEGY ENGINE (TRADE MODE)
    # =====================================================
    def tick(self, symbol: str, start: str, end: str,
             limit=1000, strategies=None, interval='1T'):
        try:
            start_dt, end_dt = normalize_range(start, end)

            df = self.provider.intraday(symbol, limit=limit, interval=interval)
            
            # Validate
            valid, error = self._validate_dataframe(df, symbol)
            if not valid:
                return {"error": error}

            df = normalize_df_time(df)
            df = filter_by_time(df, start_dt, end_dt)

            if df.empty:
                return {"error": f"Không có dữ liệu tick cho {symbol} trong khoảng thời gian này"}

            result = {
                "symbol": symbol,
                "from": start_dt.isoformat(),
                "to": end_dt.isoformat(),
                "count": len(df),
                "records": df.to_dict("records")  # ✅ Luôn hiển thị data
            }

            # ✅ FIX: Run strategies with new API
            if strategies:
                try:
                    engine = StrategyEngine()
                    signals = engine.run(df=df, strategies=strategies)
                    
                    if signals:
                        result["signals"] = signals
                    else:
                        result["signals"] = {}
                        result["signals_note"] = "Không có tín hiệu từ các chiến lược"
                        
                except Exception as e:
                    print(f"[StockService.tick] Strategy error: {e}")
                    result["signals"] = {"error": str(e)}

            return result

        except Exception as e:
            return {"error": f"Tick error: {str(e)}"}

    # =====================================================
    # 4. LAST MINUTES – REALTIME SCALPING
    # =====================================================
    def last_minutes(
        self,
        symbol: str,
        minutes=5,
        limit=300,
        strategies=None,
        interval='1T',
        validate_market_time: bool = False
    ):
        try:
            if validate_market_time:
                ok, msg = is_market_open(datetime.now())
                if not ok:
                    return {"error": msg}

            df = self.provider.intraday(symbol, limit=limit, interval=interval)
            
            # Validate
            valid, error = self._validate_dataframe(df, symbol)
            if not valid:
                return {"error": error}

            df = normalize_df_time(df)

            if df.empty:
                return {"error": f"Không có dữ liệu sau normalize cho {symbol}"}

            latest_time = df["time"].max()
            start_time = latest_time - timedelta(minutes=minutes)
            df = df[df["time"] >= start_time]

            if df.empty:
                return {"error": f"Không có dữ liệu trong {minutes} phút gần nhất"}

            result = {
                "symbol": symbol,
                "from": start_time.isoformat(),
                "to": latest_time.isoformat(),
                "count": len(df),
                "records": df.to_dict("records")  # ✅ Luôn hiển thị data
            }

            # ✅ FIX: Run strategies with new API
            if strategies:
                try:
                    engine = StrategyEngine()
                    signals = engine.run(df=df, strategies=strategies)
                    
                    if signals:
                        result["signals"] = signals
                    else:
                        result["signals"] = {}
                        result["signals_note"] = "Không có tín hiệu từ các chiến lược"
                        
                except Exception as e:
                    print(f"[StockService.last_minutes] Strategy error: {e}")
                    result["signals"] = {"error": str(e)}

            return result

        except Exception as e:
            return {"error": f"Last minutes error: {str(e)}"}