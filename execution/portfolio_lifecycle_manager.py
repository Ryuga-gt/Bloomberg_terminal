"""
execution.portfolio_lifecycle_manager
======================================

Orchestrates periodic rebalancing, performance decay detection, and
auto-disabling of underperforming strategies over a candle sequence.

Integration flow
----------------
    RankingEngine → CapitalAllocator → PortfolioEngine
         ↑                                    ↑
    RebalancePolicy + DecayDetector ──────────┘

At each rebalance step the manager:

1. Runs ``ranking_engine.run(candles[:step+1])`` on the candles seen so far.
2. Optionally filters out strategies where ``decay_detector.is_decayed()``
   is ``True``.  Filtered strategies are added to ``disabled_strategies``
   and remain disabled for the rest of the simulation.
3. Falls back to the original strategy list if all active strategies are
   disabled.
4. Computes new weights via ``allocator.compute_weights()``.
5. Instantiates a fresh ``PortfolioEngine`` with the active strategies and
   weighted capital, then re-runs it from candle 0 to the current step to
   obtain the equity at that point.

The equity curve is built step-by-step: at each candle the current
portfolio's equity at that step is recorded.

Design constraints
------------------
* No global state.
* No mutation of input candles or strategies list.
* Deterministic.
* No async, no threading, no logging.
"""

import copy

from execution.portfolio_engine import PortfolioEngine


class PortfolioLifecycleManager:
    """
    Periodic rebalancing lifecycle manager.

    Parameters
    ----------
    strategies : list[type]
        Non-empty list of strategy classes.
    initial_capital : float
        Total capital.  Must be > 0.
    ranking_engine : object
        Must expose ``run(candles) -> list[dict]``.
    allocator : object
        Must expose ``compute_weights(ranking_results) -> dict``.
    rebalance_policy : RebalancePolicy
        Determines when rebalancing occurs.
    decay_detector : PerformanceDecayDetector or None, optional
        If provided, strategies that fail the decay check are disabled.
        Default ``None``.

    Raises
    ------
    ValueError
        If ``strategies`` is empty or ``initial_capital`` <= 0.
    """

    def __init__(
        self,
        strategies: list,
        initial_capital: float,
        ranking_engine,
        allocator,
        rebalance_policy,
        decay_detector=None,
    ) -> None:
        if not strategies:
            raise ValueError("strategies must not be empty")
        if initial_capital <= 0:
            raise ValueError(
                f"initial_capital must be > 0, got {initial_capital!r}"
            )

        self._strategies = list(strategies)          # defensive copy
        self._initial_capital = float(initial_capital)
        self._ranking_engine = ranking_engine
        self._allocator = allocator
        self._rebalance_policy = rebalance_policy
        self._decay_detector = decay_detector

    # ------------------------------------------------------------------

    def run(self, candles: list) -> dict:
        """
        Simulate the portfolio over *candles* with periodic rebalancing.

        Parameters
        ----------
        candles : list[dict]
            Chronological OHLCV candles.  Not mutated.

        Returns
        -------
        dict with keys:
            final_portfolio_equity : float
            rebalance_steps        : list[int]
            disabled_strategies    : list[str]
            equity_curve           : list[float]
        """
        if not candles:
            return {
                "final_portfolio_equity": self._initial_capital,
                "rebalance_steps":        [],
                "disabled_strategies":    [],
                "equity_curve":           [],
            }

        # Track which strategy classes are still active (by class object)
        active_strategies = list(self._strategies)
        disabled_names: list = []
        rebalance_steps: list = []

        # Current portfolio engine and its equity curve
        # We start with equal allocation over all strategies.
        current_engine = PortfolioEngine(
            strategies=active_strategies,
            initial_capital=self._initial_capital,
            allocation="equal",
        )

        equity_curve: list = []

        for step, candle in enumerate(candles):
            if self._rebalance_policy.should_rebalance(step):
                rebalance_steps.append(step)

                # --- 1. Rank on candles seen so far (inclusive) ---
                window = candles[: step + 1]
                try:
                    ranking_results = self._ranking_engine.run(window)
                except Exception:
                    # If ranking fails (e.g. too few candles), keep current
                    ranking_results = None

                if ranking_results is not None:
                    # --- 2. Decay detection ---
                    if self._decay_detector is not None:
                        for result in ranking_results:
                            name = result["strategy_name"]
                            # Only check strategies still active
                            if name not in disabled_names:
                                if self._decay_detector.is_decayed(result):
                                    disabled_names.append(name)

                    # --- 3. Determine active strategy classes ---
                    new_active = [
                        cls for cls in self._strategies
                        if cls.__name__ not in disabled_names
                    ]
                    if not new_active:
                        # Fallback: restore all original strategies
                        new_active = list(self._strategies)

                    active_strategies = new_active

                    # --- 4. Compute weights ---
                    # Filter ranking_results to active strategies only
                    active_names = {cls.__name__ for cls in active_strategies}
                    active_results = [
                        r for r in ranking_results
                        if r["strategy_name"] in active_names
                    ]

                    if active_results:
                        weights = self._allocator.compute_weights(active_results)
                    else:
                        # Fallback equal
                        n = len(active_strategies)
                        weights = {cls.__name__: 1.0 / n
                                   for cls in active_strategies}

                    # --- 5. Re-instantiate PortfolioEngine ---
                    # Distribute capital according to weights
                    # PortfolioEngine only supports "equal" allocation
                    # internally, so we pass weighted capital per strategy
                    # by creating individual engines and summing.
                    # However, PortfolioEngine splits equally by design.
                    # We implement weighted allocation by running separate
                    # PortfolioEngine instances per strategy with their
                    # respective capital share, then aggregate.
                    current_engine = _WeightedPortfolioEngine(
                        strategies=active_strategies,
                        weights=weights,
                        initial_capital=self._initial_capital,
                    )

            # --- Feed current candle to the current engine ---
            current_engine.step(candle)
            equity_curve.append(current_engine.current_equity())

        final_equity = equity_curve[-1] if equity_curve else self._initial_capital

        return {
            "final_portfolio_equity": final_equity,
            "rebalance_steps":        rebalance_steps,
            "disabled_strategies":    list(disabled_names),
            "equity_curve":           equity_curve,
        }


