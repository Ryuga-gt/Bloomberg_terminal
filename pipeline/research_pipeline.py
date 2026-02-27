"""
pipeline.research_pipeline
===========================

Automated end-to-end research pipeline.

Flow
----
1. Fetch historical candles via a :class:`MarketDataProvider`.
2. Run the :class:`EvolutionEngine` to find the best strategy genome.
3. Convert the best genome to a strategy class.
4. Rank strategies using :class:`StrategyRankingEngine`.
5. Allocate capital using :class:`CapitalAllocator`.
6. Run the :class:`PortfolioLifecycleManager`.
7. Compute full analytics via :class:`PortfolioAnalytics`.
8. Return a structured report.

Single entrypoint::

    result = run_full_pipeline(
        symbol="AAPL",
        start="2020-01-01",
        end="2023-01-01",
        provider=YahooProvider(),
    )

The pipeline is deterministic when a seed is provided.
"""

import copy

from data.data_provider import MarketDataProvider
from ai.evolution_engine import EvolutionEngine
from ai.strategy_genome import genome_to_strategy_class
from research.strategy_ranking_engine import StrategyRankingEngine
from execution.capital_allocator import CapitalAllocator
from execution.portfolio_engine import PortfolioEngine
from execution.rebalance_policy import RebalancePolicy
from execution.decay_detector import PerformanceDecayDetector
from execution.portfolio_lifecycle_manager import PortfolioLifecycleManager
from analytics.portfolio_analytics import PortfolioAnalytics


