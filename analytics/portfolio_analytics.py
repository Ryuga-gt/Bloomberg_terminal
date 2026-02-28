"""
analytics.portfolio_analytics
==============================

Master analytics wrapper that aggregates all analytics modules into a
single ``full_report()`` call.

Usage
-----
    from analytics.portfolio_analytics import PortfolioAnalytics

    pa = PortfolioAnalytics(
        portfolio_equity_curve=equity_curve,
        strategy_equity_curves={"StratA": curve_a, "StratB": curve_b},
    )
    report = pa.full_report()

Validation
----------
* ``portfolio_equity_curve`` must have length >= 2 → ``ValueError``
* All values must be > 0 → ``ValueError``
"""

from analytics.risk_metrics import RiskMetrics
from analytics.drawdown_analytics import DrawdownAnalytics
from analytics.rolling_metrics import RollingMetrics
from analytics.var_engine import ValueAtRisk
from analytics.performance_attribution import PerformanceAttribution

_ROLLING_WINDOW = 20


class PortfolioAnalytics:
    """
    Master analytics wrapper.

    Parameters
    ----------
    portfolio_equity_curve : list[float]
        Full portfolio equity curve.  Length >= 2, all > 0.
    strategy_equity_curves : dict[str, list[float]] or None, optional
        Per-strategy equity curves for attribution analysis.
        Default ``None`` (attribution skipped).

    Raises
    ------
    ValueError
        If ``portfolio_equity_curve`` has fewer than 2 elements or
        contains non-positive values.
    """

    def __init__(
        self,
        portfolio_equity_curve: list,
        strategy_equity_curves: dict = None,
    ) -> None:
        # Validate via RiskMetrics (raises on bad input)
        self._risk = RiskMetrics(portfolio_equity_curve)
        self._dd   = DrawdownAnalytics(portfolio_equity_curve)
        self._roll = RollingMetrics(portfolio_equity_curve)

        # Build returns for VaR
        curve = portfolio_equity_curve
        returns = [
            (curve[i] - curve[i - 1]) / curve[i - 1]
            for i in range(1, len(curve))
        ]
        self._var = ValueAtRisk(returns) if len(returns) >= 2 else None

        # Attribution
        self._attribution = None
        if strategy_equity_curves:
            self._attribution = PerformanceAttribution(
                portfolio_equity_curve, strategy_equity_curves
            )

        self._curve = list(portfolio_equity_curve)

    # ------------------------------------------------------------------

    def full_report(self) -> dict:
        """
        Compute and return the full analytics report.

        Returns
        -------
        dict with keys:
            total_return            : float
            cagr                    : float
            volatility              : float
            sharpe                  : float
            sortino                 : float
            max_drawdown            : float
            max_drawdown_duration   : int
            var_95_hist             : float or None
            var_95_param            : float or None
            rolling_sharpe_20       : list
            rolling_vol_20          : list
            attribution             : dict or None
        """
        # Rolling metrics (window=20, or smaller if curve is short)
        window = min(_ROLLING_WINDOW, len(self._curve) - 1)
        window = max(window, 2)

        rolling_sharpe = self._roll.rolling_sharpe(window)
        rolling_vol    = self._roll.rolling_volatility(window)

        # VaR
        var_95_hist  = None
        var_95_param = None
        if self._var is not None:
            var_95_hist  = self._var.historical_var(0.95)
            var_95_param = self._var.parametric_var(0.95)

        # Attribution
        attribution = None
        if self._attribution is not None:
            attribution = self._attribution.compute()

        return {
            "total_return":          self._risk.total_return(),
            "cagr":                  self._risk.cagr(),
            "volatility":            self._risk.volatility(),
            "sharpe":                self._risk.sharpe(),
            "sortino":               self._risk.sortino_ratio(),
            "max_drawdown":          self._dd.max_drawdown(),
            "max_drawdown_duration": self._dd.max_drawdown_duration(),
            "var_95_hist":           var_95_hist,
            "var_95_param":          var_95_param,
            "rolling_sharpe_20":     rolling_sharpe,
            "rolling_vol_20":        rolling_vol,
            "attribution":           attribution,
        }
