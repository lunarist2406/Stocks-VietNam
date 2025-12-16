import os
from dotenv import load_dotenv

# Load biến môi trường từ file .env
load_dotenv()

# Default values (nếu không truyền query thì dùng giá trị này)
DEFAULT_SOURCE = os.getenv("DEFAULT_SOURCE", "VCI")
DEFAULT_LIMIT = int(os.getenv("DEFAULT_LIMIT", 50))
DEFAULT_START_DATE = os.getenv("DEFAULT_START_DATE", "2025-12-15")
DEFAULT_END_DATE = os.getenv("DEFAULT_END_DATE", "2025-12-15")
