import requests

BASE_URL = "http://127.0.0.1:8000/api/v1/stock"

def test_foreign_trading(symbol="EIB"):
    url = f"{BASE_URL}/live"
    resp = requests.get(url, params={"symbol": symbol})
    data = resp.json()

    print(f"=== /live: {symbol} ===")
    print(f"Giá: {data.get('price')} | KL: {data.get('volume')}")
    
    foreign = data.get("foreign_trading", [])
    if not foreign:
        print("❌ Không có dữ liệu khối ngoại")
    else:
        print("✅ Có dữ liệu khối ngoại:")
        for row in foreign[:3]:  # in tối đa 3 dòng
            print(f"  Ngày: {row['date']}, Mua: {row['buy_volume']}, Bán: {row['sell_volume']}, Ròng: {row['net_volume']}")

if __name__ == "__main__":
    test_foreign_trading("EIB")
