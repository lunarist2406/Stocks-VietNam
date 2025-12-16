from datetime import datetime

def is_market_open(now: datetime) -> tuple[bool, str]:
    """
    Kiểm tra thị trường mở cửa (9h-15h).
    Trả về (True, "") nếu trong giờ giao dịch,
    ngược lại trả về (False, thông báo).
    """
    start_time = now.replace(hour=9, minute=0, second=0, microsecond=0)
    end_time = now.replace(hour=15, minute=0, second=0, microsecond=0)

    if now < start_time:
        return False, "Thị trường chưa mở cửa"
    elif now > end_time:
        return False, "Thị trường đã đóng cửa"
    return True, ""
