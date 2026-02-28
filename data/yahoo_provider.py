"""
data.yahoo_provider
====================

Free market data provider using Yahoo Finance's public chart API.

No API key required.

Endpoint
--------
    https://query1.finance.yahoo.com/v8/finance/chart/{symbol}

Parameters
----------
    period1 : Unix timestamp (start)
    period2 : Unix timestamp (end)
    interval : e.g. "1d", "1h", "1wk"

Error handling
--------------
* Network errors → raises ``RuntimeError``
* Empty / malformed response → returns ``[]``
* Rate limit (HTTP 429) → raises ``RuntimeError`` with message
"""

import json
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

from data.data_provider import MarketDataProvider
from data.cache import JSONFileCache
from data.indian_symbol_mapper import map_symbol as _map_indian_symbol


def _to_unix(date_str: str) -> int:
    """Convert 'YYYY-MM-DD' to Unix timestamp (UTC midnight)."""
    dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return int(dt.timestamp())


def _from_unix(ts: int) -> str:
    """Convert Unix timestamp to 'YYYY-MM-DD' string."""
    return datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d")


class YahooProvider(MarketDataProvider):
    """
    Market data provider backed by Yahoo Finance (free, no API key).

    Parameters
    ----------
    cache : JSONFileCache or None, optional
        If provided, responses are cached to avoid repeated HTTP calls.
        Default ``None`` (no caching).
    timeout : int, optional
        HTTP request timeout in seconds.  Default 10.
    """

    _BASE_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"

    def __init__(self, cache: JSONFileCache = None, timeout: int = 10) -> None:
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
        Fetch historical OHLCV candles from Yahoo Finance.

        Parameters
        ----------
        symbol : str
            Ticker symbol, e.g. ``"AAPL"``.
        start : str
            Start date ``"YYYY-MM-DD"``.
        end : str
            End date ``"YYYY-MM-DD"``.
        interval : str, optional
            Data interval.  Default ``"1d"``.

        Returns
        -------
        list[dict]
            Chronological OHLCV candles.

        Raises
        ------
        RuntimeError
            On HTTP errors or rate limiting.
        """
        # Convert Indian NSE:/BSE: symbols to Yahoo Finance format transparently
        yahoo_symbol = _map_indian_symbol(symbol)

        # Check cache (use original symbol as key for consistency)
        if self._cache is not None:
            key = self._cache.make_key(symbol, start, end, interval)
            if self._cache.has(key):
                return self._cache.get(key)

        candles = self._fetch(yahoo_symbol, start, end, interval)

        # Store in cache
        if self._cache is not None:
            self._cache.set(key, candles)

        return candles

    def _fetch(self, symbol: str, start: str, end: str, interval: str) -> list:
        period1 = _to_unix(start)
        period2 = _to_unix(end) + 86400  # include end date

        url = (
            self._BASE_URL.format(symbol=symbol)
            + f"?period1={period1}&period2={period2}&interval={interval}"
        )

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }

        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                if resp.status == 429:
                    raise RuntimeError(
                        f"Yahoo Finance rate limit hit for {symbol!r}"
                    )
                raw = resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            if e.code == 429:
                raise RuntimeError(
                    f"Yahoo Finance rate limit hit for {symbol!r}"
                ) from e
            raise RuntimeError(
                f"HTTP error {e.code} fetching {symbol!r}: {e.reason}"
            ) from e
        except urllib.error.URLError as e:
            raise RuntimeError(
                f"Network error fetching {symbol!r}: {e.reason}"
            ) from e

        return self._parse(raw)

    @staticmethod
    def _parse(raw: str) -> list:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return []

        try:
            result = data["chart"]["result"]
            if not result:
                return []
            chart = result[0]
            timestamps = chart.get("timestamp", [])
            indicators = chart.get("indicators", {})
            quote = indicators.get("quote", [{}])[0]

            opens   = quote.get("open",   [])
            highs   = quote.get("high",   [])
            lows    = quote.get("low",    [])
            closes  = quote.get("close",  [])
            volumes = quote.get("volume", [])

            candles = []
            for i, ts in enumerate(timestamps):
                o = opens[i]   if i < len(opens)   else None
                h = highs[i]   if i < len(highs)   else None
                lo = lows[i]   if i < len(lows)    else None
                c = closes[i]  if i < len(closes)  else None
                v = volumes[i] if i < len(volumes) else None

                # Skip candles with missing OHLCV
                if any(x is None for x in [o, h, lo, c, v]):
                    continue

                candles.append({
                    "timestamp": _from_unix(ts),
                    "open":      float(o),
                    "high":      float(h),
                    "low":       float(lo),
                    "close":     float(c),
                    "volume":    float(v),
                })

            return candles

        except (KeyError, IndexError, TypeError):
            return []
