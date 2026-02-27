from fastapi.testclient import TestClient


def test_get_market_returns_200_with_schema():
    from app.main import app  # will fail: module does not exist yet
    client = TestClient(app)
    response = client.get("/api/market")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["symbol"], str)
    assert isinstance(body["data"], list)
