from fastapi import APIRouter, Query
from pydantic import BaseModel
from src.services.calculator.position_calculator import AutoPositionCalculator
from src.services.calculator.position_sizer import PositionSizer

router = APIRouter()

# ================= Example Models =================
class CalculatePositionExample(BaseModel):
    symbol: str = "EIB"
    side: str = "long"
    entry: float = 22.65
    stop_loss: float = 21.0
    take_profit: float = 24.8
    current_price: float = 21.45
    quantity: int = 100
    account_balance: float = 3000

class SuggestQuantityExample(BaseModel):
    entry: float = 22.65
    stop_loss: float = 21.0
    account_balance: float = 3000
    risk_pct: float = 2.0
    lot_size: int = 100

# ================= Routes =================
@router.get("/manual")
def manual_trade_calculate(
    symbol: str = Query(..., example="EIB"),
    side: str = Query("long", regex="^(long|short)$", example="long"),
    entry: float = Query(..., gt=0, example=22.65),
    quantity: int = Query(..., gt=0, example=100),
    rr: float = Query(2.0, gt=0, example=2.0),
    account_balance: float = Query(..., gt=0, example=3000),
):
    return AutoPositionCalculator.calculate(
        symbol=symbol,
        side=side,
        entry=entry,
        quantity=quantity,
        rr=rr,
        account_balance=account_balance,
    )

@router.get("/suggest-quantity", summary="Gợi ý quantity theo rule 2%", response_model=dict)
def suggest_quantity(
    entry: float = Query(..., gt=0, example=22.65),
    stop_loss: float = Query(..., gt=0, example=21.0),
    account_balance: float = Query(..., gt=0, example=3000),
    risk_pct: float = Query(2.0, example=2.0),
    lot_size: int = Query(100, example=100),
):
    """
    Tính quantity tối ưu theo rule % rủi ro và lot_size
    """
    return PositionSizer.suggest_quantity(
        entry=entry,
        stop_loss=stop_loss,
        account_balance=account_balance,
        risk_pct=risk_pct,
        lot_size=lot_size,
    )
