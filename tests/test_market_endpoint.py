from fastapi.testclient import TestClient
from app.main import app, CANDLE_KEYS  # CANDLE_KEYS does not exist yet -> RED

client = TestClient(app)

EXPECTED_CANDLE_KEYS = {"timestamp", "open", "high", "low", "close", "volume"}


def _assert_candle_structure(item: dict) -> None:
    """Assert every item in data[] has exactly the required keys."""
    assert isinstance(item, dict), f"data item must be a dict, got {type(item)}"
    missing = EXPECTED_CANDLE_KEYS - item.keys()
    assert not missing, f"data item missing keys: {missing}"


def test_get_market_returns_200_with_schema():
    response = client.get("/api/market")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["symbol"], str)
    assert isinstance(body["data"], list)
    for item in body["data"]:
        _assert_candle_structure(item)


def test_get_market_reflects_symbol_query_param():
    response = client.get("/api/market?symbol=AAPL")
    assert response.status_code == 200
    body = response.json()
    assert body["symbol"] == "AAPL"


def test_candle_keys_match_expected_contract():
    """CANDLE_KEYS exported from app.main must equal the expected set."""
    assert set(CANDLE_KEYS) == EXPECTED_CANDLE_KEYS
