"""
analytics.rolling_metrics
==========================

Rolling window metrics for an equity curve.

All computations are pure Python, O(n), deterministic, and non-mutating.

Methods
-------
rolling_volatility(window)      — annualised sample std of returns in window
rolling_sharpe(window)          — annualised mean / std of returns in window
rolling_max_drawdown(window)    — max drawdown within each rolling window

Rules
-----
* ``window`` must be >= 2 → ``ValueError``
* Returned lists have the same length as the equity curve.
* Positions where a full window is not yet available are padded with ``None``.
* Annualisation factor: √252 for volatility, ×252 for mean.

Validation
----------
* ``equity_curve`` must have length >= 1 → ``ValueError``
* All values must be > 0 → ``ValueError``
"""

import math


class RollingMetrics:
    """
    Rolling window metrics for a single equity curve.

    Parameters
    ----------
    equity_curve : list[float]
        Chronological portfolio equity values.  Length >= 1, all > 0.

    Raises
    ------
    ValueError
        If ``equity_curve`` is empty or contains non-positive values.
    """

    def __init__(self, equity_curve: list) -> None:
        if len(equity_curve) < 1:
            raise ValueError("equity_curve must not be empty")
        for i, v in enumerate(equity_curve):
            if v <= 0:
                raise ValueError(
                    f"equity_curve values must be > 0; "
                    f"got {v!r} at index {i}"
                )
        self._curve = list(equity_curve)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _returns(self) -> list:
        """Simple period returns."""
        r = []
        for i in range(1, len(self._curve)):
            r.append(
                (self._curve[i] - self._curve[i - 1]) / self._curve[i - 1]
            )
        return r

    @staticmethod
    def _sample_std(values: list) -> float:
        n = len(values)
        if n < 2:
            return 0.0
        mu = sum(values) / n
        var = sum((x - mu) ** 2 for x in values) / (n - 1)
        return math.sqrt(var)

    @staticmethod
    def _mean(values: list) -> float:
        if not values:
            return 0.0
        return sum(values) / len(values)

    @staticmethod
    def _window_max_drawdown(equity_window: list) -> float:
        """Max drawdown within a sub-window of equity values."""
        peak = equity_window[0]
        min_dd = 0.0
        for v in equity_window:
            if v > peak:
                peak = v
            dd = (v - peak) / peak
            if dd < min_dd:
                min_dd = dd
        return min_dd

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def rolling_volatility(self, window: int) -> list:
        """
        Annualised rolling volatility (sample std × √252).

        Parameters
        ----------
        window : int
            Rolling window size.  Must be >= 2.

        Returns
        -------
        list
            Length equals ``len(equity_curve)``.  First ``window`` entries
            are ``None``; subsequent entries are floats.

        Raises
        ------
        ValueError
            If ``window`` < 2.
        """
        if window < 2:
            raise ValueError(f"window must be >= 2, got {window!r}")

        returns = self._returns()
        n = len(self._curve)
        result = [None] * n

        # returns[i] corresponds to equity_curve[i+1]
        # A window of `window` returns requires equity indices [i, i+window]
        # i.e. returns indices [i, i+window-1]
        for i in range(window - 1, len(returns)):
            w_returns = returns[i - window + 1 : i + 1]
            vol = self._sample_std(w_returns) * math.sqrt(252)
            result[i + 1] = vol  # align to equity_curve index

        return result

    def rolling_sharpe(self, window: int) -> list:
        """
        Annualised rolling Sharpe ratio.

        Parameters
        ----------
        window : int
            Rolling window size.  Must be >= 2.

        Returns
        -------
        list
            Length equals ``len(equity_curve)``.  First ``window`` entries
            are ``None``; subsequent entries are floats (0.0 if vol == 0).

        Raises
        ------
        ValueError
            If ``window`` < 2.
        """
        if window < 2:
            raise ValueError(f"window must be >= 2, got {window!r}")

        returns = self._returns()
        n = len(self._curve)
        result = [None] * n

        for i in range(window - 1, len(returns)):
            w_returns = returns[i - window + 1 : i + 1]
            mu = self._mean(w_returns) * 252
            vol = self._sample_std(w_returns) * math.sqrt(252)
            sharpe = 0.0 if vol == 0.0 else mu / vol
            result[i + 1] = sharpe

        return result

    def rolling_max_drawdown(self, window: int) -> list:
        """
        Rolling maximum drawdown within each window of equity values.

        Parameters
        ----------
        window : int
            Rolling window size.  Must be >= 2.

        Returns
        -------
        list
            Length equals ``len(equity_curve)``.  First ``window - 1``
            entries are ``None``; subsequent entries are floats (<= 0).

        Raises
        ------
        ValueError
            If ``window`` < 2.
        """
        if window < 2:
            raise ValueError(f"window must be >= 2, got {window!r}")

        n = len(self._curve)
        result = [None] * n

        for i in range(window - 1, n):
            w_equity = self._curve[i - window + 1 : i + 1]
            result[i] = self._window_max_drawdown(w_equity)

        return result
