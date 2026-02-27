from fastapi import FastAPI

app = FastAPI()


@app.get("/api/market")
def get_market(symbol: str = "TEST"):
    return {"symbol": symbol, "data": []}
