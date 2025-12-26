from src.config import Config
from xnoapi import client
from xnoapi.vn.data.stocks import Company, Finance, Quote
from xnoapi.vn.data.derivatives import get_hist as get_derivatives_hist
from xnoapi.vn.data import get_stock_foreign_trading
from xnoapi.vn.metrics import Metrics, Backtest_Derivates
import time


class XnoAPIProvider:
    """
    XNOAPI Provider – extended
    Bao gồm:
    - Stock intraday / history
    - Derivatives intraday / history
    - Foreign trading
    - Price depth
    - Company & Finance info
    - Metrics & Backtest
    """

    def __init__(self, retry=2, retry_delay=0.5):
        self.retry = retry
        self.retry_delay = retry_delay

        try:
            client(apikey=Config.XNOAPI_KEY)
            print("[XNOAPI] Client initialized")
        except Exception as e:
            raise RuntimeError(f"[XNOAPI Init Failed] {e}")

    # ==================================================
    # INTERNAL
    # ==================================================
    def _retry(self, func, *args, **kwargs):
        for i in range(self.retry + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if i == self.retry:
                    raise e
                time.sleep(self.retry_delay)

    def _ohlcv(self, df):
        if df is None or df.empty:
            return None

        # Nếu dataframe có tick intraday (chỉ có 'price')
        if all(col in df.columns for col in ['open','high','low','close','volume']):
            return df[['time','open','high','low','close','volume']]
        elif all(col in df.columns for col in ['time','price','volume']):
            # map price -> close và duplicate cho open/high/low
            df = df.rename(columns={'price':'close'})
            df['open'] = df['high'] = df['low'] = df['close']
            return df[['time','open','high','low','close','volume']]
        else:
            return None


    # ==================================================
    # STOCK DATA
    # ==================================================
    def intraday(self, symbol, limit=100):
        try:
            df = self._retry(
                Quote(symbol).intraday,
                page_size=limit  # đổi từ limit -> page_size
            )
            return self._ohlcv(df)
        except Exception as e:
            print(f"[XNO Intraday Error] {symbol}: {e}")
            return None


    def history(self, symbol, start, end, interval="1d"):
        try:
            df = self._retry(
                Quote(symbol).history,
                start=start,
                end=end,
                interval=interval
            )
            return self._ohlcv(df)
        except Exception as e:
            print(f"[XNO History Error] {symbol}: {e}")
            return None

    # ==================================================
    # DERIVATIVES
    # ==================================================
    def derivatives_hist(self, symbol, frequency="1M"):
        """
        frequency:
        - "1M", "5M", "15M"  -> intraday
        - "1H"
        - "1D"
        """
        try:
            df = self._retry(
                get_derivatives_hist,
                symbol,
                frequency
            )

            if df is None or df.empty:
                return None

            # chuẩn hóa lại cho giống stock
            df = df.rename(columns={
                "datetime": "time",
                "vol": "volume"
            })

            return df[['time', 'open', 'high', 'low', 'close', 'volume']]
        except Exception as e:
            print(f"[XNO Derivatives Error] {symbol}: {e}")
            return None


    # ==================================================
    # FOREIGN / DEPTH
    # ==================================================
    def foreign_trading(self, symbol):
        try:
            df = self._retry(get_stock_foreign_trading, symbol)
            return [] if df is None or df.empty else df.to_dict("records")
        except Exception as e:
            print(f"[XNO Foreign Error] {symbol}: {e}")
            return []

    def price_depth(self, symbol):
        try:
            df = self._retry(Quote(symbol).price_depth)
            return [] if df is None or df.empty else df.to_dict("records")
        except Exception as e:
            print(f"[XNO PriceDepth Error] {symbol}: {e}")
            return []

    # ==================================================
    # COMPANY / FINANCE
    # ==================================================
    def company_info(self, symbol):
        try:
            company = Company(symbol)
            return {
                "overview": company.overview(),
                "profile": company.profile(),
                "shareholders": company.shareholders(),
                "officers": company.officers(),
                "subsidiaries": company.subsidiaries(),
                "events": company.events(),
                "news": company.news()
            }
        except Exception as e:
            print(f"[XNO Company Error] {symbol}: {e}")
            return {}

    def finance_info(self, symbol):
        try:
            finance = Finance(symbol)
            return {
                "income_statement": finance.income_statement("year"),
                "balance_sheet": finance.balance_sheet("year"),
                "cash_flow": finance.cash_flow("year"),
                "ratio_summary": finance.ratio_summary()
            }
        except Exception as e:
            print(f"[XNO Finance Error] {symbol}: {e}")
            return {}

    # ==================================================
    # METRICS / BACKTEST
    # ==================================================
    def calc_metrics(self, pnl_series):
        """
        pnl_series: list hoặc pandas Series lợi nhuận
        """
        try:
            return Metrics(pnl_series).summary()
        except Exception as e:
            print(f"[XNO Metrics Error] {e}")
            return {}

    def backtest_derivatives(self, df, fee=0.0002):
        """
        df cần có: time, close, signal (1, -1, 0)
        """
        try:
            bt = Backtest_Derivates(df, fee=fee)
            return {
                "summary": bt.summary(),
                "trades": bt.trades
            }
        except Exception as e:
            print(f"[XNO Backtest Error] {e}")
            return {}

    # ==================================================
    # HEALTH
    # ==================================================
    def ping(self):
        try:
            return {"status": "ok"}
        except Exception:
            return {"status": "fail"}
