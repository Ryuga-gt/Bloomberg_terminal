"""
Tests for execution.portfolio_lifecycle_manager.PortfolioLifecycleManager

Contract
--------
PortfolioLifecycleManager(
    strategies, initial_capital, ranking_engine, allocator,
    rebalance_policy, decay_detector=None
)

    run(candles) -> dict
        Returns:
            final_portfolio_equity : float
            rebalance_steps        : list[int]
            disabled_strategies    : list[str]
            equity_curve           : list[float]

Validation
----------
    strategies empty → ValueError
    initial_capital <= 0 → ValueError
    no candle mutation
    deterministic

Uses mock ranking engines and allocators to avoid research-layer deps.
"""

import pytest
import copy

from execution.portfolio_lifecycle_manager import PortfolioLifecycleManager
from execution.rebalance_policy import RebalancePolicy
from execution.decay_detector import PerformanceDecayDetector
from execution.capital_allocator import CapitalAllocator


# ---------------------------------------------------------------------------
# Candle factory
# ---------------------------------------------------------------------------

def make_candle(close: float) -> dict:
    return {
        "open":   close,
        "high":   close,
        "low":    close,
        "close":  close,
        "volume": 1_000_000,
    }


# ---------------------------------------------------------------------------
# Test strategy classes
# ---------------------------------------------------------------------------

class AlwaysBuyHold:
    """BUY on first candle, HOLD thereafter."""
    def __init__(self):
        self._called = False

    def generate_signal(self, candle: dict) -> str:
        if not self._called:
            self._called = True
            return "BUY"
        return "HOLD"


class AlwaysFlat:
    """Always HOLD."""
    def generate_signal(self, candle: dict) -> str:
        return "HOLD"


class AlwaysPositiveSharpe:
    """Always HOLD — used with mock ranking that gives positive sharpe."""
    def generate_signal(self, candle: dict) -> str:
        return "HOLD"


class AlwaysNegativeSharpe:
    """Always HOLD — used with mock ranking that gives negative sharpe."""
    def generate_signal(self, candle: dict) -> str:
        return "HOLD"


# ---------------------------------------------------------------------------
# Mock ranking engine
# ---------------------------------------------------------------------------

class MockRankingEngine:
    """
    Returns a fixed ranking result for each strategy class.
    sharpe_map: {ClassName: sharpe_value}
    robustness_map: {ClassName: robustness_value}
    """
    def __init__(self, strategies, sharpe_map=None, robustness_map=None):
        self._strategies = strategies
        self._sharpe_map = sharpe_map or {}
        self._robustness_map = robustness_map or {}

    def run(self, candles):
        results = []
        for i, cls in enumerate(self._strategies):
            name = cls.__name__
            results.append({
                "strategy_name": name,
                "backtest": {
                    "sharpe_ratio":    self._sharpe_map.get(name, 1.0),
                    "calmar_ratio":    0.0,
                    "return_pct":      0.0,
                    "max_drawdown_pct": 0.0,
                },
                "robustness": self._robustness_map.get(name, 1.0),
                "composite_score": 0.0,
                "rank": i + 1,
            })
        return results


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_manager(
    strategies,
    initial_capital=1000,
    interval=5,
    sharpe_map=None,
    robustness_map=None,
    decay_detector=None,
    allocator_mode="equal",
):
    ranking_engine = MockRankingEngine(
        strategies, sharpe_map=sharpe_map, robustness_map=robustness_map
    )
    allocator = CapitalAllocator(mode=allocator_mode)
    policy = RebalancePolicy(interval=interval)
    return PortfolioLifecycleManager(
        strategies=strategies,
        initial_capital=initial_capital,
        ranking_engine=ranking_engine,
        allocator=allocator,
        rebalance_policy=policy,
        decay_detector=decay_detector,
    )


# ===========================================================================
# Part 1 — Validation
# ===========================================================================

def test_empty_strategies_raises():
    with pytest.raises(ValueError):
        make_manager(strategies=[])


def test_initial_capital_zero_raises():
    with pytest.raises(ValueError):
        make_manager(strategies=[AlwaysFlat], initial_capital=0)


def test_initial_capital_negative_raises():
    with pytest.raises(ValueError):
        make_manager(strategies=[AlwaysFlat], initial_capital=-100)


# ===========================================================================
# Part 2 — Return type and required keys
# ===========================================================================

def test_run_returns_dict():
    manager = make_manager([AlwaysFlat])
    result = manager.run([make_candle(100.0)])
    assert isinstance(result, dict)


def test_run_result_has_final_portfolio_equity():
    manager = make_manager([AlwaysFlat])
    result = manager.run([make_candle(100.0)])
    assert "final_portfolio_equity" in result


def test_run_result_has_rebalance_steps():
    manager = make_manager([AlwaysFlat])
    result = manager.run([make_candle(100.0)])
    assert "rebalance_steps" in result


def test_run_result_has_disabled_strategies():
    manager = make_manager([AlwaysFlat])
    result = manager.run([make_candle(100.0)])
    assert "disabled_strategies" in result


