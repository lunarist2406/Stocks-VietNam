#!/usr/bin/env python
"""
Test script để kiểm tra VNStock API columns
Chạy: python test_vnstock.py
"""

from vnstock import Vnstock

def test_intraday():
    """Test intraday data và in ra columns"""
    print("="*80)
    print("🧪 TEST INTRADAY DATA")
    print("="*80)
    
    try:
        client = Vnstock()
        
        # Test với FPT
        symbol = "FPT"
        print(f"\n📡 Fetching intraday data for {symbol}...")
        
        df = client.stock(symbol=symbol, source="VCI").quote.intraday(
            symbol=symbol,
            page_size=10,
            show_log=False
        )
        
        if df is None or df.empty:
            print("❌ No data returned")
            return
        
        print(f"✅ Got {len(df)} rows")
        print(f"\n📊 Columns: {df.columns.tolist()}")
        print(f"\n📋 Data types:")
        print(df.dtypes)
        print(f"\n🔍 First 5 rows:")
        print(df.head())
        print(f"\n📈 Sample values:")
        print(df.iloc[0].to_dict())
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


def test_history():
    """Test history data và in ra columns"""
    print("\n" + "="*80)
    print("🧪 TEST HISTORY DATA")
    print("="*80)
    
    try:
        client = Vnstock()
        
        symbol = "FPT"
        print(f"\n📡 Fetching history data for {symbol}...")
        
        df = client.stock(symbol=symbol, source="VCI").quote.history(
            start="2024-12-01",
            end="2024-12-17",
            interval="1D"
        )
        
        if df is None or df.empty:
            print("❌ No data returned")
            return
        
        print(f"✅ Got {len(df)} rows")
        print(f"\n📊 Columns: {df.columns.tolist()}")
        print(f"\n📋 Data types:")
        print(df.dtypes)
        print(f"\n🔍 First 5 rows:")
        print(df.head())
        print(f"\n📈 Sample values:")
        print(df.iloc[0].to_dict())
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


def test_sources():
    """Test different data sources"""
    print("\n" + "="*80)
    print("🧪 TEST DIFFERENT SOURCES")
    print("="*80)
    
    sources = ["VCI", "TCBS"]
    symbol = "FPT"
    
    for source in sources:
        print(f"\n📡 Testing source: {source}")
        try:
            client = Vnstock()
            df = client.stock(symbol=symbol, source=source).quote.intraday(
                symbol=symbol,
                page_size=5,
                show_log=False
            )
            
            if df is not None and not df.empty:
                print(f"  ✅ {source}: {df.columns.tolist()}")
            else:
                print(f"  ❌ {source}: No data")
                
        except Exception as e:
            print(f"  ❌ {source}: {e}")


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                        VNStock API Column Tester                             ║
║                  Kiểm tra cấu trúc dữ liệu từ VNStock API                   ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    test_intraday()
    test_history()
    test_sources()
    
    print("\n" + "="*80)
    print("✅ TEST COMPLETED")
    print("="*80)
    print("\nℹ️  Dựa vào kết quả trên để update COLUMN_MAP trong VnStockProvider")
    print()