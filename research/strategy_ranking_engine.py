"""
research.strategy_ranking_engine
=================================

Composite strategy ranking engine.

Runs each supplied strategy class through the full research pipeline:

    * Backtester          — return_pct, sharpe_ratio, calmar_ratio, max_drawdown_pct
    * StabilityEngine     — stability_score
    * WalkForwardEngine   — mean_test_sharpe, performance_decay
    * MonteCarloEngine    — mean_sharpe, sharpe_variance, probability_of_loss
    * RobustnessEngine    — robustness_score

Then computes a composite score and returns results sorted descending by that
score (stable sort preserves insertion order on ties).

Composite score formula
-----------------------
    score =
        1.0 * sharpe_ratio
      + 0.8 * calmar_ratio
      + 1.2 * stability_score
      + 1.5 * robustness_score
      - 1.0 * abs(max_drawdown_pct)
      - 1.0 * abs(performance_decay)
"""

import copy

from app.backtester.engine import Backtester
from research.stability_engine import analyze_strategy as stability_analyze
from research.walk_forward_engine import walk_forward_analysis
from research.monte_carlo_engine import MonteCarloEngine
from research.robustness_engine import RobustnessEngine


class StrategyRankingEngine:
    """
    Rank multiple strategy classes by composite score.

    Parameters
    ----------
    strategies : list[type]
        Non-empty list of strategy classes (not instances).  Each class must
        accept a no-argument constructor and expose
        ``generate(candles) -> list[str]``.
    candles : list[dict]
        Full chronological OHLCV history.  Not mutated.
    initial_cash : float, optional
        Starting cash for every ``Backtester`` instance.  Default 1000.
    train_size : int, optional
        Training-window size forwarded to walk-forward / robustness engines.
        Default 10.
    test_size : int, optional
        Test-window size forwarded to walk-forward / robustness engines.
        Default 5.
    step_size : int, optional
        Sliding-window step forwarded to walk-forward / robustness engines.
        Default 5.
    simulations : int, optional
        Number of Monte Carlo paths per fold in ``RobustnessEngine`` and in
        the standalone ``MonteCarloEngine`` call.  Default 50.
    seed : int or None, optional
        Seed for all stochastic engines.  Ensures deterministic results when
        fixed.  Default ``None``.
    """

    def __init__(
        self,
        strategies: list,
        candles: list,
        initial_cash: float = 1000,
        train_size: int = 10,
        test_size: int = 5,
        step_size: int = 5,
        simulations: int = 50,
        seed=None,
    ) -> None:
        if not strategies:
            raise ValueError("strategies must not be empty")

        self._strategies   = strategies
        self._candles      = candles
        self._initial_cash = initial_cash
        self._train_size   = train_size
        self._test_size    = test_size
        self._step_size    = step_size
        self._simulations  = simulations
        self._seed         = seed

    # ------------------------------------------------------------------
    def run(self) -> list:
        """
        Execute the full ranking pipeline for every strategy.

        Returns
        -------
        list[dict]
            Results sorted descending by ``composite_score``.  Each entry:

            {
                "strategy_name"  : str,
                "backtest"       : dict,   # Backtester.run output subset
                "stability"      : dict,   # stability_analyze output subset
                "walk_forward"   : dict,   # walk_forward_analysis output subset
                "monte_carlo"    : dict,   # MonteCarloEngine.analyze output subset
                "robustness"     : float,  # robustness_score
                "composite_score": float,
                "rank"           : int,    # 1-based, assigned after sorting
            }

        Raises
        ------
        ValueError
            Propagated from ``MonteCarloEngine`` when ``simulations < 1``.
        """
        results = []

        for strategy_class in self._strategies:
            # ---------------------------------------------------------- #
            # 1. Backtest on the full candle set                          #
            # ---------------------------------------------------------- #
            bt = Backtester(self._initial_cash)
            bt_result = bt.run(
                [copy.copy(c) for c in self._candles],
                strategy=strategy_class(),
            )

            backtest = {
                "return_pct":      bt_result["return_pct"],
                "sharpe_ratio":    bt_result["sharpe_ratio"],
                "calmar_ratio":    bt_result["calmar_ratio"],
                "max_drawdown_pct": bt_result["max_drawdown_pct"],
            }

            # ---------------------------------------------------------- #
            # 2. Stability analysis                                        #
            # ---------------------------------------------------------- #
            # Use train_size as the window_size for regime splitting so
            # that the same candle budget is respected across all engines.
            stab_result = stability_analyze(
                strategy_class,
                [copy.copy(c) for c in self._candles],
                window_size=self._train_size,
                initial_cash=self._initial_cash,
            )

            stability = {
                "stability_score": stab_result["stability_score"],
            }

            # ---------------------------------------------------------- #
            # 3. Walk-forward analysis                                     #
            # ---------------------------------------------------------- #
            wf_result = walk_forward_analysis(
                strategy_class,
                [copy.copy(c) for c in self._candles],
                train_size=self._train_size,
                test_size=self._test_size,
                step_size=self._step_size,
                initial_cash=self._initial_cash,
            )

            walk_forward = {
                "mean_test_sharpe":  wf_result["mean_test_sharpe"],
                "performance_decay": wf_result["performance_decay"],
            }

            # ---------------------------------------------------------- #
            # 4. Monte Carlo analysis on the full backtest returns series  #
            # ---------------------------------------------------------- #
            mc_engine = MonteCarloEngine(
                initial_cash=self._initial_cash,
                seed=self._seed,
            )
            mc_result = mc_engine.analyze(
                returns_series=bt_result["returns_series"],
                mode="returns",
                simulations=self._simulations,
            )

            monte_carlo = {
                "mean_sharpe":         mc_result["mean_sharpe"],
                "sharpe_variance":     mc_result["sharpe_variance"],
                "probability_of_loss": mc_result["probability_of_loss"],
            }

            # ---------------------------------------------------------- #
            # 5. Robustness analysis                                       #
            # ---------------------------------------------------------- #
            rob_engine = RobustnessEngine(
                strategy_class=strategy_class,
                candles=[copy.copy(c) for c in self._candles],
                train_size=self._train_size,
                test_size=self._test_size,
                step_size=self._step_size,
                simulations=self._simulations,
                seed=self._seed,
                initial_cash=self._initial_cash,
            )
            rob_result = rob_engine.run()
            robustness_score = rob_result["robustness_score"]

            # ---------------------------------------------------------- #
            # 6. Composite score                                           #
            # ---------------------------------------------------------- #
            sharpe_ratio     = backtest["sharpe_ratio"]
            calmar_ratio     = backtest["calmar_ratio"]
            max_drawdown_pct = backtest["max_drawdown_pct"]
            stab_score       = stability["stability_score"]
            perf_decay       = walk_forward["performance_decay"]

            composite_score = (
                1.0 * sharpe_ratio
                + 0.8 * calmar_ratio
                + 1.2 * stab_score
                + 1.5 * robustness_score
                - 1.0 * abs(max_drawdown_pct)
                - 1.0 * abs(perf_decay)
            )

            results.append({
                "strategy_name":   strategy_class.__name__,
                "backtest":        backtest,
                "stability":       stability,
                "walk_forward":    walk_forward,
                "monte_carlo":     monte_carlo,
                "robustness":      robustness_score,
                "composite_score": composite_score,
                "rank":            None,  # assigned after sorting
            })

        # ------------------------------------------------------------------ #
        # Sort descending by composite_score (stable — preserves insertion    #
        # order for ties).                                                     #
        # ------------------------------------------------------------------ #
        results.sort(key=lambda r: r["composite_score"], reverse=True)

        # Assign 1-based ranks
        for i, entry in enumerate(results):
            entry["rank"] = i + 1

        return results
