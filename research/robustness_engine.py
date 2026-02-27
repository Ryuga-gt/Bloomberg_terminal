"""
research.robustness_engine
==========================

Walk-forward Monte Carlo robustness engine.

Combines ``walk_forward_analysis`` fold-slicing geometry with
``MonteCarloEngine`` per-fold simulation to produce a single
*robustness score* that measures how reliably a strategy's out-of-sample
edge survives randomised return ordering.

Robustness formula
------------------
For each walk-forward fold *i*:

    R_i = mc_mean_sharpe_i  -  mc_sharpe_variance_i  -  mc_probability_of_loss_i

Global robustness score:

    R = mean(R_i  for i in folds)
"""

import copy

from app.backtester.engine import Backtester
from research.walk_forward_engine import walk_forward_analysis
from research.monte_carlo_engine import MonteCarloEngine


class RobustnessEngine:
    """
    Walk-forward Monte Carlo robustness engine.
    """

    def __init__(
        self,
        strategy_class,
        candles: list[dict],
        train_size: int,
        test_size: int,
        step_size: int,
        simulations: int = 100,
        seed=None,
        initial_cash: float = 1000,
    ) -> None:
        self._strategy_class = strategy_class
        self._candles = candles
        self._train_size = train_size
        self._test_size = test_size
        self._step_size = step_size
        self._simulations = simulations
        self._seed = seed
        self._initial_cash = initial_cash

    # ------------------------------------------------------------------
    def run(self) -> dict:
        """
        Execute the robustness analysis.
        """

        # -----------------------------
        # Explicit guards (critical fix)
        # -----------------------------
        if self._simulations < 1:
            raise ValueError("simulations must be >= 1")

        if self._train_size < 2:
            raise ValueError("train_size must be >= 2")

        if self._test_size < 2:
            raise ValueError("test_size must be >= 2")

        if self._step_size < 1:
            raise ValueError("step_size must be >= 1")

        if len(self._candles) < self._train_size + self._test_size:
            raise ValueError("Not enough candles for one complete fold")

        # Delegate validation to walk_forward_analysis
        walk_forward_analysis(
            self._strategy_class,
            self._candles,
            train_size=self._train_size,
            test_size=self._test_size,
            step_size=self._step_size,
            initial_cash=self._initial_cash,
        )

        fold_scores: list[float] = []
        fold_mc_results: list[dict] = []

        pos = 0
        candles = self._candles

        while True:
            test_slice = candles[
                pos + self._train_size : pos + self._train_size + self._test_size
            ]

            if len(test_slice) < self._test_size:
                break

            # Run backtester on test slice
            bt = Backtester(self._initial_cash)
            test_result = bt.run(
                [copy.copy(c) for c in test_slice],
                strategy=self._strategy_class(),
            )

            test_returns_series = test_result["returns_series"]

            # Prevent degenerate return series (avoids Sharpe division by zero)
            if len(test_returns_series) < 2:
                raise ValueError("Test window must produce at least 2 return points")

            mc_engine = MonteCarloEngine(
                initial_cash=self._initial_cash,
                seed=self._seed,
            )

            mc_result = mc_engine.analyze(
                returns_series=test_returns_series,
                mode="returns",
                simulations=self._simulations,
            )

            r_i = (
                mc_result["mean_sharpe"]
                - mc_result["sharpe_variance"]
                - mc_result["probability_of_loss"]
            )

            fold_scores.append(r_i)
            fold_mc_results.append(mc_result)

            pos += self._step_size

        # Critical fix: prevent division by zero
        if not fold_scores:
            raise ValueError("No valid folds produced")

        robustness_score = sum(fold_scores) / len(fold_scores)

        return {
            "fold_scores": fold_scores,
            "fold_mc_results": fold_mc_results,
            "robustness_score": robustness_score,
        }