# ---------------------------------------------------------------------------
# Internal helper: weighted portfolio engine
# ---------------------------------------------------------------------------

class _WeightedPortfolioEngine:
    """
    Internal helper that runs one :class:`PortfolioEngine` per strategy
    with capital proportional to the given weights.

    This allows weighted (non-equal) capital allocation while reusing the
    existing :class:`PortfolioEngine` infrastructure.
    """

    def __init__(
        self,
        strategies: list,
        weights: dict,
        initial_capital: float,
    ) -> None:
        self._engines = []
        for cls in strategies:
            name = cls.__name__
            w = weights.get(name, 0.0)
            capital = initial_capital * w
            if capital > 0:
                engine = PortfolioEngine(
                    strategies=[cls],
                    initial_capital=capital,
                    allocation="equal",
                )
                self._engines.append(engine)

        # Fallback: if all weights are 0, use equal allocation
        if not self._engines:
            n = len(strategies)
            for cls in strategies:
                engine = PortfolioEngine(
                    strategies=[cls],
                    initial_capital=initial_capital / n,
                    allocation="equal",
                )
                self._engines.append(engine)

        # History of candles fed so far (for re-run after rebalance)
        self._candle_history: list = []

    def step(self, candle: dict) -> None:
        """Feed *candle* to all sub-engines."""
        self._candle_history.append(candle)
        for engine in self._engines:
            # Each engine maintains its own internal state; we feed
            # candles one at a time by calling run() on the accumulated
            # history and reading the last equity curve value.
            # Since PortfolioEngine.run() is idempotent (resets curve),
            # we call it with the full history each time.
            pass  # handled in current_equity via full re-run

    def current_equity(self) -> float:
        """Return the current total portfolio equity."""
        if not self._candle_history:
            return sum(
                e._initial_capital for e in self._engines
            )
        total = 0.0
        for engine in self._engines:
            result = engine.run(self._candle_history)
            total += result["portfolio_equity"]
        return total
