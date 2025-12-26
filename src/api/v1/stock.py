from fastapi import APIRouter, Query
from src.services.stock_service import StockService

router = APIRouter()
service = StockService()


@router.get("/live")
def get_live(symbol: str = Query(..., description="Mã cổ phiếu")):
    """
    📊 Giá realtime hiện tại
    """
    return service.snapshot(symbol)


@router.get("/history")
def get_history(
    symbol: str = Query(..., description="Mã cổ phiếu"),
    start: str = Query(..., description="Thời gian bắt đầu"),
    end: str = Query(..., description="Thời gian kết thúc"),
    interval: str = Query("1d", description="Khung thời gian: 1m, 1h, 1d")
):
    """
    📈 Dữ liệu lịch sử (chart)
    """
    return service.history(symbol, start, end, interval)


@router.get("/tick")
def get_tick(
    symbol: str = Query(..., description="Mã cổ phiếu"),
    start: str = Query(..., description="Thời gian bắt đầu"),
    end: str = Query(..., description="Thời gian kết thúc"),
    limit: int = Query(1000, description="Số lượng tick tối đa"),
    strategies: str = Query(None, description="Danh sách strategy: order_block, wyckoff, smc"),
    interval: str = Query("1T", description="Khung nến: 1T (1min), 5T (5min), 15T, 1H")
):
    """
    🧠 Tick + Strategy Engine
    
    Lấy dữ liệu intraday và chạy chiến lược (Order Block / Wyckoff / SMC).
    
    **Luôn trả về:**
    - `records`: Dữ liệu OHLCV chi tiết
    - `signals`: Tín hiệu từ các chiến lược (nếu có)
    - `count`: Số lượng nến
    """
    return service.tick(
        symbol=symbol,
        start=start,
        end=end,
        limit=limit,
        strategies=strategies,
        interval=interval
    )


@router.get("/lastMin")
def get_last_5_min(
    symbol: str = Query(..., description="Mã cổ phiếu"),
    minutes: int = Query(5, description="Số phút gần nhất"),
    limit: int = Query(10000, description="Số lượng tick tối đa"),
    strategies: str = Query(None, description="Strategy chạy realtime"),
    interval: str = Query("1T", description="Khung nến: 1T (1min), 5T (5min)")
):
    """
    ⚡ N phút gần nhất (Scalping)
    
    Lấy dữ liệu N phút gần nhất + optional Strategy Engine.
    
    **Luôn trả về:**
    - `records`: Dữ liệu OHLCV chi tiết
    - `signals`: Tín hiệu từ các chiến lược (nếu có)
    - `count`: Số lượng nến
    """
    return service.last_minutes(
        symbol=symbol,
        minutes=minutes,
        limit=limit,
        strategies=strategies,
        interval=interval
    )


