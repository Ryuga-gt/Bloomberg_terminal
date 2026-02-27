from app.data_loader import load_ohlc_from_csv_string  # module does not exist yet -> RED

SAMPLE_CSV = """\
timestamp,open,high,low,close,volume
2024-01-01T09:30:00,150.0,152.5,149.0,151.5,1000000
2024-01-01T09:31:00,151.5,153.0,151.0,152.0,850000
2024-01-01T09:32:00,152.0,154.0,151.5,153.5,920000
"""

REQUIRED_KEYS = {"timestamp", "open", "high", "low", "close", "volume"}


def test_load_ohlc_returns_list_of_dicts():
    result = load_ohlc_from_csv_string(SAMPLE_CSV)
    assert isinstance(result, list)


def test_load_ohlc_length_matches_row_count():
    result = load_ohlc_from_csv_string(SAMPLE_CSV)
    assert len(result) == 3  # three data rows, header excluded


def test_load_ohlc_each_item_has_required_keys():
    result = load_ohlc_from_csv_string(SAMPLE_CSV)
    for item in result:
        assert isinstance(item, dict), f"expected dict, got {type(item)}"
        missing = REQUIRED_KEYS - item.keys()
        assert not missing, f"item missing keys: {missing}"


def test_load_ohlc_empty_csv_returns_empty_list():
    result = load_ohlc_from_csv_string("timestamp,open,high,low,close,volume\n")
    assert result == []
