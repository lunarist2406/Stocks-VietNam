from fastapi import FastAPI
from src.controllers import stock_controller

app = FastAPI(
    title="VN Stock API",
    version="1.0.0",
    description="Realtime Vietnam Stock API using vnstock"
)

# Đăng ký router
app.include_router(stock_controller.router)

@app.get("/")
def root():
    return {"message": "VN Stock API is running"}
