class PositionSizer:
    """
    Gợi ý quantity theo rule % rủi ro:
    - Tính risk per unit
    - Tính quantity tối ưu dựa trên risk_pct và lot_size
    - Có thể giới hạn max_quantity
    """

    @staticmethod
    def suggest_quantity(
        *,
        entry: float,
        stop_loss: float,
        account_balance: float,
        risk_pct: float = 2.0,
        lot_size: int = 1,
        max_quantity: int | None = None,
    ):
        if entry <= 0 or stop_loss <= 0:
            raise ValueError("Entry và Stop Loss phải > 0")
        if entry == stop_loss:
            raise ValueError("Entry không được bằng Stop Loss")
        if account_balance <= 0:
            raise ValueError("Account balance phải > 0")

        risk_amount = account_balance * (risk_pct / 100)
        risk_per_unit = abs(entry - stop_loss)

        raw_qty = risk_amount / risk_per_unit

        # làm tròn theo lot
        quantity = int(raw_qty // lot_size * lot_size)

        if max_quantity:
            quantity = min(quantity, max_quantity)

        return {
            "risk_pct": risk_pct,
            "risk_amount": round(risk_amount, 2),
            "risk_per_unit": round(risk_per_unit, 4),
            "suggested_quantity": max(quantity, 0),
            "raw_quantity": round(raw_qty, 2),
        }
