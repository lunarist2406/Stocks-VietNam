# src/api/routes/trade.py

from fastapi import APIRouter, Query
from src.services.stock_service import StockService
from src.services.trade_signal_builder import TradeSignalBuilder
from src.utils.df_utils import normalize_df_time
import pandas as pd

router = APIRouter(prefix="/api/v1/trade", tags=["Trade"])

stock_service = StockService()
signal_builder = TradeSignalBuilder(rr_min=2.0)


@router.get("/signal")
def trade_signal(
    symbol: str = Query(..., description="Mã cổ phiếu"),
    timeframe: str = Query("5m", description="Khung thời gian: 1m, 5m, 15m"),
    strategies: str = Query("smc,order_block,wyckoff", description="Strategies")
):
    """
    🎯 Trade Signal Generator
    
    Phân tích và tạo tín hiệu giao dịch với:
    - Entry point
    - Stop Loss
    - Take Profit
    - Risk/Reward ratio
    - Confidence score
    
    **Timeframes:**
    - `1m`: Scalping (3 phút data)
    - `5m`: Intraday (10 phút data)
    - `15m`: Swing (30 phút data)
    """
    
    # Map timeframe → minutes & interval
    timeframe_config = {
        "1m": {"minutes": 3, "interval": "1T", "limit": 300},
        "5m": {"minutes": 10, "interval": "5T", "limit": 500},
        "15m": {"minutes": 30, "interval": "15T", "limit": 500}
    }
    
    config = timeframe_config.get(timeframe)
    if not config:
        return {
            "symbol": symbol,
            "status": "error",
            "error": f"Invalid timeframe: {timeframe}. Use: 1m, 5m, 15m"
        }
    
    try:
        # Get recent data với strategies
        result = stock_service.last_minutes(
            symbol=symbol,
            minutes=config["minutes"],
            limit=config["limit"],
            strategies=strategies,
            interval=config["interval"]
        )
        
        # Check for errors
        if "error" in result:
            return {
                "symbol": symbol,
                "status": "error",
                "error": result["error"]
            }
        
        # Check if we have signals
        if "signals" not in result or not result["signals"]:
            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "status": "no_trade",
                "reason": "No strategy signals detected",
                "data_summary": {
                    "candles": result.get("count", 0),
                    "from": result.get("from"),
                    "to": result.get("to")
                }
            }
        
        # Convert records to DataFrame for analysis
        if "records" not in result or not result["records"]:
            return {
                "symbol": symbol,
                "status": "error",
                "error": "No price data available"
            }
        
        df = pd.DataFrame(result["records"])
        df = normalize_df_time(df)
        
        # Build trade signal
        trade_signal = signal_builder.build(df, result["signals"])
        
        if not trade_signal:
            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "status": "no_trade",
                "reason": "Setup found but RR/confluence not satisfied",
                "strategies_detected": list(result["signals"].keys()),
                "data_summary": {
                    "candles": len(df),
                    "from": result.get("from"),
                    "to": result.get("to")
                }
            }
        
        # Success - return full signal
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "status": "trade_signal",
            "signal": trade_signal,
            "timestamp": result.get("to"),
            "strategies_used": list(result["signals"].keys())
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "symbol": symbol,
            "status": "error",
            "error": str(e)
        }


@router.get("/scan")
def scan_signals(
    symbols: str = Query(..., description="Danh sách mã (VD: FPT,VNM,HPG)"),
    timeframe: str = Query("5m", description="Khung thời gian"),
    strategies: str = Query("smc,order_block,wyckoff", description="Strategies"),
    rr_min: float = Query(2.0, description="RR tối thiểu")
):
    """
    📡 Scan nhiều cổ phiếu cùng lúc
    
    Tìm kiếm trade signals trên nhiều mã
    """
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    
    if len(symbol_list) > 10:
        return {
            "status": "error",
            "error": "Maximum 10 symbols per scan"
        }
    
    # Update RR threshold
    builder = TradeSignalBuilder(rr_min=rr_min)
    
    results = {
        "timeframe": timeframe,
        "strategies": strategies,
        "rr_min": rr_min,
        "total_scanned": len(symbol_list),
        "signals": [],
        "no_setup": [],
        "errors": []
    }
    
    for symbol in symbol_list:
        try:
            # Reuse trade_signal logic
            signal_result = trade_signal(
                symbol=symbol,
                timeframe=timeframe,
                strategies=strategies
            )
            
            if signal_result["status"] == "trade_signal":
                results["signals"].append({
                    "symbol": symbol,
                    "signal": signal_result["signal"],
                    "timestamp": signal_result.get("timestamp")
                })
            elif signal_result["status"] == "no_trade":
                results["no_setup"].append({
                    "symbol": symbol,
                    "reason": signal_result.get("reason")
                })
            else:
                results["errors"].append({
                    "symbol": symbol,
                    "error": signal_result.get("error")
                })
                
        except Exception as e:
            results["errors"].append({
                "symbol": symbol,
                "error": str(e)
            })
    
    results["signals_found"] = len(results["signals"])
    return results


@router.get("/validate")
def validate_signal(
    symbol: str = Query(..., description="Mã cổ phiếu"),
    entry: float = Query(..., description="Entry price"),
    sl: float = Query(..., description="Stop loss"),
    tp: float = Query(..., description="Take profit")
):
    """
    ✅ Validate một trade signal
    
    Kiểm tra:
    - RR có đủ không
    - Price levels có hợp lý không
    - Market có đang open không
    """
    try:
        # Validate logic
        if sl >= entry:
            return {
                "valid": False,
                "error": "Stop loss phải nhỏ hơn entry"
            }
        
        if tp <= entry:
            return {
                "valid": False,
                "error": "Take profit phải lớn hơn entry"
            }
        
        risk = entry - sl
        reward = tp - entry
        rr = reward / risk
        
        # Get current price
        snapshot = stock_service.snapshot(symbol)
        
        if "error" in snapshot:
            current_price = None
            distance_to_entry = None
        else:
            current_price = snapshot["price"]
            distance_to_entry = abs(current_price - entry) / entry * 100
        
        return {
            "valid": True,
            "symbol": symbol,
            "entry": entry,
            "stop_loss": sl,
            "take_profit": tp,
            "risk": round(risk, 2),
            "reward": round(reward, 2),
            "rr": round(rr, 2),
            "current_price": current_price,
            "distance_to_entry_pct": round(distance_to_entry, 2) if distance_to_entry else None,
            "risk_pct": round(risk / entry * 100, 2),
            "reward_pct": round(reward / entry * 100, 2)
        }
        
    except Exception as e:
        return {
            "valid": False,
            "error": str(e)
        }