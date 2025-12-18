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


@router.get("/signals")
def get_signals_only(
    symbol: str = Query(..., description="Mã cổ phiếu"),
    start: str = Query(None, description="Thời gian bắt đầu (VD: 2025-12-17 hoặc 2025-12-17 09:00:00)"),
    end: str = Query(None, description="Thời gian kết thúc (VD: 2025-12-17 hoặc 2025-12-17 15:00:00)"),
    strategies: str = Query("order_block,wyckoff,smc", description="Strategies"),
    limit: int = Query(1000, description="Số lượng tick"),
    interval: str = Query("5T", description="Khung nến: 1T (1min), 5T (5min), 15T, 1H"),
    minutes: int = Query(None, description="Hoặc dùng N phút gần nhất (bỏ qua start/end)")
):
    """
    🎯 Chỉ lấy signals (không cần records)
    
    **2 cách sử dụng:**
    
    1. **Time range** (cho historical): 
       - `start` và `end` phải có datetime đầy đủ
       - VD: start=2025-12-17 09:00:00, end=2025-12-17 15:00:00
    
    2. **Recent minutes** (cho realtime):
       - Chỉ cần `minutes` (VD: minutes=10)
       - Bỏ qua start/end
    
    Endpoint tối ưu cho việc chỉ cần tín hiệu giao dịch, không cần raw data
    """
    
    # Mode 1: Use minutes (realtime)
    if minutes:
        result = service.last_minutes(
            symbol=symbol,
            minutes=minutes,
            limit=limit,
            strategies=strategies,
            interval=interval
        )
    # Mode 2: Use time range
    else:
        if not start or not end:
            return {
                "error": "Cần cung cấp start+end hoặc minutes",
                "hint": "VD 1: start=2025-12-17 09:00:00&end=2025-12-17 15:00:00",
                "hint2": "VD 2: minutes=10 (lấy 10 phút gần nhất)"
            }
        
        # Auto-add time if missing
        if len(start.strip()) == 10:  # Only date
            start = start.strip() + " 09:00:00"
        if len(end.strip()) == 10:  # Only date
            end = end.strip() + " 15:00:00"
        
        result = service.tick(
            symbol=symbol,
            start=start,
            end=end,
            limit=limit,
            strategies=strategies,
            interval=interval
        )
    
    # Return error if any
    if "error" in result:
        return result
    
    # Return only signals (no records)
    return {
        "symbol": result["symbol"],
        "from": result["from"],
        "to": result["to"],
        "count": result["count"],
        "signals": result.get("signals", {}),
        "signals_note": result.get("signals_note", "")
    }