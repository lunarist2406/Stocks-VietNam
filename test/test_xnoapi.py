# test/test_xnoapi.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # thêm root vào path

from src.providers.xnoapi_provider import XnoAPIProvider

provider = XnoAPIProvider()
df = provider.intraday("EIB", limit=1)
print(df)
