"""
data.cache
==========

Simple JSON file-based cache for market data responses.

Cache keys are derived from a hash of (symbol, start, end, interval).
Cached data is stored as JSON files in a configurable directory.

Usage
-----
    cache = JSONFileCache(cache_dir=".market_cache")
    key = cache.make_key("AAPL", "2020-01-01", "2023-01-01", "1d")
    if cache.has(key):
        candles = cache.get(key)
    else:
        candles = fetch_from_api(...)
        cache.set(key, candles)
"""

import hashlib
import json
import os


class JSONFileCache:
    """
    File-based JSON cache for market data.

    Parameters
    ----------
    cache_dir : str, optional
        Directory where cache files are stored.  Created if it does not
        exist.  Default ``".market_cache"``.
    """

    def __init__(self, cache_dir: str = ".market_cache") -> None:
        self._cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

    # ------------------------------------------------------------------

    @staticmethod
    def make_key(symbol: str, start: str, end: str, interval: str) -> str:
        """
        Compute a deterministic cache key from the request parameters.

        Returns
        -------
        str
            Hex digest of SHA-256 hash.
        """
        raw = f"{symbol}|{start}|{end}|{interval}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def _path(self, key: str) -> str:
        return os.path.join(self._cache_dir, f"{key}.json")

    def has(self, key: str) -> bool:
        """Return ``True`` if *key* is present in the cache."""
        return os.path.isfile(self._path(key))

    def get(self, key: str) -> list:
        """
        Retrieve cached data for *key*.

        Returns
        -------
        list[dict]

        Raises
        ------
        KeyError
            If *key* is not in the cache.
        """
        path = self._path(key)
        if not os.path.isfile(path):
            raise KeyError(f"Cache miss for key {key!r}")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def set(self, key: str, data: list) -> None:
        """
        Store *data* under *key*.

        Parameters
        ----------
        key : str
        data : list[dict]
        """
        path = self._path(key)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)

    def clear(self, key: str) -> None:
        """Remove a single cache entry (no-op if not present)."""
        path = self._path(key)
        if os.path.isfile(path):
            os.remove(path)

    def clear_all(self) -> None:
        """Remove all cache entries in the cache directory."""
        for fname in os.listdir(self._cache_dir):
            if fname.endswith(".json"):
                os.remove(os.path.join(self._cache_dir, fname))
