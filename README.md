# 📈 Stocks-VietNam

Dự án **Stocks-VietNam** cung cấp API tra cứu dữ liệu chứng khoán Việt Nam theo thời gian thực và lịch sử, đồng thời tích hợp các chiến lược phân tích kỹ thuật như **Order Block**, **Wyckoff**, và **SMC**.

---

## 🚀 Tính năng chính
- **Snapshot**: Lấy giá cổ phiếu hiện tại (intraday).
- **History**: Lấy dữ liệu lịch sử theo ngày / giờ / phút.
- **Tick + Strategy Engine**: Lấy dữ liệu intraday và chạy chiến lược phân tích.
- **Last Minutes (Scalping)**: Lấy dữ liệu 5 phút gần nhất để giao dịch nhanh.

---

## 🛠️ Công nghệ sử dụng
- **Python 3.10+**
- **FastAPI**: xây dựng REST API.
- **vnstock**: thư viện lấy dữ liệu chứng khoán Việt Nam.
- **Pandas**: xử lý dữ liệu.
- **Docker** (tùy chọn): triển khai nhanh.

---

## 📦 Cài đặt

Clone dự án:
```bash
git clone https://github.com/lunarist2406/Stocks-VietNam.git
cd Stocks-VietNam
