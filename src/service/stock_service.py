from vnstock import Vnstock, Trading
from datetime import datetime
from cachetools import TTLCache, cached
import pandas as pd
import src.config as config

# Cache TTL 10 giây cho snapshot
cache = TTLCache(maxsize=50, ttl=10)

vnstock_instance = None
def get_vnstock_instance():
    global vnstock_instance
    if vnstock_instance is None:
        vnstock_instance = Vnstock()
    return vnstock_instance

def validate_symbol(symbol: str) -> bool:
    return symbol.isalpha() and 3 <= len(symbol) <= 5

# Helper: lấy khối ngoại từ SSI/TCBS
def get_foreign_data(symbol: str) -> tuple[int,int]:
    for src in ["TCBS", "SSI"]:
        try:
            board = Trading(source=src).price_board([symbol])
            if board is not None and not board.empty:
                total_buy = int(board["NN Mua"].iloc[0]) if "NN Mua" in board.columns else 0
                total_sell = int(board["NN Bán"].iloc[0]) if "NN Bán" in board.columns else 0
                return total_buy, total_sell
        except Exception:
            continue
    return 0, 0

# 1. Snapshot mới nhất
@cached(cache)
def fetch_stock(symbol: str):
    symbol = symbol.strip().upper()
    if not validate_symbol(symbol):
        return {"error": "Invalid stock symbol"}
    try:
        vn = get_vnstock_instance().stock(symbol=symbol, source="VCI")
        df = vn.quote.intraday(symbol=symbol, page_size=config.DEFAULT_LIMIT, show_log=False)
        if df is None or df.empty:
            return {"error": f"No data for {symbol}"}
        row = df.iloc[-1]

        total_foreign_buy, total_foreign_sell = get_foreign_data(symbol)
        most_traded_price = df["price"].mode().iloc[0] if "price" in df.columns and not df["price"].empty else None

        return {
            "symbol": symbol,
            "price": float(row.get("price", 0)),
            "volume": int(row.get("volume", 0)),
            "foreign_buy": int(row.get("foreign_buy", 0)),
            "foreign_sell": int(row.get("foreign_sell", 0)),
            "total_foreign_buy": total_foreign_buy,
            "total_foreign_sell": total_foreign_sell,
            "best_bid_price": float(row.get("best_bid_price", 0)),
            "best_bid_volume": int(row.get("best_bid_volume", 0)),
            "best_ask_price": float(row.get("best_ask_price", 0)),
            "best_ask_volume": int(row.get("best_ask_volume", 0)),
            "most_traded_price": float(most_traded_price) if most_traded_price else None,
            "time": str(row.get("time"))
        }
    except Exception as e:
        return {"error": str(e)}

# 2. History
def fetch_stock_by_date(symbol: str, start: str, end: str, interval="1d"):
    symbol = symbol.strip().upper()
    if not validate_symbol(symbol):
        return {"error": "Invalid stock symbol"}
    try:
        vn = get_vnstock_instance().stock(symbol=symbol, source="VCI")
        df = vn.quote.history(start=start, end=end, interval=interval)
        if df is None or df.empty:
            return {"error": f"No {interval} data for {symbol}"}

        df["time"] = pd.to_datetime(df["time"], errors="coerce").dt.tz_localize(None)
        mask = (df["time"] >= pd.to_datetime(start)) & (df["time"] <= pd.to_datetime(end))
        df = df.loc[mask]
        if df.empty:
            return {"error": f"No {interval} data for {symbol} between {start} and {end}"}

        most_traded_price = df["price"].mode().iloc[0] if not df["price"].empty else None
        total_foreign_buy, total_foreign_sell = get_foreign_data(symbol)

        records = df.to_dict(orient="records")
        for r in records:
            r["most_traded_price"] = float(most_traded_price) if most_traded_price else None

        return {
            "symbol": symbol,
            "records": records,
            "total_foreign_buy": total_foreign_buy,
            "total_foreign_sell": total_foreign_sell
        }
    except Exception as e:
        return {"error": str(e)}

# 3. Tick
def fetch_stock_tick(symbol: str, start: str, end: str, limit: int = 10000, block_threshold: int = 10000):
    """
    Lấy dữ liệu tick từ VCI (giá/khối lượng), khối ngoại từ SSI/TCBS.
    Đồng thời phát hiện order block (các lệnh có volume >= block_threshold).
    """
    symbol = symbol.strip().upper()
    if not validate_symbol(symbol):
        return {"error": "Invalid stock symbol"}
    try:
        vn = get_vnstock_instance().stock(symbol=symbol, source="VCI")
        df = vn.quote.intraday(symbol=symbol, page_size=limit, show_log=False)
        if df is None or df.empty:
            return {"error": f"No tick data for {symbol}"}

        # lọc theo khoảng thời gian
        df["time"] = pd.to_datetime(df["time"], errors="coerce").dt.tz_localize(None)
        mask = (df["time"] >= pd.to_datetime(start)) & (df["time"] <= pd.to_datetime(end))
        df = df.loc[mask]
        if df.empty:
            return {"error": f"No tick data for {symbol} between {start} and {end}"}

        # giá giao dịch nhiều nhất
        most_traded_price = df["price"].mode().iloc[0] if not df["price"].empty else None
        # khối ngoại từ SSI/TCBS
        total_foreign_buy, total_foreign_sell = get_foreign_data(symbol)

        # records đầy đủ
        records = df.to_dict(orient="records")
        for r in records:
            r["most_traded_price"] = float(most_traded_price) if most_traded_price else None

        # phát hiện order block
        order_blocks = df[df["volume"] >= block_threshold].to_dict(orient="records")

        return {
            "symbol": symbol,
            "records": records,
            "total_foreign_buy": total_foreign_buy,
            "total_foreign_sell": total_foreign_sell,
            "order_blocks": order_blocks,
            "block_threshold": block_threshold
        }
    except Exception as e:
        return {"error": str(e)}


# 4. Wrapper
def fetch_stock_by_range(symbol: str, start: datetime, end: datetime, interval="tick", block_threshold: int = 10000):
    """
    Wrapper: nếu interval = tick thì gọi fetch_stock_tick (có order block),
    ngược lại gọi fetch_stock_by_date.
    """
    symbol = symbol.strip().upper()
    if not validate_symbol(symbol):
        return {"error": "Invalid stock symbol"}
    try:
        start_str = start.strftime("%Y-%m-%d %H:%M:%S")
        end_str = end.strftime("%Y-%m-%d %H:%M:%S")
        if interval == "tick":
            return fetch_stock_tick(symbol, start_str, end_str, block_threshold=block_threshold)
        else:
            return fetch_stock_by_date(symbol, start_str, end_str, interval)
    except Exception as e:
        return {"error": str(e)}
