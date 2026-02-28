"""
Tests for data layer (data_provider, cache, yahoo_provider, alpha_vantage_provider).

These tests cover:
- Abstract interface raises NotImplementedError
- JSONFileCache: make_key, has/get/set/clear
- YahooProvider: parse logic (no real HTTP calls)
- AlphaVantageProvider: validation, parse logic (no real HTTP calls)
"""

import json
import os
import tempfile
import pytest

from data.data_provider import MarketDataProvider
from data.cache import JSONFileCache
from data.yahoo_provider import YahooProvider
from data.alpha_vantage_provider import AlphaVantageProvider


# ===========================================================================
# Part 1 — Abstract interface
# ===========================================================================

def test_abstract_provider_raises():
    provider = MarketDataProvider()
    with pytest.raises(NotImplementedError):
        provider.get_historical("AAPL", "2020-01-01", "2020-12-31")


# ===========================================================================
# Part 2 — JSONFileCache
# ===========================================================================

def test_cache_make_key_deterministic():
    k1 = JSONFileCache.make_key("AAPL", "2020-01-01", "2020-12-31", "1d")
    k2 = JSONFileCache.make_key("AAPL", "2020-01-01", "2020-12-31", "1d")
    assert k1 == k2


def test_cache_make_key_different_for_different_params():
    k1 = JSONFileCache.make_key("AAPL", "2020-01-01", "2020-12-31", "1d")
    k2 = JSONFileCache.make_key("GOOG", "2020-01-01", "2020-12-31", "1d")
    assert k1 != k2


def test_cache_has_returns_false_for_missing():
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = JSONFileCache(cache_dir=tmpdir)
        assert cache.has("nonexistent_key") is False


def test_cache_set_and_get():
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = JSONFileCache(cache_dir=tmpdir)
        data = [{"timestamp": "2020-01-01", "close": 100.0}]
        key = "test_key"
        cache.set(key, data)
        assert cache.has(key) is True
        result = cache.get(key)
        assert result == data


def test_cache_get_missing_raises_key_error():
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = JSONFileCache(cache_dir=tmpdir)
        with pytest.raises(KeyError):
            cache.get("nonexistent")


def test_cache_clear_removes_entry():
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = JSONFileCache(cache_dir=tmpdir)
        cache.set("k", [{"close": 1.0}])
        cache.clear("k")
        assert cache.has("k") is False


def test_cache_clear_all():
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = JSONFileCache(cache_dir=tmpdir)
        cache.set("k1", [{"close": 1.0}])
        cache.set("k2", [{"close": 2.0}])
        cache.clear_all()
        assert cache.has("k1") is False
        assert cache.has("k2") is False


def test_cache_clear_nonexistent_no_error():
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = JSONFileCache(cache_dir=tmpdir)
        cache.clear("nonexistent")  # should not raise


# ===========================================================================
# Part 3 — YahooProvider._parse (unit test without HTTP)
# ===========================================================================

def _make_yahoo_response(timestamps, opens, highs, lows, closes, volumes):
    return json.dumps({
        "chart": {
            "result": [{
                "timestamp": timestamps,
                "indicators": {
                    "quote": [{
                        "open":   opens,
                        "high":   highs,
                        "low":    lows,
                        "close":  closes,
                        "volume": volumes,
                    }]
                }
            }]
        }
    })


def test_yahoo_parse_valid_response():
    raw = _make_yahoo_response(
        timestamps=[1577836800, 1577923200],  # 2020-01-01, 2020-01-02
        opens=[300.0, 305.0],
        highs=[310.0, 315.0],
        lows=[295.0, 300.0],
        closes=[305.0, 310.0],
        volumes=[1000000.0, 1100000.0],
    )
    candles = YahooProvider._parse(raw)
    assert len(candles) == 2
    assert candles[0]["close"] == pytest.approx(305.0)
    assert candles[1]["close"] == pytest.approx(310.0)


