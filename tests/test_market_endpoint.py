from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_get_market_returns_200_with_schema():
    response = client.get("/api/market")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["symbol"], str)
    assert isinstance(body["data"], list)


def test_get_market_reflects_symbol_query_param():
    response = client.get("/api/market?symbol=AAPL")
    assert response.status_code == 200
    body = response.json()
    assert body["symbol"] == "AAPL"
