from src.providers.vnstock_provider import VnStockProvider


class AutoPositionCalculator:
    """
    Trade tay nhưng auto hóa:
    - Input: symbol, side, entry (VND), quantity, rr, account_balance (VND)
    - Auto: current price, stop loss, take profit
    - Không crash khi market sideway
    """

    @staticmethod
    def _fallback_stop_loss(entry: float, side: str, pct: float = 0.01) -> float:
        """
        Fallback SL theo % entry (default 1%)
        """
        if side.lower() == "long":
            return entry * (1 - pct)
        else:
            return entry * (1 + pct)

    @staticmethod
    def calculate(
        *,
        symbol: str,
        side: str,
        entry: float,                # VND (vd: 22000)
        quantity: int,
        rr: float,
        account_balance: float,      # VND (vd: 20_000_000)
        lookback: int = 20,
        risk_rule_pct: float = 2.0,
        alert_pnl_pct: float = 5.0,
    ):
        # ===== Validate input =====
        if quantity <= 0:
            raise ValueError("Quantity phải > 0")
        if account_balance <= 0:
            raise ValueError("Account balance phải > 0")
        if rr <= 0:
            raise ValueError("RR phải > 0")
        if side.lower() not in {"long", "short"}:
            raise ValueError("Side phải là long hoặc short")

        is_long = side.lower() == "long"

        provider = VnStockProvider()

        # ===== Get intraday OHLC =====
        df = provider.intraday(
            symbol=symbol,
            limit=lookback * 5,
            interval="1min"  # tránh deprecated "1T"
        )

        if df is None or df.empty:
            raise ValueError("Không lấy được dữ liệu intraday")

        recent = df.tail(lookback)

        required_cols = {"open", "high", "low", "close"}
        if not required_cols.issubset(recent.columns):
            raise ValueError(
                f"Intraday thiếu OHLC, nhận được: {recent.columns.tolist()}"
            )

        current_price = float(recent["close"].iloc[-1])

        # ===== Auto Stop Loss =====
        raw_stop_loss = (
            recent["low"].min() if is_long
            else recent["high"].max()
        )

        risk_per_unit = abs(entry - raw_stop_loss)

        if risk_per_unit <= 0:
            stop_loss = AutoPositionCalculator._fallback_stop_loss(entry, side)
            sl_source = "fallback_1pct"
            risk_per_unit = abs(entry - stop_loss)
        else:
            stop_loss = raw_stop_loss
            sl_source = "intraday_low_high"

        # ===== Take Profit theo RR =====
        take_profit = (
            entry + rr * risk_per_unit
            if is_long
            else entry - rr * risk_per_unit
        )

        # ===== PnL =====
        pnl_current = (
            (current_price - entry) * quantity
            if is_long
            else (entry - current_price) * quantity
        )

        risk_amount = risk_per_unit * quantity
        reward_amount = abs(take_profit - entry) * quantity

        pnl_account_pct = pnl_current / account_balance * 100
        risk_account_pct = risk_amount / account_balance * 100

        # ===== Status =====
        if pnl_current > 0:
            status = "profit"
        elif pnl_current < 0:
            status = "loss"
        else:
            status = "breakeven"

        # ===== Alerts =====
        alerts = []

        if risk_account_pct > risk_rule_pct:
            alerts.append(
                f"⚠️ Risk {risk_account_pct:.2f}% vượt rule {risk_rule_pct}%"
            )

        if pnl_account_pct >= alert_pnl_pct:
            alerts.append(f"🚀 Lãi {pnl_account_pct:.2f}% tài khoản")
        elif pnl_account_pct <= -alert_pnl_pct:
            alerts.append(f"🩸 Lỗ {abs(pnl_account_pct):.2f}% tài khoản")

        # ===== Response =====
        return {
            "symbol": symbol,
            "side": side,

            # Prices (VND)
            "entry": round(entry),
            "current_price": round(current_price),
            "stop_loss": round(stop_loss),
            "stop_loss_source": sl_source,
            "take_profit": round(take_profit),

            # Position
            "quantity": quantity,
            "rr": rr,

            # Risk / Reward (VND)
            "risk_per_unit": round(risk_per_unit),
            "risk_amount": round(risk_amount),
            "reward_amount": round(reward_amount),

            # Account impact (%)
            "risk_account_pct": round(risk_account_pct, 2),
            "pnl_current": round(pnl_current),
            "pnl_account_pct": round(pnl_account_pct, 2),

            "status": status,
            "alerts": alerts,

            "is_risk_allowed": bool(risk_account_pct <= risk_rule_pct),
        }
