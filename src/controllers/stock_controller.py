from fastapi import APIRouter, Query, HTTPException
from typing import Dict, Any
from datetime import datetime, timedelta
import src.config as config
from src.service.stock_service import (
    fetch_stock,
    fetch_stock_by_date,
    fetch_stock_tick,
    fetch_stock_by_range
)

router = APIRouter(prefix="/stock", tags=["Stock"])


# 1. API lấy snapshot mới nhất
@router.get("/live", response_model=Dict[str, Any])
def get_stock(
    symbol: str = Query(..., description="Mã cổ phiếu VN (VD: VNM, FPT)")
):
    """
    Snapshot giá/khối lượng từ VCI, khối ngoại từ SSI/TCBS (dual-source).
    """
    data = fetch_stock(symbol)
    if isinstance(data, dict) and "error" in data:
        raise HTTPException(status_code=400, detail=data["error"])
    return data


# 2. API lấy dữ liệu theo ngày / phút / giờ
@router.get("/history", response_model=Dict[str, Any])
def get_stock_history(
    symbol: str = Query(..., description="Mã cổ phiếu VN (VD: VNM, FPT)"),
    start: str = Query(config.DEFAULT_START_DATE, description="Ngày/giờ bắt đầu"),
    end: str = Query(config.DEFAULT_END_DATE, description="Ngày/giờ kết thúc"),
    interval: str = Query("1d", description="Khoảng thời gian (1d=ngày, 1m=phút, 1h=giờ)")
):
    """
    Lịch sử giá/khối lượng từ VCI, khối ngoại từ SSI/TCBS (dual-source).
    """
    data = fetch_stock_by_date(symbol, start, end, interval)
    if isinstance(data, dict) and "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])
    return data


# 3. API lấy dữ liệu tick theo khoảng
@router.get("/tick", response_model=Dict[str, Any])
def get_stock_tick_api(
    symbol: str = Query(..., description="Mã cổ phiếu VN (VD: VNM, FPT)"),
    start: str = Query(..., description="Ngày/giờ bắt đầu (YYYY-MM-DD HH:MM:SS)"),
    end: str = Query(..., description="Ngày/giờ kết thúc (YYYY-MM-DD HH:MM:SS)"),
    limit: int = Query(10000, description="Số bản ghi tối đa")
):
    """
    Tick giá/khối lượng từ VCI, khối ngoại từ SSI/TCBS (dual-source).
    """
    data = fetch_stock_tick(symbol, start, end, limit)
    if isinstance(data, dict) and "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])
    return data


# 4. API lấy dữ liệu tick trong 5 phút gần nhất
@router.get("/last5min", response_model=Dict[str, Any])
def get_last5min(
    symbol: str = Query(..., description="Mã cổ phiếu VN (VD: VNM, FPT)")
):
    """
    Tick 5 phút gần nhất: giá/khối lượng từ VCI, khối ngoại từ SSI/TCBS (dual-source).
    """
    now = datetime.now()
    start_time = now - timedelta(minutes=5)
    start_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
    end_str = now.strftime("%Y-%m-%d %H:%M:%S")

    data = fetch_stock_tick(symbol, start_str, end_str)
    if isinstance(data, dict) and "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])
    return data
