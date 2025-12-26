import os
from dotenv import load_dotenv
from datetime import datetime

# Load biến môi trường từ file .env
load_dotenv()

class Config:
    # Default values (nếu không truyền query thì dùng giá trị này)
    DEFAULT_SOURCE = os.getenv("DEFAULT_SOURCE", "VCI")
    XNOAPI_KEY = os.getenv("XNOAPI_KEY", "")
    try:
        DEFAULT_LIMIT = int(os.getenv("DEFAULT_LIMIT") or 50)
    except ValueError:
        DEFAULT_LIMIT = 50

    # Ngày/giờ mặc định: nên để định dạng đầy đủ YYYY-MM-DD HH:MM:SS
    DEFAULT_START_DATE = os.getenv("DEFAULT_START_DATE", "2025-12-15 09:00:00")
    DEFAULT_END_DATE = os.getenv("DEFAULT_END_DATE", "2025-12-15 15:00:00")

    # Optional: validate định dạng ngày/giờ
    @staticmethod
    def validate_datetime(date_str: str):
        try:
            datetime.fromisoformat(date_str)
            return True
        except ValueError:
            print(f"[Config Warning] Ngày/giờ không đúng định dạng ISO: {date_str}")
            return False

    # Kiểm tra ngay khi load
    validate_datetime(DEFAULT_START_DATE)
    validate_datetime(DEFAULT_END_DATE)