def run_full_pipeline(
    symbol: str,
    start: str,
    end: str,
    provider: MarketDataProvider,
    initial_capital: float = 10_000,
    population_size: int = 10,
    generations: int = 5,
    rebalance_interval: int = 20,
    decay_threshold: float = -1.0,
    allocator_mode: str = "sharpe",
    seed: int = 42,
) -> dict:
    """
    Run the full automated research pipeline.

    Parameters
    ----------
    symbol : str
        Ticker symbol, e.g. ``"AAPL"``.
    start : str
        Start date ``"YYYY-MM-DD"``.
    end : str
        End date ``"YYYY-MM-DD"``.
    provider : MarketDataProvider
        Data provider instance.
    initial_capital : float, optional
        Total portfolio capital.  Default 10,000.
    population_size : int, optional
        Evolution population size.  Default 10.
    generations : int, optional
        Evolution generations.  Default 5.
    rebalance_interval : int, optional
        Candles between rebalances.  Default 20.
    decay_threshold : float, optional
        Sharpe threshold below which a strategy is disabled.  Default -1.0.
    allocator_mode : str, optional
        Capital allocation mode.  Default ``"sharpe"``.
    seed : int or None, optional
        Random seed.  Default 42.

    Returns
    -------
    dict with keys:
        symbol              : str
        candle_count        : int
        best_genome         : dict
        best_fitness        : float
        ranking_results     : list[dict]
        portfolio_result    : dict
        analytics_report    : dict
    """
    # 1. Fetch data
    candles = provider.get_historical(symbol, start, end, interval="1d")
    if not candles:
        return {
            "symbol":           symbol,
            "candle_count":     0,
            "best_genome":      None,
            "best_fitness":     None,
            "ranking_results":  [],
            "portfolio_result": {},
            "analytics_report": {},
            "error":            "No candles returned by provider",
        }

    # 2. Evolve strategies
    evolution = EvolutionEngine(
        candles=candles,
        population_size=population_size,
        generations=generations,
        seed=seed,
        fitness_mode="fast",
        initial_cash=initial_capital / max(population_size, 1),
    )
    evo_result = evolution.run()
    best_genome   = evo_result["best_genome"]
    best_fitness  = evo_result["best_fitness"]

    # 3. Build strategy classes from top genomes (deduplicated by type)
    history = evo_result["history"]
    # Sort by fitness descending, take top unique genomes
    seen_types = set()
    top_strategies = []
    for entry in sorted(history, key=lambda x: x["fitness"], reverse=True):
        g = entry["genome"]
        key = (g["type"], str(sorted(g.items())))
        if key not in seen_types:
            seen_types.add(key)
            top_strategies.append(genome_to_strategy_class(g))
        if len(top_strategies) >= 3:
            break

    if not top_strategies:
        top_strategies = [genome_to_strategy_class(best_genome)]

    # 4. Rank strategies
    n = len(candles)
    # Use smaller windows to ensure at least 2 walk-forward folds
    train_size = max(10, min(n // 5, 50))
    test_size  = max(5,  min(n // 10, 25))
    step_size  = max(5,  min(n // 10, 25))

    # Ensure train+test fits within candle count
    while train_size + test_size > n and train_size > 10:
        train_size = max(10, train_size - 5)
        test_size  = max(5,  test_size  - 2)

    ranking_results = []
    try:
        ranking_engine = StrategyRankingEngine(
            strategies=top_strategies,
            candles=[copy.copy(c) for c in candles],
            initial_cash=initial_capital / len(top_strategies),
            train_size=train_size,
            test_size=test_size,
            step_size=step_size,
            simulations=10,
            seed=seed,
        )
        ranking_results = ranking_engine.run()
    except Exception:
        # Fallback: build minimal ranking results from backtester only
        from app.backtester.engine import Backtester
        for i, cls in enumerate(top_strategies):
            bt = Backtester(initial_capital / len(top_strategies))
            try:
                bt_result = bt.run(
                    [copy.copy(c) for c in candles],
                    strategy=cls(),
                )
                ranking_results.append({
                    "strategy_name":   cls.__name__,
                    "backtest":        {
                        "return_pct":       bt_result.get("return_pct", 0.0),
                        "sharpe_ratio":     bt_result.get("sharpe_ratio", 0.0),
                        "calmar_ratio":     bt_result.get("calmar_ratio", 0.0),
                        "max_drawdown_pct": bt_result.get("max_drawdown_pct", 0.0),
                    },
                    "stability":       {"stability_score": 0.0},
                    "walk_forward":    {"mean_test_sharpe": 0.0, "performance_decay": 0.0},
                    "monte_carlo":     {"mean_sharpe": 0.0, "sharpe_variance": 0.0,
                                       "probability_of_loss": 0.5},
                    "robustness":      0.0,
                    "composite_score": bt_result.get("sharpe_ratio", 0.0),
                    "rank":            i + 1,
                })
            except Exception:
                ranking_results.append({
                    "strategy_name":   cls.__name__,
                    "backtest":        {"return_pct": 0.0, "sharpe_ratio": 0.0,
                                       "calmar_ratio": 0.0, "max_drawdown_pct": 0.0},
                    "stability":       {"stability_score": 0.0},
                    "walk_forward":    {"mean_test_sharpe": 0.0, "performance_decay": 0.0},
                    "monte_carlo":     {"mean_sharpe": 0.0, "sharpe_variance": 0.0,
                                       "probability_of_loss": 0.5},
                    "robustness":      0.0,
                    "composite_score": 0.0,
                    "rank":            i + 1,
                })
        # Sort by composite_score descending
        ranking_results.sort(key=lambda r: r["composite_score"], reverse=True)
        for i, r in enumerate(ranking_results):
            r["rank"] = i + 1

    # 5. Allocate capital
    allocator = CapitalAllocator(mode=allocator_mode)

    # 6. Run lifecycle manager
    rebalance_policy = RebalancePolicy(interval=rebalance_interval)
    decay_detector   = PerformanceDecayDetector(
        threshold=decay_threshold, metric="sharpe"
    )

    mock_ranking_engine = _StaticRankingEngine(ranking_results, top_strategies)

    lifecycle = PortfolioLifecycleManager(
        strategies=top_strategies,
        initial_capital=initial_capital,
        ranking_engine=mock_ranking_engine,
        allocator=allocator,
        rebalance_policy=rebalance_policy,
        decay_detector=decay_detector,
    )
    portfolio_result = lifecycle.run(candles)

    # 7. Analytics
    equity_curve = portfolio_result.get("equity_curve", [])
    analytics_report = {}
    if len(equity_curve) >= 2:
        # Guard: PortfolioAnalytics requires all values > 0
        safe_curve = [max(v, 0.01) for v in equity_curve]
        try:
            pa = PortfolioAnalytics(safe_curve)
            analytics_report = pa.full_report()
        except Exception:
            analytics_report = {}

    return {
        "symbol":           symbol,
        "candle_count":     len(candles),
        "best_genome":      best_genome,
        "best_fitness":     best_fitness,
        "ranking_results":  ranking_results,
        "portfolio_result": portfolio_result,
        "analytics_report": analytics_report,
    }


# ---------------------------------------------------------------------------
# Internal helper: static ranking engine wrapper
# ---------------------------------------------------------------------------

class _StaticRankingEngine:
    """Returns pre-computed ranking results regardless of candles passed."""

    def __init__(self, results: list, strategies: list) -> None:
        self._results = results
        self._strategies = strategies

    def run(self, candles: list) -> list:
        if self._results:
            return self._results
        # Fallback: return minimal results
        return [
            {
                "strategy_name": cls.__name__,
                "backtest": {"sharpe_ratio": 0.0, "calmar_ratio": 0.0,
                             "return_pct": 0.0, "max_drawdown_pct": 0.0},
                "robustness": 0.0,
                "composite_score": 0.0,
                "rank": i + 1,
            }
            for i, cls in enumerate(self._strategies)
        ]