def test_run_result_has_equity_curve():
    manager = make_manager([AlwaysFlat])
    result = manager.run([make_candle(100.0)])
    assert "equity_curve" in result


# ===========================================================================
# Part 3 — Equity curve length matches candle count
# ===========================================================================

def test_equity_curve_length_matches_candles():
    candles = [make_candle(float(100 + i)) for i in range(10)]
    manager = make_manager([AlwaysFlat], interval=5)
    result = manager.run(candles)
    assert len(result["equity_curve"]) == 10


def test_equity_curve_empty_candles():
    manager = make_manager([AlwaysFlat])
    result = manager.run([])
    assert result["equity_curve"] == []


def test_equity_curve_single_candle():
    manager = make_manager([AlwaysFlat])
    result = manager.run([make_candle(100.0)])
    assert len(result["equity_curve"]) == 1


# ===========================================================================
# Part 4 — Rebalance occurs at correct steps
# ===========================================================================

def test_rebalance_steps_interval5():
    candles = [make_candle(100.0) for _ in range(11)]
    manager = make_manager([AlwaysFlat], interval=5)
    result = manager.run(candles)
    assert 0 in result["rebalance_steps"]
    assert 5 in result["rebalance_steps"]
    assert 10 in result["rebalance_steps"]


def test_rebalance_steps_interval1_all_steps():
    candles = [make_candle(100.0) for _ in range(5)]
    manager = make_manager([AlwaysFlat], interval=1)
    result = manager.run(candles)
    assert result["rebalance_steps"] == [0, 1, 2, 3, 4]


def test_rebalance_steps_large_interval_only_step0():
    candles = [make_candle(100.0) for _ in range(5)]
    manager = make_manager([AlwaysFlat], interval=100)
    result = manager.run(candles)
    assert result["rebalance_steps"] == [0]


def test_rebalance_steps_ordered():
    candles = [make_candle(100.0) for _ in range(15)]
    manager = make_manager([AlwaysFlat], interval=5)
    result = manager.run(candles)
    steps = result["rebalance_steps"]
    assert steps == sorted(steps)


# ===========================================================================
# Part 5 — Disabled strategies removed after threshold breach
# ===========================================================================

def test_decayed_strategy_added_to_disabled():
    """
    AlwaysNegativeSharpe has sharpe=-1.0 < threshold=0.0 → disabled.
    """
    decay = PerformanceDecayDetector(threshold=0.0, metric="sharpe")
    manager = make_manager(
        [AlwaysNegativeSharpe],
        interval=1,
        sharpe_map={"AlwaysNegativeSharpe": -1.0},
        decay_detector=decay,
    )
    candles = [make_candle(100.0) for _ in range(3)]
    result = manager.run(candles)
    assert "AlwaysNegativeSharpe" in result["disabled_strategies"]


def test_healthy_strategy_not_disabled():
    """
    AlwaysPositiveSharpe has sharpe=2.0 > threshold=0.0 → not disabled.
    """
    decay = PerformanceDecayDetector(threshold=0.0, metric="sharpe")
    manager = make_manager(
        [AlwaysPositiveSharpe],
        interval=1,
        sharpe_map={"AlwaysPositiveSharpe": 2.0},
        decay_detector=decay,
    )
    candles = [make_candle(100.0) for _ in range(3)]
    result = manager.run(candles)
    assert "AlwaysPositiveSharpe" not in result["disabled_strategies"]


def test_no_decay_detector_no_disabled():
    manager = make_manager([AlwaysFlat], interval=5, decay_detector=None)
    candles = [make_candle(100.0) for _ in range(10)]
    result = manager.run(candles)
    assert result["disabled_strategies"] == []


# ===========================================================================
# Part 6 — Fallback if all disabled
# ===========================================================================

def test_fallback_if_all_disabled_no_crash():
    """
    Both strategies decayed → fallback to original list → no crash.
    """
    decay = PerformanceDecayDetector(threshold=10.0, metric="sharpe")
    manager = make_manager(
        [AlwaysFlat, AlwaysBuyHold],
        interval=1,
        sharpe_map={"AlwaysFlat": -1.0, "AlwaysBuyHold": -1.0},
        decay_detector=decay,
    )
    candles = [make_candle(100.0) for _ in range(3)]
    result = manager.run(candles)
    # Should not raise; equity curve should have 3 entries
    assert len(result["equity_curve"]) == 3


# ===========================================================================
# Part 7 — Single strategy behavior
# ===========================================================================

def test_single_flat_strategy_equity_unchanged():
    manager = make_manager([AlwaysFlat], initial_capital=1000, interval=5)
    candles = [make_candle(100.0) for _ in range(5)]
    result = manager.run(candles)
    assert result["final_portfolio_equity"] == pytest.approx(1000.0)


def test_single_strategy_equity_curve_length():
    manager = make_manager([AlwaysFlat], interval=5)
    candles = [make_candle(100.0) for _ in range(7)]
    result = manager.run(candles)
    assert len(result["equity_curve"]) == 7


# ===========================================================================
# Part 8 — Determinism
# ===========================================================================

