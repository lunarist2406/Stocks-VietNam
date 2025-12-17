# 📈 Stocks-VietNam

Dự án **Stocks-VietNam** cung cấp API tra cứu dữ liệu chứng khoán Việt Nam theo **thời gian thực** và **lịch sử**, đồng thời tích hợp các chiến lược phân tích kỹ thuật hiện đại như **Order Block**, **Wyckoff**, và **SMC (Smart Money Concept)**.

---

## 🚀 Tính năng chính

* **Snapshot (Live Price)**
  Lấy giá cổ phiếu hiện tại (intraday).

* **History**
  Lấy dữ liệu lịch sử theo **ngày / giờ / phút**.

* **Tick + Strategy Engine**
  Lấy dữ liệu intraday và chạy các chiến lược phân tích kỹ thuật.

* **Last Minutes (Scalping)**
  Lấy dữ liệu **5 phút gần nhất** để phục vụ giao dịch nhanh.

---

## 🛠️ Công nghệ sử dụng

* **Python 3.10+**
* **FastAPI** – xây dựng REST API
* **vnstock** – lấy dữ liệu chứng khoán Việt Nam
* **Pandas** – xử lý và phân tích dữ liệu
* **Docker** *(tùy chọn)* – triển khai nhanh

---

## 📦 Cài đặt

### 1️⃣ Clone dự án

```bash
git clone https://github.com/lunarist2406/Stocks-VietNam.git
cd Stocks-VietNam
```

### 2️⃣ Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### 3️⃣ Chạy server

```bash
uvicorn src.api.main:app --reload --port 8000
```

---

## ⚙️ Cấu hình

Các biến môi trường được định nghĩa trong file `.env`:

```env
DEFAULT_SOURCE=VCI
DEFAULT_LIMIT=50
DEFAULT_START_DATE=2025-12-15 09:00:00
DEFAULT_END_DATE=2025-12-15 15:00:00
```

---

## 📡 API Endpoints

### 1️⃣ Snapshot giá cổ phiếu hiện tại

```http
GET /api/v1/stock/live?symbol=FPT
```

---

### 2️⃣ Lịch sử giá theo khoảng thời gian

```http
GET /api/v1/stock/history?symbol=FPT&start=2024-01-01&end=2024-01-31&interval=1d
```

---

### 3️⃣ Tick + Strategy Engine

```http
GET /api/v1/stock/tick?symbol=VNM&start=2024-02-01 09:00:00&end=2024-02-01 14:30:00&strategies=order_block,smc
```

---

### 4️⃣ Last 5 Minutes (Scalping)

```http
GET /api/v1/stock/last5min?symbol=FPT&strategies=wyckoff
```

---

## 🧠 Các chiến lược tích hợp

* **Order Block**
  Phát hiện các vùng có khối lượng giao dịch lớn vượt ngưỡng.

* **SMC (Smart Money Concept)**
  Phát hiện **Break of Structure (BOS)** – dấu hiệu dòng tiền lớn tham gia.

* **Wyckoff**
  Phát hiện mô hình **Spring** – giá giảm nhưng khối lượng tăng.

---

## 📊 Ví dụ Response

```json
{
  "symbol": "VNM",
  "from": "2024-02-01T09:00:00",
  "to": "2024-02-01T14:30:00",
  "records": [],
  "order_blocks": [],
  "signals": {
    "order_block": [],
    "smc": [],
    "wyckoff": []
  }
}
```

---

## 📌 Ghi chú

* API phù hợp cho **dashboard phân tích**, **bot trading**, hoặc **hệ thống cảnh báo giá**.
* Dữ liệu phụ thuộc vào nguồn cung cấp từ `vnstock`.
* Không khuyến nghị dùng trực tiếp cho quyết định đầu tư tài chính.

---

🔥 Nếu bạn thấy project hữu ích, đừng quên **star ⭐ repo** để ủng hộ nhé!
