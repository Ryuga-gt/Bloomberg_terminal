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
5. Runs the next segment (candles from current step to next rebalance)
   using a fresh ``PortfolioEngine`` seeded with the current equity.

The equity curve is built segment-by-segment: each segment starts from
the equity at the end of the previous segment.

Design constraints
------------------
* No global state.
* No mutation of input candles or strategies list.
* Deterministic.
* No async, no threading, no logging.
"""

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

        n = len(candles)
        active_strategies = list(self._strategies)
        disabled_names: list = []
        rebalance_steps: list = []
        equity_curve: list = []

        # Current capital and weights
        current_capital = self._initial_capital
        current_weights = {
            cls.__name__: 1.0 / len(active_strategies)
            for cls in active_strategies
        }

        # Find all rebalance points
        rebalance_points = [i for i in range(n)
                            if self._rebalance_policy.should_rebalance(i)]

        # Build segment boundaries: [start, end) pairs
        # Each segment runs from one rebalance point to the next
        if not rebalance_points:
            rebalance_points = [0]

        # Ensure we start at 0
        if rebalance_points[0] != 0:
            rebalance_points = [0] + rebalance_points

        # Add sentinel end
        boundaries = list(rebalance_points) + [n]

        for seg_idx in range(len(boundaries) - 1):
            seg_start = boundaries[seg_idx]
            seg_end   = boundaries[seg_idx + 1]
            seg_candles = candles[seg_start:seg_end]

            if not seg_candles:
                continue

            # --- Rebalance at seg_start ---
            rebalance_steps.append(seg_start)

            # Rank on candles seen so far (up to and including seg_start)
            window = candles[: seg_start + 1]
            try:
                ranking_results = self._ranking_engine.run(window)
            except Exception:
                ranking_results = None

            if ranking_results is not None:
                # Decay detection
                if self._decay_detector is not None:
                    for result in ranking_results:
                        name = result["strategy_name"]
                        if name not in disabled_names:
                            if self._decay_detector.is_decayed(result):
                                disabled_names.append(name)

                # Determine active strategies
                new_active = [
                    cls for cls in self._strategies
                    if cls.__name__ not in disabled_names
                ]
                if not new_active:
                    new_active = list(self._strategies)
                active_strategies = new_active

                # Compute weights
                active_names = {cls.__name__ for cls in active_strategies}
                active_results = [
                    r for r in ranking_results
                    if r["strategy_name"] in active_names
                ]
                if active_results:
                    current_weights = self._allocator.compute_weights(active_results)
                else:
                    n_act = len(active_strategies)
                    current_weights = {
                        cls.__name__: 1.0 / n_act
                        for cls in active_strategies
                    }

            # --- Run this segment with current capital ---
            seg_equity_curve = self._run_segment(
                strategies=active_strategies,
                weights=current_weights,
                capital=current_capital,
                candles=seg_candles,
            )

            equity_curve.extend(seg_equity_curve)

            # Update capital for next segment
            if seg_equity_curve:
                current_capital = seg_equity_curve[-1]

        final_equity = equity_curve[-1] if equity_curve else self._initial_capital

        return {
            "final_portfolio_equity": final_equity,
            "rebalance_steps":        rebalance_steps,
            "disabled_strategies":    list(disabled_names),
            "equity_curve":           equity_curve,
        }

    # ------------------------------------------------------------------

    def _run_segment(
        self,
        strategies: list,
        weights: dict,
        capital: float,
        candles: list,
    ) -> list:
        """
        Run a single segment of candles and return the equity curve.

        Each strategy gets capital proportional to its weight.
        Returns a list of equity values, one per candle.
        """
        if not candles or capital <= 0:
            return [capital] * len(candles)

        # Build per-strategy engines with weighted capital
        engines = []
        for cls in strategies:
            name = cls.__name__
            w = weights.get(name, 0.0)
            strat_capital = capital * w
            if strat_capital > 0:
                engine = PortfolioEngine(
                    strategies=[cls],
                    initial_capital=strat_capital,
                    allocation="equal",
                )
                engines.append(engine)

        if not engines:
            # Fallback: equal allocation
            n = len(strategies)
            for cls in strategies:
                engine = PortfolioEngine(
                    strategies=[cls],
                    initial_capital=capital / n,
                    allocation="equal",
                )
                engines.append(engine)

        # Run all engines on the segment candles
        results = [engine.run(candles) for engine in engines]

        # Aggregate equity curve step by step
        seg_len = len(candles)
        seg_equity = []
        for i in range(seg_len):
            step_equity = sum(r["portfolio_equity_curve"][i] for r in results)
            seg_equity.append(step_equity)

        return seg_equity
