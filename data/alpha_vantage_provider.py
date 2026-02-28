"""
data.alpha_vantage_provider
============================

Market data provider backed by Alpha Vantage (free tier, API key required).

API key
-------
Set the environment variable ``ALPHA_VANTAGE_API_KEY`` before use::

    export ALPHA_VANTAGE_API_KEY=your_key_here

Supported functions
-------------------
Daily historical  — TIME_SERIES_DAILY_ADJUSTED
Intraday          — TIME_SERIES_INTRADAY (interval: 1min, 5min, 15min, 30min, 60min)

Free tier limits: 25 requests/day, 5 requests/minute.
"""

import json
import os
import urllib.request
import urllib.error

from data.data_provider import MarketDataProvider
from data.cache import JSONFileCache

_BASE_URL = "https://www.alphavantage.co/query"

_INTRADAY_INTERVALS = {"1min", "5min", "15min", "30min", "60min"}


class AlphaVantageProvider(MarketDataProvider):
    """
    Market data provider backed by Alpha Vantage.

    Parameters
    ----------
    api_key : str or None, optional
        Alpha Vantage API key.  If ``None``, reads from the environment
        variable ``ALPHA_VANTAGE_API_KEY``.
    cache : JSONFileCache or None, optional
        Optional file cache.  Default ``None``.
    timeout : int, optional
        HTTP request timeout in seconds.  Default 15.

    Raises
    ------
    ValueError
        If no API key is available.
    """

    def __init__(
        self,
        api_key: str = None,
        cache: JSONFileCache = None,
        timeout: int = 15,
    ) -> None:
        key = api_key or os.environ.get("ALPHA_VANTAGE_API_KEY", "")
        if not key:
            raise ValueError(
                "Alpha Vantage API key required. "
                "Set ALPHA_VANTAGE_API_KEY environment variable or pass api_key."
            )
        self._api_key = key
        self._cache = cache
        self._timeout = timeout

    # ------------------------------------------------------------------

    def get_historical(
        self,
        symbol: str,
        start: str,
        end: str,
        interval: str = "1d",
    ) -> list:
        """
        Fetch historical OHLCV candles from Alpha Vantage.

        Parameters
        ----------
        symbol : str
            Ticker symbol.
        start : str
            Start date ``"YYYY-MM-DD"``.
        end : str
            End date ``"YYYY-MM-DD"``.
        interval : str, optional
            ``"1d"`` for daily, or intraday intervals
            (``"1min"``, ``"5min"``, ``"15min"``, ``"30min"``, ``"60min"``).
            Default ``"1d"``.

        Returns
        -------
        list[dict]
            Chronological OHLCV candles filtered to [start, end].

        Raises
        ------
        RuntimeError
            On HTTP errors.
        ValueError
            If *interval* is not supported.
        """
        if self._cache is not None:
            key = self._cache.make_key(symbol, start, end, interval)
            if self._cache.has(key):
                return self._cache.get(key)

        candles = self._fetch(symbol, start, end, interval)

        if self._cache is not None:
            self._cache.set(key, candles)

        return candles

    def _fetch(self, symbol: str, start: str, end: str, interval: str) -> list:
        if interval == "1d":
            function = "TIME_SERIES_DAILY_ADJUSTED"
            params = (
                f"?function={function}&symbol={symbol}"
                f"&outputsize=full&apikey={self._api_key}&datatype=json"
            )
        elif interval in _INTRADAY_INTERVALS:
            function = "TIME_SERIES_INTRADAY"
            params = (
                f"?function={function}&symbol={symbol}"
                f"&interval={interval}&outputsize=full"
                f"&apikey={self._api_key}&datatype=json"
            )
        else:
            raise ValueError(
                f"Unsupported interval {interval!r}. "
                f"Use '1d' or one of {sorted(_INTRADAY_INTERVALS)}."
            )

        url = _BASE_URL + params
        req = urllib.request.Request(url)
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                raw = resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            raise RuntimeError(
                f"HTTP error {e.code} fetching {symbol!r}: {e.reason}"
            ) from e
        except urllib.error.URLError as e:
            raise RuntimeError(
                f"Network error fetching {symbol!r}: {e.reason}"
            ) from e

        return self._parse(raw, interval, start, end)

    @staticmethod
    def _parse(raw: str, interval: str, start: str, end: str) -> list:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return []

        # Find the time series key
        ts_key = None
        for k in data:
            if "Time Series" in k:
                ts_key = k
                break

        if ts_key is None:
            return []

        series = data[ts_key]
        candles = []

        for date_str, values in series.items():
            day = date_str[:10]  # "YYYY-MM-DD"
            if day < start or day > end:
                continue
            try:
                candles.append({
                    "timestamp": day,
                    "open":   float(values.get("1. open",   values.get("1. open", 0))),
                    "high":   float(values.get("2. high",   values.get("2. high", 0))),
                    "low":    float(values.get("3. low",    values.get("3. low",  0))),
                    "close":  float(values.get("4. close",  values.get("4. close", 0))),
                    "volume": float(values.get("6. volume", values.get("5. volume", 0))),
                })
            except (KeyError, ValueError):
                continue

        # Sort chronologically
        candles.sort(key=lambda c: c["timestamp"])
        return candles
