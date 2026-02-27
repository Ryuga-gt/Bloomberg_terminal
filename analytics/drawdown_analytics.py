"""
analytics.drawdown_analytics
=============================

Drawdown analysis for an equity curve.

All computations are O(n), pure Python, deterministic, and non-mutating.

Drawdown formula
----------------
    DD_t = (E_t - Peak_t) / Peak_t

where ``Peak_t = max(E_0, …, E_t)`` is the running maximum.

Methods
-------
drawdown_series()       — list of DD_t values (same length as equity_curve)
max_drawdown()          — minimum DD_t (most negative value)
max_drawdown_duration() — number of periods from the peak that caused
                          max_drawdown to the next recovery (or end)
average_drawdown()      — mean of all DD_t < 0
recovery_time()         — number of periods from the trough of max_drawdown
                          to the next point where equity >= peak

Validation
----------
* ``equity_curve`` must have length >= 1 → ``ValueError``
* All values must be > 0 → ``ValueError``
"""


class DrawdownAnalytics:
    """
    Drawdown analytics for a single equity curve.

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

        self._curve = list(equity_curve)  # defensive copy
        self._dd_series = self._compute_drawdown_series()

    # ------------------------------------------------------------------

    def _compute_drawdown_series(self) -> list:
        """Compute DD_t for every t in O(n)."""
        series = []
        peak = self._curve[0]
        for v in self._curve:
            if v > peak:
                peak = v
            dd = (v - peak) / peak
            series.append(dd)
        return series

    # ------------------------------------------------------------------

    def drawdown_series(self) -> list:
        """
        Return the full drawdown series.

        Returns
        -------
        list[float]
            DD_t for each period.  Values are <= 0.
        """
        return list(self._dd_series)

    def max_drawdown(self) -> float:
        """
        Maximum (most negative) drawdown.

        Returns
        -------
        float
            min(DD_t).  0.0 for a monotonically non-decreasing curve.
        """
        return min(self._dd_series)

    def max_drawdown_duration(self) -> int:
        """
        Number of periods from the peak that caused the maximum drawdown
        to the next full recovery (equity >= peak), or to the end of the
        series if no recovery occurs.

        Returns
        -------
        int
        """
        n = len(self._curve)
        if n == 1:
            return 0

        # Find the index of the maximum drawdown
        min_dd = self.max_drawdown()
        trough_idx = self._dd_series.index(min_dd)

        # Walk back to find the peak before the trough
        peak_val = self._curve[trough_idx]
        peak_idx = trough_idx
        for i in range(trough_idx + 1):
            if self._curve[i] >= peak_val:
                peak_val = self._curve[i]
                peak_idx = i

        # Walk forward from peak_idx to find recovery
        for i in range(peak_idx + 1, n):
            if self._curve[i] >= peak_val:
                return i - peak_idx

        # No recovery — duration to end
        return n - 1 - peak_idx

    def average_drawdown(self) -> float:
        """
        Mean of all negative drawdown values.

        Returns 0.0 if there are no drawdowns.

        Returns
        -------
        float
        """
        neg = [d for d in self._dd_series if d < 0]
        if not neg:
            return 0.0
        return sum(neg) / len(neg)

    def recovery_time(self) -> int:
        """
        Number of periods from the trough of the maximum drawdown to the
        next point where equity >= the peak that preceded the trough.

        Returns 0 if the curve never draws down, or the number of periods
        remaining if no recovery occurs.

        Returns
        -------
        int
        """
        n = len(self._curve)
        if n == 1:
            return 0

        min_dd = self.max_drawdown()
        if min_dd == 0.0:
            return 0

        trough_idx = self._dd_series.index(min_dd)

        # Find the peak value before the trough
        peak_val = max(self._curve[: trough_idx + 1])

        # Walk forward from trough to find recovery
        for i in range(trough_idx + 1, n):
            if self._curve[i] >= peak_val:
                return i - trough_idx

        # No recovery
        return n - 1 - trough_idx
