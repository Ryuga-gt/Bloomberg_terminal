"""
ai.fitness_evaluator
=====================

Fitness evaluator for strategy genomes.

Converts a genome to a strategy class, runs it through the backtester
and analytics layer, and returns a scalar fitness score.

Fitness score
-------------
The fitness score is the composite score from the existing
``StrategyRankingEngine``, which combines:

    1.0 * sharpe_ratio
  + 0.8 * calmar_ratio
  + 1.2 * stability_score
  + 1.5 * robustness_score
  - 1.0 * abs(max_drawdown_pct)
  - 1.0 * abs(performance_decay)

For speed in the evolution loop, a lightweight fitness function is also
provided that uses only the backtester (no Monte Carlo / walk-forward).

Usage
-----
    evaluator = FitnessEvaluator(candles, mode="fast")
    score = evaluator.evaluate(genome)
"""

import copy

from ai.strategy_genome import genome_to_strategy_class
from app.backtester.engine import Backtester
from analytics.risk_metrics import RiskMetrics


class FitnessEvaluator:
    """
    Evaluate the fitness of a strategy genome on a candle dataset.

    Parameters
    ----------
    candles : list[dict]
        Historical OHLCV candles.  Not mutated.
    initial_cash : float, optional
        Starting cash for the backtester.  Default 1000.
    mode : str, optional
        ``"fast"`` — uses only Backtester + RiskMetrics (O(n)).
        ``"full"`` — uses StrategyRankingEngine (slower, more accurate).
        Default ``"fast"``.

    Raises
    ------
    ValueError
        If ``mode`` is not ``"fast"`` or ``"full"``.
    """

    def __init__(
        self,
        candles: list,
        initial_cash: float = 1000,
        mode: str = "fast",
    ) -> None:
        if mode not in ("fast", "full"):
            raise ValueError(f"mode must be 'fast' or 'full', got {mode!r}")
        self._candles = candles
        self._initial_cash = float(initial_cash)
        self._mode = mode

    # ------------------------------------------------------------------

    def evaluate(self, genome: dict) -> float:
        """
        Compute the fitness score for *genome*.

        Parameters
        ----------
        genome : dict
            A valid genome dict.

        Returns
        -------
        float
            Fitness score.  Higher is better.
        """
        strategy_class = genome_to_strategy_class(genome)

        if self._mode == "fast":
            return self._fast_fitness(strategy_class)
        else:
            return self._full_fitness(strategy_class)

    def _fast_fitness(self, strategy_class: type) -> float:
        """Lightweight fitness: Sharpe + Calmar - abs(max_drawdown)."""
        bt = Backtester(self._initial_cash)
        try:
            result = bt.run(
                [copy.copy(c) for c in self._candles],
                strategy=strategy_class(),
            )
        except Exception:
            return -999.0

        sharpe  = result.get("sharpe_ratio", 0.0)
        calmar  = result.get("calmar_ratio", 0.0)
        mdd     = result.get("max_drawdown_pct", 0.0)

        return 1.0 * sharpe + 0.8 * calmar - 1.0 * abs(mdd)

    def _full_fitness(self, strategy_class: type) -> float:
        """Full fitness using StrategyRankingEngine composite score."""
        from research.strategy_ranking_engine import StrategyRankingEngine
        try:
            engine = StrategyRankingEngine(
                strategies=[strategy_class],
                candles=[copy.copy(c) for c in self._candles],
                initial_cash=self._initial_cash,
                train_size=max(10, len(self._candles) // 5),
                test_size=max(5, len(self._candles) // 10),
                step_size=max(5, len(self._candles) // 10),
                simulations=20,
            )
            results = engine.run()
            return results[0]["composite_score"]
        except Exception:
            return -999.0
