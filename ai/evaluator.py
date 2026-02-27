"""
ai/evaluator.py — Strategy evaluator backed by the deterministic Backtester.

StrategyEvaluator.evaluate(strategy_class, candles: list[dict]) -> dict

Returns a dict containing:
    final_equity   — cash value at the end of the backtest
    sharpe_ratio   — mean_return / std_dev (0.0 when std_dev == 0)
    calmar_ratio   — return_pct / abs(max_drawdown_pct) (0.0 when no drawdown)
    fitness_score  — sharpe_ratio - (abs(max_drawdown_pct) / 100)

Design constraints
------------------
- Input candles are never mutated; a shallow copy is passed to the engine.
- The Backtester is used as the single source of truth for all metrics.
- Behaviour is fully deterministic for the same inputs.
"""

from __future__ import annotations

from app.backtester.engine import Backtester

_INITIAL_CASH: float = 1000.0


class StrategyEvaluator:
    """
    Evaluate a strategy class against a set of candles using the deterministic
    Backtester engine.

    Usage::

        ev = StrategyEvaluator()
        metrics = ev.evaluate(MyStrategyClass, candles)
        print(metrics["fitness_score"])
    """

    def evaluate(self, strategy_class: type, candles: list[dict]) -> dict:
        """
        Run a backtest for *strategy_class* over *candles* and return a
        metrics dictionary.

        Parameters
        ----------
        strategy_class:
            A class (not an instance) that, when instantiated with no
            arguments, exposes ``generate(candles: list[dict]) -> list[str]``.
        candles:
            A list of OHLCV dicts.  This list and its elements are **not**
            mutated.

        Returns
        -------
        dict with keys:
            ``final_equity``, ``sharpe_ratio``, ``calmar_ratio``,
            ``fitness_score``.
        """
        # Shallow-copy each candle dict so the engine cannot mutate the caller's
        # data even if it were ever modified to write into candles.
        candles_copy = [dict(c) for c in candles]

        strategy_instance = strategy_class()

        bt = Backtester(initial_cash=_INITIAL_CASH)
        raw = bt.run(candles_copy, strategy=strategy_instance)

        sharpe: float = raw["sharpe_ratio"]
        calmar: float = raw["calmar_ratio"]
        final_equity: float = raw["final_equity"]
        max_drawdown_pct: float = raw["max_drawdown_pct"]

        # fitness_score = sharpe_ratio - (abs(max_drawdown_pct) / 100)
        fitness_score: float = sharpe - (abs(max_drawdown_pct) / 100.0)

        return {
            "final_equity": final_equity,
            "sharpe_ratio": sharpe,
            "calmar_ratio": calmar,
            "fitness_score": fitness_score,
        }
