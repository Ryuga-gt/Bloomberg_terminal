from fastapi import FastAPI
from pydantic import BaseModel

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
def get_market(symbol: str = "TEST"):
    return MarketResponse(symbol=symbol, data=[])
