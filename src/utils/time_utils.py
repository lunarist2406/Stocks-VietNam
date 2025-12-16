# utils/time_utils.py
import pytz
from datetime import datetime

VN_TZ = pytz.timezone("Asia/Ho_Chi_Minh")

def normalize_range(start: str, end: str) -> tuple[datetime, datetime]:
    s = datetime.fromisoformat(start)
    e = datetime.fromisoformat(end)

    if s.tzinfo is None:
        s = VN_TZ.localize(s)
    if e.tzinfo is None:
        e = VN_TZ.localize(e)

    return s, e
