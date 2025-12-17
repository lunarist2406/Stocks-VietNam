from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from src.api.v1.stock import router as stock_router
from src.api.v1.trade import router as trade_router
app = FastAPI(
    title="VN Stock API",
    version="1.0.0",
    description="Realtime Vietnam Stock API using vnstock"
)

# API v1
app.include_router(
    stock_router,
    prefix="/api/v1"
)
app.include_router(
    trade_router,
    prefix="/api/v1",
    tags=["Trade"]
)
# Root → Swagger
@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")
