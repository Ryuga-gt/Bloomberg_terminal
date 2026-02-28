"""
execution.decay_detector
========================

Performance decay detector for individual strategies.

A strategy is considered *decayed* when its chosen metric falls below a
configured threshold.

Usage
-----
    detector = PerformanceDecayDetector(threshold=0.5, metric="sharpe")
    if detector.is_decayed(ranking_result):
        ...  # disable this strategy

Supported metrics
-----------------
sharpe
    Uses ``ranking_result["backtest"]["sharpe_ratio"]``.

robustness
    Uses ``ranking_result["robustness"]``.

Validation
----------
* ``metric`` must be ``"sharpe"`` or ``"robustness"`` → ``ValueError``
* Input ``ranking_result`` is never mutated.
* Deterministic.
"""

_VALID_METRICS = frozenset({"sharpe", "robustness"})


class PerformanceDecayDetector:
    """
    Detect whether a strategy's performance has decayed below a threshold.

    Parameters
    ----------
    threshold : float
        Minimum acceptable metric value.  A strategy is decayed when
        ``metric_value < threshold``.
    metric : str, optional
        Which metric to evaluate.  One of ``"sharpe"`` or
        ``"robustness"``.  Default ``"sharpe"``.

    Raises
    ------
    ValueError
        If ``metric`` is not one of the supported values.
    """

    def __init__(self, threshold: float, metric: str = "sharpe") -> None:
        if metric not in _VALID_METRICS:
            raise ValueError(
                f"metric must be one of {sorted(_VALID_METRICS)}, "
                f"got {metric!r}"
            )
        self._threshold = float(threshold)
        self._metric = metric

    # ------------------------------------------------------------------

    @property
    def threshold(self) -> float:
        return self._threshold

    @property
    def metric(self) -> str:
        return self._metric

    # ------------------------------------------------------------------

    def is_decayed(self, ranking_result: dict) -> bool:
        """
        Return ``True`` if the strategy's metric is below the threshold.

        Parameters
        ----------
        ranking_result : dict
            A single entry from ``StrategyRankingEngine.run()``.
            Must contain ``"backtest"`` (with ``"sharpe_ratio"``) and
            ``"robustness"``.  Not mutated.

        Returns
        -------
        bool
            ``True`` when ``metric_value < threshold``.
        """
        if self._metric == "sharpe":
            value = ranking_result["backtest"]["sharpe_ratio"]
        else:  # robustness
            value = ranking_result["robustness"]

        return value < self._threshold
