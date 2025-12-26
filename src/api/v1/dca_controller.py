# src/controllers/dca_controller.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from src.services.calculator.dca_service import DCAService

router = APIRouter()
dca_service = DCAService()  # Dùng XnoAPIProvider mặc định

# ================================
# Schema request
# ================================
class DCACalcRequest(BaseModel):
    symbol: str
    current_qty: int
    additional_qty: int
    additional_price: Optional[float] = None  # giá dự kiến mua thêm

# Schema response
class DCACalcResponse(BaseModel):
    symbol: str
    current_qty: int
    additional_qty: int
    total_qty: int
    current_price: float        # giá intraday hiện tại
    additional_price: float     # giá dự kiến hoặc intraday nếu không nhập
    total_cost: float
    dca: float

# ================================
# Controller
# ================================
@router.post("/dca", response_model=DCACalcResponse)
def calculate_dca(request: DCACalcRequest = DCACalcRequest(
    symbol="EIB",
    current_qty=2000,
    additional_qty=4000,
    additional_price=21850
)):
    """
    Tính toán DCA (VND Cost Averaging)
    
    Data mẫu mặc định:
    - symbol: EIB
    - current_qty: 2000
    - additional_qty: 4000
    - additional_price: 21850
    """
    if request.current_qty < 0 or request.additional_qty < 0:
        raise HTTPException(status_code=400, detail="Số lượng cổ phiếu không hợp lệ")

    try:
        # current_price không truyền, service tự lấy intraday
        result = dca_service.calculate_dca(
            symbol=request.symbol,
            current_qty=request.current_qty,
            additional_qty=request.additional_qty,
            additional_price=request.additional_price
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return result