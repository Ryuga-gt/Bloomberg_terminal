from fastapi import FastAPI
from pydantic import BaseModel

from app.data_loader import load_ohlc_from_csv_string

app = FastAPI()


class MarketCandle(BaseModel):
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class MarketResponse(BaseModel):
    symbol: str
    data: list[MarketCandle]


CANDLE_KEYS = tuple(MarketCandle.model_fields.keys())


@app.get("/api/market", response_model=MarketResponse)
def get_market(symbol: str = "TEST", csv_data: str | None = None):
    data = load_ohlc_from_csv_string(csv_data) if csv_data is not None else []
    return MarketResponse(symbol=symbol, data=data)
