"""
data.data_provider
==================

Abstract base class for all market data providers.

Any concrete provider must subclass :class:`MarketDataProvider` and
implement :meth:`get_historical`.

Return format
-------------
Each candle dict must contain:

    {
        "timestamp": str,   # ISO-8601 date string
        "open":      float,
        "high":      float,
        "low":       float,
        "close":     float,
        "volume":    float,
    }
"""


class MarketDataProvider:
    """
    Abstract market data provider.

    Subclasses must override :meth:`get_historical`.
    """

    def get_historical(
        self,
        symbol: str,
        start: str,
        end: str,
        interval: str = "1d",
    ) -> list:
        """
        Fetch historical OHLCV candles for *symbol*.

        Parameters
        ----------
        symbol : str
            Ticker symbol, e.g. ``"AAPL"``.
        start : str
            Start date in ``"YYYY-MM-DD"`` format (inclusive).
        end : str
            End date in ``"YYYY-MM-DD"`` format (inclusive).
        interval : str, optional
            Data interval.  Common values: ``"1d"`` (daily),
            ``"1h"`` (hourly).  Default ``"1d"``.

        Returns
        -------
        list[dict]
            Chronological list of OHLCV candle dicts.

        Raises
        ------
        NotImplementedError
            Always — subclasses must override this method.
        """
        raise NotImplementedError(
            f"{type(self).__name__} must implement get_historical()"
        )