def test_yahoo_parse_empty_result():
    raw = json.dumps({"chart": {"result": []}})
    candles = YahooProvider._parse(raw)
    assert candles == []


def test_yahoo_parse_invalid_json():
    candles = YahooProvider._parse("not json")
    assert candles == []


def test_yahoo_parse_missing_fields():
    raw = json.dumps({"chart": {"result": [{"timestamp": [1577836800]}]}})
    candles = YahooProvider._parse(raw)
    # Missing quote data → empty
    assert candles == []


def test_yahoo_parse_candle_has_required_keys():
    raw = _make_yahoo_response(
        timestamps=[1577836800],
        opens=[300.0],
        highs=[310.0],
        lows=[295.0],
        closes=[305.0],
        volumes=[1000000.0],
    )
    candles = YahooProvider._parse(raw)
    assert len(candles) == 1
    for key in ("timestamp", "open", "high", "low", "close", "volume"):
        assert key in candles[0]


def test_yahoo_parse_skips_none_values():
    raw = _make_yahoo_response(
        timestamps=[1577836800, 1577923200],
        opens=[300.0, None],
        highs=[310.0, 315.0],
        lows=[295.0, 300.0],
        closes=[305.0, 310.0],
        volumes=[1000000.0, 1100000.0],
    )
    candles = YahooProvider._parse(raw)
    assert len(candles) == 1  # second candle skipped


# ===========================================================================
# Part 4 — AlphaVantageProvider validation
# ===========================================================================

def test_alpha_vantage_no_api_key_raises(monkeypatch):
    monkeypatch.delenv("ALPHA_VANTAGE_API_KEY", raising=False)
    with pytest.raises(ValueError):
        AlphaVantageProvider(api_key=None)


def test_alpha_vantage_explicit_api_key():
    provider = AlphaVantageProvider(api_key="test_key")
    assert provider is not None


def test_alpha_vantage_invalid_interval_raises():
    provider = AlphaVantageProvider(api_key="test_key")
    with pytest.raises(ValueError):
        provider._fetch("AAPL", "2020-01-01", "2020-12-31", "invalid")


def test_alpha_vantage_parse_daily():
    raw = json.dumps({
        "Time Series (Daily)": {
            "2020-01-02": {
                "1. open": "300.0",
                "2. high": "310.0",
                "3. low":  "295.0",
                "4. close": "305.0",
                "6. volume": "1000000",
            },
            "2020-01-03": {
                "1. open": "305.0",
                "2. high": "315.0",
                "3. low":  "300.0",
                "4. close": "310.0",
                "6. volume": "1100000",
            },
        }
    })
    candles = AlphaVantageProvider._parse(raw, "1d", "2020-01-01", "2020-12-31")
    assert len(candles) == 2
    assert candles[0]["timestamp"] == "2020-01-02"
    assert candles[0]["close"] == pytest.approx(305.0)


def test_alpha_vantage_parse_filters_by_date():
    raw = json.dumps({
        "Time Series (Daily)": {
            "2019-12-31": {"1. open": "290.0", "2. high": "295.0",
                           "3. low": "285.0", "4. close": "292.0", "6. volume": "900000"},
            "2020-01-02": {"1. open": "300.0", "2. high": "310.0",
                           "3. low": "295.0", "4. close": "305.0", "6. volume": "1000000"},
        }
    })
    candles = AlphaVantageProvider._parse(raw, "1d", "2020-01-01", "2020-12-31")
    assert len(candles) == 1
    assert candles[0]["timestamp"] == "2020-01-02"


def test_alpha_vantage_parse_invalid_json():
    candles = AlphaVantageProvider._parse("not json", "1d", "2020-01-01", "2020-12-31")
    assert candles == []


def test_alpha_vantage_parse_no_time_series_key():
    raw = json.dumps({"Note": "API rate limit reached"})
    candles = AlphaVantageProvider._parse(raw, "1d", "2020-01-01", "2020-12-31")
    assert candles == []
