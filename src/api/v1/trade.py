from fastapi import APIRouter, Query, HTTPException
from src.services.trade.trade_service import TradeService
import traceback

router = APIRouter(tags=["Trade"])
trade_service = TradeService()


@router.get("/signal")
def trade_signal(
    symbol: str = Query(...),
    minutes: int = Query(120),
    strategies: str = Query("smc,order_block,wyckoff"),
    rr_min: float = Query(2.0)
):
    try:
        result = trade_service.generate_signal(symbol, strategies, rr_min, minutes)
        return {
            "symbol": symbol,
            "minutes": minutes,
            **result
        }
    except Exception as e:
        # Log full traceback
        print(f"❌ ERROR in /signal:")
        print(traceback.format_exc())
        
        # Return detailed error
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "type": type(e).__name__,
                "symbol": symbol,
                "strategies": strategies
            }
        )


@router.get("/scan")
def scan_signals(
    symbols: str = Query(...),
    timeframe: str = Query("5m"),
    strategies: str = Query("smc,order_block,wyckoff"),
    rr_min: float = Query(2.0)
):
    try:
        symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]

        if len(symbol_list) > 10:
            return {"status": "error", "error": "Maximum 10 symbols per scan"}

        result = trade_service.scan_signals(symbol_list, strategies, rr_min)

        return {
            "timeframe": timeframe,
            "strategies": strategies,
            "rr_min": rr_min,
            **result
        }
    except Exception as e:
        print(f"❌ ERROR in /scan:")
        print(traceback.format_exc())
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "type": type(e).__name__,
                "symbols": symbols
            }
        )


@router.get("/validate")
def validate_signal(
    symbol: str = Query(...),
    entry: float = Query(...),
    sl: float = Query(...),
    tp: float = Query(...)
):
    try:
        return trade_service.validate_trade(symbol, entry, sl, tp)
    except Exception as e:
        print(f"❌ ERROR in /validate:")
        print(traceback.format_exc())
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "type": type(e).__name__
            }
        )