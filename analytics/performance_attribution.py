"""
analytics.performance_attribution
===================================

Strategy-level performance attribution for a multi-strategy portfolio.

Metrics
-------
For each strategy *i*:

    absolute_return_i   = E_i_final - E_i_initial

    contribution_pct_i  = absolute_return_i / portfolio_absolute_return
                          (0 if portfolio return == 0)

    allocation_effect_i = weight_i * strategy_return_i - equal_weight_return
    selection_effect_i  = 0  (placeholder; requires benchmark data)

where:
    weight_i            = E_i_initial / E_p_initial  (initial weight)
    strategy_return_i   = (E_i_final - E_i_initial) / E_i_initial
    equal_weight_return = mean of all strategy_return_i

All computations are pure Python, O(n), deterministic, and non-mutating.

Validation
----------
* ``portfolio_equity_curve`` must have length >= 1 → ``ValueError``
* ``strategy_equity_curves`` must not be empty → ``ValueError``
* All strategy curves must have the same length as the portfolio curve
  → ``ValueError``
"""


class PerformanceAttribution:
    """
    Strategy-level performance attribution.

    Parameters
    ----------
    portfolio_equity_curve : list[float]
        Full portfolio equity curve.
    strategy_equity_curves : dict[str, list[float]]
        Per-strategy equity curves.  All must have the same length as
        ``portfolio_equity_curve``.

    Raises
    ------
    ValueError
        If ``portfolio_equity_curve`` is empty, ``strategy_equity_curves``
        is empty, or any strategy curve has a different length.
    """

    def __init__(
        self,
        portfolio_equity_curve: list,
        strategy_equity_curves: dict,
    ) -> None:
        if len(portfolio_equity_curve) < 1:
            raise ValueError("portfolio_equity_curve must not be empty")
        if not strategy_equity_curves:
            raise ValueError("strategy_equity_curves must not be empty")

        n = len(portfolio_equity_curve)
        for name, curve in strategy_equity_curves.items():
            if len(curve) != n:
                raise ValueError(
                    f"Strategy '{name}' curve length {len(curve)} "
                    f"does not match portfolio curve length {n}"
                )

        self._portfolio = list(portfolio_equity_curve)
        self._strategies = {
            name: list(curve)
            for name, curve in strategy_equity_curves.items()
        }

    # ------------------------------------------------------------------

    def compute(self) -> dict:
        """
        Compute attribution metrics for each strategy.

        Returns
        -------
        dict[str, dict]
            Keys are strategy names.  Each value contains:
                absolute_return   : float
                contribution_pct  : float
                allocation_effect : float
                selection_effect  : float  (always 0.0)
        """
        p_initial = self._portfolio[0]
        p_final   = self._portfolio[-1]
        p_abs_return = p_final - p_initial

        # Per-strategy initial weights and returns
        strategy_returns = {}
        for name, curve in self._strategies.items():
            s_initial = curve[0]
            s_final   = curve[-1]
            s_return  = (s_final - s_initial) / s_initial if s_initial != 0 else 0.0
            strategy_returns[name] = s_return

        # Equal-weight return (mean of all strategy returns)
        n_strats = len(strategy_returns)
        equal_weight_return = (
            sum(strategy_returns.values()) / n_strats
            if n_strats > 0 else 0.0
        )

        result = {}
        for name, curve in self._strategies.items():
            s_initial = curve[0]
            s_final   = curve[-1]
            s_abs_return = s_final - s_initial

            # Contribution percentage
            if p_abs_return != 0.0:
                contribution_pct = s_abs_return / p_abs_return
            else:
                contribution_pct = 0.0

            # Initial weight in portfolio
            weight = s_initial / p_initial if p_initial != 0 else 0.0

            # Allocation effect
            s_return = strategy_returns[name]
            allocation_effect = weight * s_return - equal_weight_return

            result[name] = {
                "absolute_return":   s_abs_return,
                "contribution_pct":  contribution_pct,
                "allocation_effect": allocation_effect,
                "selection_effect":  0.0,
            }

        return result
