"""
ai.fitness_evaluator
=====================

Fitness evaluator for strategy genomes.

Converts a genome to a strategy class, runs it through the backtester
and returns a scalar fitness score.

Fitness formula (fast mode)
---------------------------
    fitness = sharpe_ratio - abs(max_drawdown_pct) * 0.5

Rules
-----
* Negative Sharpe is allowed — it is NOT penalised with a sentinel value.
* Only truly invalid results (NaN, None, or backtester exception with
  zero trades) receive a penalty.
* The penalty for zero-trade strategies is -10.0 (not -999).
* fitness is always a finite float.

Usage
-----
    evaluator = FitnessEvaluator(candles, mode="fast")
    score = evaluator.evaluate(genome)
"""

import copy
import math

from ai.strategy_genome import genome_to_strategy_class
from app.backtester.engine import Backtester


# Penalty for strategies that produce no trades or invalid analytics
_ZERO_TRADE_PENALTY = -10.0


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
        ``"fast"`` — uses only Backtester (O(n)).
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
            Fitness score.  Higher is better.  Always a finite float.
        """
        strategy_class = genome_to_strategy_class(genome)

        if self._mode == "fast":
            return self._fast_fitness(strategy_class)
        else:
            return self._full_fitness(strategy_class)

    def _fast_fitness(self, strategy_class: type) -> float:
        """
        Lightweight fitness: sharpe - abs(max_drawdown) * 0.5

        Negative Sharpe is valid and returned as-is.
        Only penalises strategies that produce zero trades or NaN metrics.
        """
        bt = Backtester(self._initial_cash)
        try:
            result = bt.run(
                [copy.copy(c) for c in self._candles],
                strategy=strategy_class(),
            )
        except Exception:
            # Backtester raised — penalise but not with -999
            return _ZERO_TRADE_PENALTY

        sharpe = result.get("sharpe_ratio", 0.0)
        mdd    = result.get("max_drawdown_pct", 0.0)

        # Guard against NaN / None
        if sharpe is None or (isinstance(sharpe, float) and math.isnan(sharpe)):
            sharpe = 0.0
        if mdd is None or (isinstance(mdd, float) and math.isnan(mdd)):
            mdd = 0.0

        # Penalise zero-trade strategies (equity never changed)
        equity_curve = result.get("equity_curve", [])
        if len(equity_curve) >= 2:
            if equity_curve[0] == equity_curve[-1]:
                # No PnL at all — mild penalty
                return _ZERO_TRADE_PENALTY

        fitness = float(sharpe) - abs(float(mdd)) * 0.5
        assert not math.isnan(fitness), f"fitness is NaN: sharpe={sharpe}, mdd={mdd}"
        return fitness

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
            score = results[0]["composite_score"]
            if score is None or (isinstance(score, float) and math.isnan(score)):
                return _ZERO_TRADE_PENALTY
            return float(score)
        except Exception:
            return _ZERO_TRADE_PENALTY
