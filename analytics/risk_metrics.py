"""
analytics.risk_metrics
======================

Core portfolio risk and return metrics computed from an equity curve.

All computations are pure Python, O(n), deterministic, and non-mutating.

Metrics
-------
total_return()          — (E_final - E_initial) / E_initial
cagr()                  — annualised growth rate (252 periods/year)
volatility()            — sample std of simple returns (Bessel-corrected)
sharpe()                — mean_return / volatility  (0 if vol == 0)
downside_deviation()    — sample std of negative returns only (0 if none)
sortino_ratio()         — mean_return / downside_deviation (0 if dd == 0)

Simple returns
--------------
    r_t = (E_t - E_{t-1}) / E_{t-1}   for t = 1 … n-1

Validation
----------
* ``equity_curve`` must have length >= 2 → ``ValueError``
* All values must be > 0 → ``ValueError``
"""

import math


class RiskMetrics:
    """
    Risk and return metrics for a single equity curve.

    Parameters
    ----------
    equity_curve : list[float]
        Chronological portfolio equity values.  Length >= 2, all > 0.

    Raises
    ------
    ValueError
        If ``equity_curve`` has fewer than 2 elements or contains
        non-positive values.
    """

    def __init__(self, equity_curve: list) -> None:
        if len(equity_curve) < 2:
            raise ValueError(
                f"equity_curve must have at least 2 elements, "
                f"got {len(equity_curve)}"
            )
        for i, v in enumerate(equity_curve):
            if v <= 0:
                raise ValueError(
                    f"equity_curve values must be > 0; "
                    f"got {v!r} at index {i}"
                )

        self._curve = list(equity_curve)  # defensive copy
        self._returns = self._compute_returns()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _compute_returns(self) -> list:
        """Simple period returns r_t = (E_t - E_{t-1}) / E_{t-1}."""
        returns = []
        for i in range(1, len(self._curve)):
            r = (self._curve[i] - self._curve[i - 1]) / self._curve[i - 1]
            returns.append(r)
        return returns

    @staticmethod
    def _mean(values: list) -> float:
        if not values:
            return 0.0
        return sum(values) / len(values)

    @staticmethod
    def _sample_std(values: list) -> float:
        """Sample standard deviation (Bessel-corrected, n-1)."""
        n = len(values)
        if n < 2:
            return 0.0
        mu = sum(values) / n
        variance = sum((x - mu) ** 2 for x in values) / (n - 1)
        return math.sqrt(variance)

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def total_return(self) -> float:
        """
        Total return over the full equity curve.

        Returns
        -------
        float
            (E_final - E_initial) / E_initial
        """
        return (self._curve[-1] - self._curve[0]) / self._curve[0]

    def cagr(self) -> float:
        """
        Compound Annual Growth Rate assuming 252 trading periods per year.

        Returns
        -------
        float
        """
        n = len(self._curve) - 1          # number of periods
        years = n / 252.0
        if years <= 0:
            return 0.0
        ratio = self._curve[-1] / self._curve[0]
        return ratio ** (1.0 / years) - 1.0

    def volatility(self) -> float:
        """
        Annualised sample volatility of simple returns (× √252).

        Returns
        -------
        float
        """
        return self._sample_std(self._returns) * math.sqrt(252)

    def sharpe(self) -> float:
        """
        Sharpe ratio: annualised mean return / annualised volatility.

        Returns 0 if volatility is zero.

        Returns
        -------
        float
        """
        mu = self._mean(self._returns) * 252
        vol = self.volatility()
        if vol == 0.0:
            return 0.0
        return mu / vol

    def downside_deviation(self) -> float:
        """
        Annualised downside deviation (sample std of negative returns × √252).

        Returns 0 if there are no negative returns.

        Returns
        -------
        float
        """
        neg = [r for r in self._returns if r < 0]
        if not neg:
            return 0.0
        return self._sample_std(neg) * math.sqrt(252)

    def sortino_ratio(self) -> float:
        """
        Sortino ratio: annualised mean return / downside deviation.

        Returns 0 if downside deviation is zero.

        Returns
        -------
        float
        """
        mu = self._mean(self._returns) * 252
        dd = self.downside_deviation()
        if dd == 0.0:
            return 0.0
        return mu / dd
