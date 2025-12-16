# Sử dụng image Python 3.12 chính thức
FROM python:3.12-slim

# Biến môi trường để tối ưu container
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Tạo thư mục làm việc
WORKDIR /app

# Cài các thư viện hệ thống cần thiết
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy file requirements và cài thư viện Python
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy toàn bộ mã nguồn vào container
COPY . .

# Mở port cho FastAPI
EXPOSE 8000

# Chạy ứng dụng bằng uvicorn
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
