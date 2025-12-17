from vnstock import Vnstock
import pandas as pd
import sys
from pathlib import Path

# Add project root to path when running directly
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

from src.config import Config


class VnStockProvider:
    """
    Provider cho VNStock API
    - Intraday: Build OHLC từ tick data
    - History: Sử dụng data có sẵn
    """

    def __init__(self, source=Config.DEFAULT_SOURCE):
        self.source = source
        self.client = Vnstock()

    def _build_ohlc_from_ticks(self, df, interval='1T'):
        """
        Build nến OHLC từ tick data
        
        Args:
            df: DataFrame với columns ['time', 'price', 'volume']
            interval: '1T' = 1 minute, '5T' = 5 minutes
        
        Returns:
            DataFrame với columns ['time', 'open', 'high', 'low', 'close', 'volume']
        """
        if df is None or df.empty:
            return None

        # Ensure time is datetime
        if not pd.api.types.is_datetime64_any_dtype(df['time']):
            df['time'] = pd.to_datetime(df['time'])

        # Set time as index
        df = df.set_index('time')

        # Resample to OHLC
        ohlc = df['price'].resample(interval).ohlc()
        volume = df['volume'].resample(interval).sum()

        # Combine
        result = pd.DataFrame({
            'open': ohlc['open'],
            'high': ohlc['high'],
            'low': ohlc['low'],
            'close': ohlc['close'],
            'volume': volume
        })

        # Remove NaN rows (periods without trades)
        result = result.dropna()

        # Reset index to get time as column
        result = result.reset_index()
        result = result.rename(columns={'index': 'time'})

        return result

    def intraday(self, symbol, limit, interval='1T'):
        """
        Lấy dữ liệu intraday và build OHLC
        
        Args:
            symbol: Mã chứng khoán
            limit: Số lượng ticks (sẽ được build thành nến)
            interval: Khung thời gian nến ('1T', '5T', '15T', '1H')
        
        Returns:
            DataFrame với columns ['time', 'open', 'high', 'low', 'close', 'volume']
        """
        try:
            print(f"[Intraday] Fetching {symbol} (limit={limit}, interval={interval})")
            
            # Get tick data
            df = self.client.stock(
                symbol=symbol, source=self.source
            ).quote.intraday(
                symbol=symbol,
                page_size=limit,
                show_log=False
            )

            if df is None or df.empty:
                print(f"[Intraday] No data for {symbol}")
                return None

            print(f"[Intraday] Got {len(df)} ticks")
            print(f"[Intraday] Columns: {df.columns.tolist()}")

            # Validate required columns
            if 'time' not in df.columns or 'price' not in df.columns:
                print(f"[Intraday] Missing required columns")
                return None

            # Build OHLC từ ticks
            ohlc_df = self._build_ohlc_from_ticks(df[['time', 'price', 'volume']], interval)

            if ohlc_df is None or ohlc_df.empty:
                print(f"[Intraday] Failed to build OHLC")
                return None

            print(f"[Intraday] Built {len(ohlc_df)} candles")
            return ohlc_df

        except Exception as e:
            print(f"[Intraday Error] {symbol}: {e}")
            import traceback
            traceback.print_exc()
            return None

    def history(self, symbol, start, end, interval):
        """
        Lấy dữ liệu lịch sử (đã có OHLC sẵn)
        
        Returns:
            DataFrame với columns ['time', 'open', 'high', 'low', 'close', 'volume']
        """
        try:
            print(f"[History] Fetching {symbol} ({start} → {end}, {interval})")

            df = self.client.stock(
                symbol=symbol, source=self.source
            ).quote.history(
                start=start,
                end=end,
                interval=interval
            )

            if df is None or df.empty:
                print(f"[History] No data for {symbol}")
                return None

            print(f"[History] Got {len(df)} rows")
            print(f"[History] Columns: {df.columns.tolist()}")

            # Validate columns
            required = ['time', 'open', 'high', 'low', 'close', 'volume']
            if not all(col in df.columns for col in required):
                print(f"[History] Missing required columns")
                return None

            return df[required]

        except Exception as e:
            print(f"[History Error] {symbol} ({start} → {end}, {interval}): {e}")
            import traceback
            traceback.print_exc()
            return None
