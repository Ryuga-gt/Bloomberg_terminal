import urllib.parse

from fastapi.testclient import TestClient
from app.main import app, CANDLE_KEYS

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


# ---------------------------------------------------------------------------
# csv_data integration — RED: endpoint ignores csv_data, always returns data=[]
# ---------------------------------------------------------------------------

_INLINE_CSV = (
    "timestamp,open,high,low,close,volume\n"
    "2024-01-02T09:30:00,180.0,182.0,179.5,181.0,500000\n"
    "2024-01-02T09:31:00,181.0,183.5,180.5,182.5,620000\n"
)


def test_csv_data_param_populates_data_list():
    """Passing csv_data should return parsed candles in data[]."""
    encoded = urllib.parse.quote(_INLINE_CSV)
    response = client.get(f"/api/market?symbol=AAPL&csv_data={encoded}")
    assert response.status_code == 200
    body = response.json()
    assert body["symbol"] == "AAPL"
    # endpoint currently ignores csv_data → data=[] → len == 0, not 2 → RED
    assert len(body["data"]) == 2
    for item in body["data"]:
        _assert_candle_structure(item)
