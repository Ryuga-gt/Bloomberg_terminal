"""
execution.capital_allocator
============================

Dynamic capital weight computation for multi-strategy portfolios.

Supports three weighting modes:

equal
    All strategies receive equal weight: ``1 / N``.

sharpe
    Weights proportional to each strategy's ``sharpe_ratio`` (from the
    ``backtest`` sub-dict of a :class:`StrategyRankingEngine` result).
    Only strategies with ``sharpe_ratio > 0`` receive weight.
    If all sharpe ratios are <= 0, falls back to equal weighting.

robustness
    Weights proportional to each strategy's ``robustness`` score.
    Only strategies with ``robustness > 0`` receive weight.
    If all robustness scores are <= 0, falls back to equal weighting.

Usage
-----
    allocator = CapitalAllocator(mode="sharpe")
    weights = allocator.compute_weights(ranking_results)
    # weights == {"StrategyA": 0.6, "StrategyB": 0.4}

Input format
------------
``ranking_results`` is the list returned by
``StrategyRankingEngine.run()``.  Each element must contain at least:

    {
        "strategy_name": str,
        "backtest": {"sharpe_ratio": float, ...},
        "robustness": float,
        ...
    }

Validation
----------
* ``ranking_results`` must not be empty → ``ValueError``
* ``mode`` must be one of ``"equal"``, ``"sharpe"``, ``"robustness"``
  → ``ValueError`` for any other value
* Input list is never mutated.
* Returned weights always sum to 1.0 (within floating-point precision).
"""

_VALID_MODES = frozenset({"equal", "sharpe", "robustness"})


class CapitalAllocator:
    """
    Compute strategy weights for capital allocation.

    Parameters
    ----------
    mode : str, optional
        Weighting mode.  One of ``"equal"``, ``"sharpe"``,
        ``"robustness"``.  Default ``"equal"``.

    Raises
    ------
    ValueError
        If ``mode`` is not one of the supported values.
    """

    def __init__(self, mode: str = "equal") -> None:
        if mode not in _VALID_MODES:
            raise ValueError(
                f"mode must be one of {sorted(_VALID_MODES)}, got {mode!r}"
            )
        self._mode = mode

    # ------------------------------------------------------------------

    @property
    def mode(self) -> str:
        return self._mode

    # ------------------------------------------------------------------

    def compute_weights(self, ranking_results: list) -> dict:
        """
        Compute allocation weights for each strategy.

        Parameters
        ----------
        ranking_results : list[dict]
            Non-empty list of strategy result dicts as returned by
            ``StrategyRankingEngine.run()``.  Not mutated.

        Returns
        -------
        dict[str, float]
            Mapping of ``strategy_name`` → weight (float in (0, 1]).
            Weights sum to 1.0.

        Raises
        ------
        ValueError
            If ``ranking_results`` is empty.
        """
        if not ranking_results:
            raise ValueError("ranking_results must not be empty")

        if self._mode == "equal":
            return self._equal_weights(ranking_results)
        elif self._mode == "sharpe":
            return self._sharpe_weights(ranking_results)
        else:  # robustness
            return self._robustness_weights(ranking_results)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _equal_weights(results: list) -> dict:
        n = len(results)
        w = 1.0 / n
        return {r["strategy_name"]: w for r in results}

    @staticmethod
    def _sharpe_weights(results: list) -> dict:
        sharpes = {
            r["strategy_name"]: r["backtest"]["sharpe_ratio"]
            for r in results
        }
        positive = {name: v for name, v in sharpes.items() if v > 0}

        if not positive:
            # Fallback to equal
            n = len(results)
            return {r["strategy_name"]: 1.0 / n for r in results}

        total = sum(positive.values())
        weights = {}
        for r in results:
            name = r["strategy_name"]
            weights[name] = positive[name] / total if name in positive else 0.0

        return weights

    @staticmethod
    def _robustness_weights(results: list) -> dict:
        robustness = {
            r["strategy_name"]: r["robustness"]
            for r in results
        }
        positive = {name: v for name, v in robustness.items() if v > 0}

        if not positive:
            # Fallback to equal
            n = len(results)
            return {r["strategy_name"]: 1.0 / n for r in results}

        total = sum(positive.values())
        weights = {}
        for r in results:
            name = r["strategy_name"]
            weights[name] = positive[name] / total if name in positive else 0.0

        return weights
