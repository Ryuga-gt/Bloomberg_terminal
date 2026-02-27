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

The three Monte Carlo statistics come directly from
``MonteCarloEngine.analyze(mode="returns")`` applied to the **test-slice**
returns series of every fold.
"""

import copy

from app.backtester.engine import Backtester
from research.walk_forward_engine import walk_forward_analysis  # noqa: F401  (validates fold params)
from research.monte_carlo_engine import MonteCarloEngine


class RobustnessEngine:
    """
    Walk-forward Monte Carlo robustness engine.

    Parameters
    ----------
    strategy_class :
        A class (not an instance) whose constructor takes no arguments and
        whose instances expose ``generate(candles) -> list[str]``.
    candles : list[dict]
        Full chronological OHLCV history.  Not mutated.
    train_size : int
        Number of candles per training slice (must be >= 2).
    test_size : int
        Number of candles per test slice (must be >= 2).
    step_size : int
        Number of candles to advance the window origin per fold (must be >= 1).
    simulations : int, optional
        Number of Monte Carlo paths per fold.  Default 100.  Must be >= 1.
    seed : int or None, optional
        Seed for the internal ``MonteCarloEngine`` RNG.  Ensures deterministic
        results when fixed.  Default ``None``.
    initial_cash : float, optional
        Starting cash for each ``Backtester`` instance.  Default 1000.
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
        self._candles        = candles
        self._train_size     = train_size
        self._test_size      = test_size
        self._step_size      = step_size
        self._simulations    = simulations
        self._seed           = seed
        self._initial_cash   = initial_cash

    # ------------------------------------------------------------------
    def run(self) -> dict:
        """
        Execute the robustness analysis.

        Returns
        -------
        dict with keys:
            fold_scores      : list[float]  — R_i per fold
            fold_mc_results  : list[dict]   — raw MonteCarloEngine output per fold
            robustness_score : float        — arithmetic mean of fold_scores

        Raises
        ------
        ValueError
            Propagated from walk-forward validation when parameters are invalid
            (``train_size < 2``, ``test_size < 2``, ``step_size < 1``, or
            dataset too small for one complete fold).
        ValueError
            When ``simulations < 1`` (propagated from MonteCarloEngine).
        """
        # ---------------------------------------------------------------- #
        # Step 1 — validate fold parameters by delegating to               #
        # walk_forward_analysis.  We call it but discard the result;       #
        # its only purpose here is centralised parameter validation so     #
        # we don't duplicate the guard logic.                              #
        # ---------------------------------------------------------------- #
        walk_forward_analysis(
            self._strategy_class,
            self._candles,
            train_size=self._train_size,
            test_size=self._test_size,
            step_size=self._step_size,
            initial_cash=self._initial_cash,
        )

        # ---------------------------------------------------------------- #
        # Step 2 — slide folds and compute per-fold robustness scores      #
        # ---------------------------------------------------------------- #
        fold_scores:     list[float] = []
        fold_mc_results: list[dict]  = []

        pos = 0
        candles = self._candles

        while True:
            test_slice = candles[
                pos + self._train_size: pos + self._train_size + self._test_size
            ]

            # Stop when the test window is incomplete (matches walk_forward_analysis)
            if len(test_slice) < self._test_size:
                break

            # ------------------------------------------------------------ #
            # Run backtester on test slice to obtain per-period returns     #
            # ------------------------------------------------------------ #
            bt = Backtester(self._initial_cash)
            test_result = bt.run(
                [copy.copy(c) for c in test_slice],
                strategy=self._strategy_class(),
            )
            test_returns_series = test_result["returns_series"]

            # ------------------------------------------------------------ #
            # Monte Carlo analysis over the test returns                    #
            # ------------------------------------------------------------ #
            mc_engine = MonteCarloEngine(
                initial_cash=self._initial_cash,
                seed=self._seed,
            )
            mc_result = mc_engine.analyze(
                returns_series=test_returns_series,
                mode="returns",
                simulations=self._simulations,
            )

            # ------------------------------------------------------------ #
            # R_i = mc_mean_sharpe - mc_sharpe_variance - mc_prob_of_loss  #
            # ------------------------------------------------------------ #
            r_i = (
                mc_result["mean_sharpe"]
                - mc_result["sharpe_variance"]
                - mc_result["probability_of_loss"]
            )

            fold_scores.append(r_i)
            fold_mc_results.append(mc_result)

            pos += self._step_size

        # ---------------------------------------------------------------- #
        # Step 3 — global robustness score                                 #
        # ---------------------------------------------------------------- #
        robustness_score = sum(fold_scores) / len(fold_scores)

        return {
            "fold_scores":      fold_scores,
            "fold_mc_results":  fold_mc_results,
            "robustness_score": robustness_score,
        }
