from fastapi import APIRouter, Query
from typing import Dict, Any

from src.services.stock_service import StockService
from src.api.deps import handle_service_error

router = APIRouter(
    prefix="/stock",
    tags=["Stock"]
)

stock_service = StockService()

# =====================================================
# 1. SNAPSHOT – GIÁ HIỆN TẠI
# =====================================================
@router.get(
    "/live",
    response_model=Dict[str, Any],
    summary="📡 Snapshot giá cổ phiếu hiện tại",
    description="Lấy snapshot mới nhất (giá, khối lượng, thời gian) từ intraday."
)
def live(
    symbol: str = Query(
        ...,
        description="Mã cổ phiếu VN",
        example="FPT"
    )
):
    """
    Ví dụ:
    ```
    GET /stock/live?symbol=VNM
    ```
    """
    return handle_service_error(
        stock_service.snapshot(symbol)
    )


# =====================================================
# 2. HISTORY – DỮ LIỆU LỊCH SỬ
# =====================================================
@router.get(
    "/history",
    response_model=Dict[str, Any],
    summary="📊 Lịch sử giá theo khoảng thời gian",
    description="Lấy dữ liệu lịch sử theo ngày / phút / giờ."
)
def history(
    symbol: str = Query(
        ...,
        example="FPT",
        description="Mã cổ phiếu"
    ),
    start: str = Query(
        ...,
        example="2024-01-01",
        description="Thời gian bắt đầu (YYYY-MM-DD hoặc datetime)"
    ),
    end: str = Query(
        ...,
        example="2024-01-31",
        description="Thời gian kết thúc"
    ),
    interval: str = Query(
        "1d",
        example="1d",
        description="Khung thời gian: 1d, 1h, 1m"
    )
):
    """
    Ví dụ:
    ```
    GET /stock/history?symbol=FPT&start=2024-01-01&end=2024-01-31&interval=1d
    ```
    """
    return handle_service_error(
        stock_service.history(symbol, start, end, interval)
    )


# =====================================================
# 3. TICK + STRATEGY ENGINE
# =====================================================
@router.get(
    "/tick",
    response_model=Dict[str, Any],
    summary="🧠 Tick + Strategy Engine",
    description="Lấy dữ liệu intraday và chạy chiến lược (Order Block / Wyckoff / SMC)."
)
def tick(
    symbol: str = Query(
        ...,
        example="VNM",
        description="Mã cổ phiếu"
    ),
    start: str = Query(
        ...,
        example="2024-02-01 09:00:00",
        description="Thời gian bắt đầu"
    ),
    end: str = Query(
        ...,
        example="2024-02-01 14:30:00",
        description="Thời gian kết thúc"
    ),
    limit: int = Query(
        1000,
        example=1000,
        description="Số lượng tick tối đa"
    ),
    block_threshold: int = Query(
        10000,
        example=20000,
        description="Ngưỡng khối lượng để xác định Order Block"
    ),
    strategies: str | None = Query(
        None,
        example="order_block,smc",
        description="Danh sách strategy: order_block, wyckoff, smc"
    )
):
    """
    Ví dụ:
    ```
    GET /stock/tick?symbol=VNM&start=2024-02-01 09:00:00&end=2024-02-01 14:30:00&strategies=order_block,smc
    ```
    """
    return handle_service_error(
        stock_service.tick(
            symbol=symbol,
            start=start,
            end=end,
            limit=limit,
            block_threshold=block_threshold,
            strategies=strategies
        )
    )


# =====================================================
# 4. LAST 5 MINUTES – SCALPING MODE
# =====================================================
@router.get(
    "/last5min",
    response_model=Dict[str, Any],
    summary="⚡ 5 phút gần nhất (Scalping)",
    description="Lấy tick 5 phút gần nhất + optional Strategy Engine."
)
def last_5_min(
    symbol: str = Query(
        ...,
        example="FPT",
        description="Mã cổ phiếu"
    ),
    strategies: str | None = Query(
        None,
        example="order_block",
        description="Strategy chạy realtime"
    )
):
    """
    Ví dụ:
    ```
    GET /stock/last5min?symbol=FPT&strategies=order_block
    ```
    """
    return handle_service_error(
        stock_service.last_minutes(
            symbol=symbol,
            minutes=5,
            strategies=strategies
        )
    )