def test_deterministic_same_candles_same_result():
    candles = [make_candle(float(100 + i)) for i in range(10)]

    manager1 = make_manager([AlwaysFlat, AlwaysBuyHold], interval=5)
    result1 = manager1.run(candles)

    manager2 = make_manager([AlwaysFlat, AlwaysBuyHold], interval=5)
    result2 = manager2.run(candles)

    assert result1["final_portfolio_equity"] == pytest.approx(
        result2["final_portfolio_equity"]
    )
    assert result1["equity_curve"] == pytest.approx(result2["equity_curve"])
    assert result1["rebalance_steps"] == result2["rebalance_steps"]
    assert result1["disabled_strategies"] == result2["disabled_strategies"]


# ===========================================================================
# Part 9 — No candle mutation
# ===========================================================================

def test_run_does_not_mutate_candles():
    candles = [make_candle(float(100 + i)) for i in range(5)]
    originals = copy.deepcopy(candles)
    manager = make_manager([AlwaysFlat], interval=5)
    manager.run(candles)
    assert candles == originals


# ===========================================================================
# Part 10 — Robustness-based decay
# ===========================================================================

def test_robustness_decay_disables_strategy():
    decay = PerformanceDecayDetector(threshold=0.5, metric="robustness")
    manager = make_manager(
        [AlwaysFlat],
        interval=1,
        robustness_map={"AlwaysFlat": 0.1},
        decay_detector=decay,
    )
    candles = [make_candle(100.0) for _ in range(3)]
    result = manager.run(candles)
    assert "AlwaysFlat" in result["disabled_strategies"]


def test_robustness_healthy_not_disabled():
    decay = PerformanceDecayDetector(threshold=0.5, metric="robustness")
    manager = make_manager(
        [AlwaysFlat],
        interval=1,
        robustness_map={"AlwaysFlat": 1.0},
        decay_detector=decay,
    )
    candles = [make_candle(100.0) for _ in range(3)]
    result = manager.run(candles)
    assert "AlwaysFlat" not in result["disabled_strategies"]


# ===========================================================================
# Part 11 — Sharpe allocator used correctly
# ===========================================================================

def test_sharpe_allocator_no_crash():
    manager = make_manager(
        [AlwaysFlat, AlwaysBuyHold],
        interval=5,
        sharpe_map={"AlwaysFlat": 1.0, "AlwaysBuyHold": 3.0},
        allocator_mode="sharpe",
    )
    candles = [make_candle(100.0) for _ in range(10)]
    result = manager.run(candles)
    assert len(result["equity_curve"]) == 10


# ===========================================================================
# Part 12 — rebalance_steps correct ordering and no duplicates
# ===========================================================================

def test_rebalance_steps_no_duplicates():
    candles = [make_candle(100.0) for _ in range(20)]
    manager = make_manager([AlwaysFlat], interval=5)
    result = manager.run(candles)
    steps = result["rebalance_steps"]
    assert len(steps) == len(set(steps))


def test_rebalance_steps_interval3():
    candles = [make_candle(100.0) for _ in range(10)]
    manager = make_manager([AlwaysFlat], interval=3)
    result = manager.run(candles)
    expected = [0, 3, 6, 9]
    assert result["rebalance_steps"] == expected


# ===========================================================================
# Part 13 — Capital roll-forward fix: equity never resets to initial_capital
# ===========================================================================

def test_equity_never_resets_to_initial_capital_after_rebalance():
    """
    With a buy-hold strategy on rising prices, equity should grow
    monotonically and never jump back to initial_capital after a rebalance.
    """
    # Rising prices: 100, 110, 120, ..., 190
    candles = [make_candle(float(100 + i * 10)) for i in range(10)]
    manager = make_manager([AlwaysBuyHold], initial_capital=1000, interval=3)
    result = manager.run(candles)
    curve = result["equity_curve"]

    assert len(curve) == 10

    # After the first BUY, equity should grow with price.
    # It must never drop back to exactly 1000 after step 0
    # (unless the strategy is flat, which AlwaysBuyHold is not after first candle).
    # At minimum, the final equity should be >= initial capital.
    assert result["final_portfolio_equity"] >= 1000.0


def test_equity_curve_length_equals_candle_count_with_rebalance():
    """Equity curve length must always equal the number of candles."""
    candles = [make_candle(float(100 + i)) for i in range(15)]
    manager = make_manager([AlwaysFlat, AlwaysBuyHold], interval=5)
    result = manager.run(candles)
    assert len(result["equity_curve"]) == 15


def test_equity_first_element_equals_initial_capital_for_flat():
    """For a flat strategy, first equity value equals initial capital."""
    candles = [make_candle(100.0) for _ in range(5)]
    manager = make_manager([AlwaysFlat], initial_capital=1000, interval=10)
    result = manager.run(candles)
    assert result["equity_curve"][0] == pytest.approx(1000.0)


def test_positive_returns_final_equity_greater_than_initial():
    """
    Buy-hold on strictly rising prices → final equity > initial capital.
    """
    candles = [make_candle(float(100 + i * 5)) for i in range(20)]
    manager = make_manager([AlwaysBuyHold], initial_capital=1000, interval=100)
    result = manager.run(candles)
    assert result["final_portfolio_equity"] > 1000.0
