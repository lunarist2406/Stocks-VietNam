import pandas as pd
from typing import List, Dict, Any, Optional, Union
from src.services.strategy_engine import StrategyEngine
from src.services.stock_service import StockService
from src.services.trade.trade_signal_builder import TradeSignalBuilder
from src.utils.df_utils import normalize_df_time


class TradeService:
    def __init__(self):
        self.stock_service = StockService()
        self.engine = StrategyEngine()
        self.builder = TradeSignalBuilder()

    # ==================================================
    # DATA
    # ==================================================
    def _fetch_intraday_df(
        self,
        symbol: str,
        minutes: int = 120,
        limit: int = 1000,
        interval: str = "1T"
    ):
        """
        Fetch intraday data for the last N minutes using 1-minute candles by default.
        Expects StockService.last_minutes(...) to return a dict like:
        { "records": [ {time, open, high, low, close, volume}, ... ], ... }
        """
        try:
            result = self.stock_service.last_minutes(
                symbol=symbol,
                minutes=minutes,
                limit=limit,
                interval=interval
            )
        except Exception as e:
            return None, f"Fetch data failed: {e}"

        # Validate raw result
        if result is None:
            return None, "Fetch data failed: result is None"

        if isinstance(result, dict) and "error" in result:
            return None, result.get("error", "Fetch data failed")

        # Parse records
        try:
            records = result["records"] if isinstance(result, dict) else result
            df = pd.DataFrame(records)
        except Exception as e:
            return None, f"Invalid data format: {e}"

        if df.empty or len(df) < 20:
            return None, f"Không đủ dữ liệu (có {len(df)} nến, cần ít nhất 20)"

        # Normalize time column to datetime
        try:
            df = normalize_df_time(df)
        except Exception as e:
            return None, f"Normalize time failed: {e}"

        if df.empty or len(df) < 20:
            return None, f"Không đủ dữ liệu (có {len(df)} nến, cần ít nhất 20)"

        print(f"[TradeService] ✓ Loaded {len(df)} candles for {symbol} ({minutes} phút, {interval})")
        return df, None

    # ==================================================
    # CORE PIPELINE
    # ==================================================
    def generate_signal(
        self,
        symbol: str,
        strategies: Union[str, List[str], List[Dict]],
        rr_min: float = 2.0,
        minutes: int = 120,
        interval: str = "1T",
    ) -> Dict[str, Any]:
        df, error = self._fetch_intraday_df(symbol, minutes=minutes, interval=interval)
        if error:
            return {
                "status": "no_trade",
                "reason": error,
                "symbol": symbol,
                "minutes": minutes,
                "interval": interval
            }

        try:
            strategy_results = self.engine.run(df=df, strategies=strategies)
        except Exception as e:
            return {
                "status": "no_trade",
                "reason": f"Strategy engine failed: {e}",
                "symbol": symbol,
                "minutes": minutes,
                "interval": interval,
                "from": df.iloc[0]["time"].isoformat(),
                "to": df.iloc[-1]["time"].isoformat(),
                "count": len(df),
                "records": df.to_dict(orient="records"),
                "signals": {}
            }

        if not strategy_results:
            # vẫn cho builder chạy với strategy_results rỗng
            self.builder.rr_min = rr_min
            signal = self.builder.build(df, {})
            return {
                "status": "weak_signal" if signal.get("shark_score", 0) < self.builder.shark_min_score else "trade_signal",
                "reason": "Không có tín hiệu từ strategy nào",
                "symbol": symbol,
                "minutes": minutes,
                "interval": interval,
                "shark_score": signal.get("shark_score"),
                "debug": signal.get("debug"),
                "signal": signal,
                "strategies_used": [],
                "from": df.iloc[0]["time"].isoformat(),
                "to": df.iloc[-1]["time"].isoformat(),
                "count": len(df),
                "records": df.to_dict(orient="records"),
                "signals": {}
            }


        # Build trade signal
        self.builder.rr_min = rr_min
        signal = self.builder.build(df, strategy_results)

        if not signal or not isinstance(signal, dict):
            return {
                "status": "no_trade",
                "reason": "Builder không tạo được tín hiệu",
                "symbol": symbol,
                "minutes": minutes,
                "interval": interval,
                "from": df.iloc[0]["time"].isoformat(),
                "to": df.iloc[-1]["time"].isoformat(),
                "count": len(df),
                "records": df.to_dict(orient="records"),
                "signals": strategy_results
            }

        # Decide status
        status = "trade_signal"
        reason = None
        if signal.get("shark_score", 0) < self.builder.shark_min_score:
            status = "weak_signal"
            reason = f"Shark score thấp ({signal.get('shark_score', 0)})"

        return {
            "status": status,
            "reason": reason,
            "symbol": symbol,
            "minutes": minutes,
            "interval": interval,
            "shark_score": signal.get("shark_score"),   # ✅ đưa ra ngoài
            "debug": signal.get("debug"),               # ✅ đưa ra ngoài
            "signal": signal,
            "strategies_used": list(strategy_results.keys()),
            "from": df.iloc[0]["time"].isoformat(),
            "to": df.iloc[-1]["time"].isoformat(),
            "count": len(df),
            "records": df.to_dict(orient="records"),
            "signals": strategy_results
        }


    # ==================================================
    # SCAN
    # ==================================================
    def scan_signals(
        self,
        symbols: List[str],
        strategies: Union[str, List[str], List[Dict]],
        rr_min: float = 2.0,
        minutes: int = 120,
        interval: str = "1T",
    ) -> Dict[str, Any]:
        """
        Scan multiple symbols over the last N minutes.
        """
        results: Dict[str, Any] = {
            "total_scanned": len(symbols),
            "signals": [],
            "no_setup": [],
            "errors": []
        }

        for symbol in symbols:
            try:
                res = self.generate_signal(symbol, strategies, rr_min, minutes, interval)

                if res.get("status") == "trade_signal":
                    results["signals"].append({
                        "symbol": symbol,
                        "signal": res.get("signal")
                    })
                else:
                    results["no_setup"].append({
                        "symbol": symbol,
                        "status": res.get("status"),
                        "reason": res.get("reason")
                    })

            except Exception as e:
                results["errors"].append({
                    "symbol": symbol,
                    "error": str(e)
                })

        results["signals_found"] = len(results["signals"])
        results["minutes"] = minutes
        results["interval"] = interval
        results["strategies"] = strategies
        results["rr_min"] = rr_min
        return results

    # ==================================================
    # VALIDATE
    # ==================================================
    def validate_trade(
        self,
        symbol: str,
        entry: float,
        sl: float,
        tp: float
    ) -> Dict[str, Any]:
        """
        Validate trade parameters
        """
        if sl >= entry:
            return {"valid": False, "error": "SL phải nhỏ hơn entry"}

        if tp <= entry:
            return {"valid": False, "error": "TP phải lớn hơn entry"}

        risk = entry - sl
        reward = tp - entry
        rr = reward / risk if risk > 0 else 0

        try:
            snapshot = self.stock_service.snapshot(symbol)
            current_price = snapshot.get("price") if snapshot else None
        except Exception:
            current_price = None

        return {
            "valid": True,
            "symbol": symbol,
            "entry": entry,
            "stop_loss": sl,
            "take_profit": tp,
            "rr": round(rr, 2),
            "current_price": current_price,
            "risk_pct": round(risk / entry * 100, 2),
            "reward_pct": round(reward / entry * 100, 2)
        }
