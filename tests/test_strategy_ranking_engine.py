"""
Tests for research.strategy_ranking_engine.StrategyRankingEngine

Contract
--------
StrategyRankingEngine(
    strategies: list[type],
    candles: list[dict],
    initial_cash: float = 1000,
    train_size: int = 10,
    test_size: int = 5,
    step_size: int = 5,
    simulations: int = 50,
    seed=None,
)

instance.run() -> list[dict]

Each result dict contains:
    strategy_name   : str
    backtest        : dict  (return_pct, sharpe_ratio, calmar_ratio, max_drawdown_pct)
    stability       : dict  (stability_score)
    walk_forward    : dict  (mean_test_sharpe, performance_decay)
    monte_carlo     : dict  (mean_sharpe, sharpe_variance, probability_of_loss)
    robustness      : float
    composite_score : float
    rank            : int   (1-based, sorted descending by composite_score)

Composite score formula:
    1.0 * sharpe_ratio
  + 0.8 * calmar_ratio
  + 1.2 * stability_score
  + 1.5 * robustness_score
  - 1.0 * abs(max_drawdown_pct)
  - 1.0 * abs(performance_decay)

Validation:
    - Empty strategies list → ValueError
    - simulations < 1 → ValueError (propagated from MonteCarloEngine)
    - Input candles must NOT be mutated
    - Deterministic under fixed seed
"""

import copy
import pytest

from research.strategy_ranking_engine import StrategyRankingEngine
from app.backtester.engine import Backtester
from research.stability_engine import analyze_strategy as stability_analyze
from research.walk_forward_engine import walk_forward_analysis
from research.monte_carlo_engine import MonteCarloEngine
from research.robustness_engine import RobustnessEngine


# ---------------------------------------------------------------------------
# Candle factory
# ---------------------------------------------------------------------------

def make_candle(timestamp: str, close: float) -> dict:
    return {
        "timestamp": timestamp,
        "open":   close,
        "high":   close,
        "low":    close,
        "close":  close,
        "volume": 1_000_000,
    }


# ---------------------------------------------------------------------------
# Candle fixtures
#
# CANDLES_20: 20 candles with train_size=4, test_size=4, step_size=4
#   Stability:     5 non-overlapping windows of 4 candles each
#   Walk-forward:  4 complete folds (pos 0,4,8,12; pos 16 → test[20:24]=[] → stop)
#   Robustness:    same 4 folds
#
# Two price series are used to create two strategies with different scores:
#   CANDLES_RISING:  monotonically rising prices → strong trend
#   CANDLES_FLAT:    flat prices → no trend, zero returns
# ---------------------------------------------------------------------------

CANDLES_20 = [
    make_candle(f"2024-01-{i+1:02d}", float(100 + i * 5))
    for i in range(20)
]

CANDLES_FLAT = [
    make_candle(f"2024-01-{i+1:02d}", 100.0)
    for i in range(20)
]


# ---------------------------------------------------------------------------
# Strategy fixtures
# ---------------------------------------------------------------------------

class AlwaysLongStrategy:
    """BUY on first candle, HOLD the rest — fully invested throughout."""
    def generate(self, candles: list) -> list:
        return ["BUY"] + ["HOLD"] * (len(candles) - 1)


class AlwaysFlatStrategy:
    """Never buys — always HOLD (zero returns)."""
    def generate(self, candles: list) -> list:
        return ["HOLD"] * len(candles)


# ---------------------------------------------------------------------------
# Reference implementation — mirrors the specification exactly
# ---------------------------------------------------------------------------

def _ref_composite_score(
    strategy_class,
    candles: list,
    initial_cash: float = 1000,
    train_size: int = 4,
    test_size: int = 4,
    step_size: int = 4,
    simulations: int = 10,
    seed=None,
) -> float:
    """
    Compute composite score using the same engines as StrategyRankingEngine.
    Used to verify formula correctness without hard-coding floats.
    """
    # Backtest
    bt = Backtester(initial_cash)
    bt_result = bt.run(
        [copy.copy(c) for c in candles],
        strategy=strategy_class(),
    )
    sharpe_ratio     = bt_result["sharpe_ratio"]
    calmar_ratio     = bt_result["calmar_ratio"]
    max_drawdown_pct = bt_result["max_drawdown_pct"]

    # Stability
    stab_result = stability_analyze(
        strategy_class,
        [copy.copy(c) for c in candles],
        window_size=train_size,
        initial_cash=initial_cash,
    )
    stability_score = stab_result["stability_score"]

    # Walk-forward
    wf_result = walk_forward_analysis(
        strategy_class,
        [copy.copy(c) for c in candles],
        train_size=train_size,
        test_size=test_size,
        step_size=step_size,
        initial_cash=initial_cash,
    )
    performance_decay = wf_result["performance_decay"]

    # Monte Carlo
    mc_engine = MonteCarloEngine(initial_cash=initial_cash, seed=seed)
    mc_result = mc_engine.analyze(
        returns_series=bt_result["returns_series"],
        mode="returns",
        simulations=simulations,
    )

    # Robustness
    rob_engine = RobustnessEngine(
        strategy_class=strategy_class,
        candles=[copy.copy(c) for c in candles],
        train_size=train_size,
        test_size=test_size,
        step_size=step_size,
        simulations=simulations,
        seed=seed,
        initial_cash=initial_cash,
    )
    rob_result = rob_engine.run()
    robustness_score = rob_result["robustness_score"]

    return (
        1.0 * sharpe_ratio
        + 0.8 * calmar_ratio
        + 1.2 * stability_score
        + 1.5 * robustness_score
        - 1.0 * abs(max_drawdown_pct)
        - 1.0 * abs(performance_decay)
    )


# ---------------------------------------------------------------------------
# Common engine kwargs for tests
# ---------------------------------------------------------------------------

ENGINE_KWARGS = dict(
    initial_cash=1000,
    train_size=4,
    test_size=4,
    step_size=4,
    simulations=10,
    seed=42,
)


# ===========================================================================
# Part 1 — Return type and required keys
# ===========================================================================

def test_run_returns_list():
    engine = StrategyRankingEngine(
        strategies=[AlwaysLongStrategy],
        candles=CANDLES_20,
        **ENGINE_KWARGS,
    )
    result = engine.run()
    assert isinstance(result, list)


def test_single_strategy_returns_length_one():
    engine = StrategyRankingEngine(
        strategies=[AlwaysLongStrategy],
        candles=CANDLES_20,
        **ENGINE_KWARGS,
    )
    result = engine.run()
    assert len(result) == 1


def test_two_strategies_returns_length_two():
    engine = StrategyRankingEngine(
        strategies=[AlwaysLongStrategy, AlwaysFlatStrategy],
        candles=CANDLES_20,
        **ENGINE_KWARGS,
    )
    result = engine.run()
    assert len(result) == 2


def test_result_entry_has_strategy_name():
    engine = StrategyRankingEngine(
        strategies=[AlwaysLongStrategy],
        candles=CANDLES_20,
        **ENGINE_KWARGS,
    )
    result = engine.run()
    assert "strategy_name" in result[0]


def test_result_entry_has_backtest():
    engine = StrategyRankingEngine(
        strategies=[AlwaysLongStrategy],
        candles=CANDLES_20,
        **ENGINE_KWARGS,
    )
    result = engine.run()
    assert "backtest" in result[0]


def test_result_entry_has_stability():
    engine = StrategyRankingEngine(
        strategies=[AlwaysLongStrategy],
        candles=CANDLES_20,
        **ENGINE_KWARGS,
    )
    result = engine.run()
    assert "stability" in result[0]


def test_result_entry_has_walk_forward():
    engine = StrategyRankingEngine(
        strategies=[AlwaysLongStrategy],
        candles=CANDLES_20,
        **ENGINE_KWARGS,
    )
    result = engine.run()
    assert "walk_forward" in result[0]


def test_result_entry_has_monte_carlo():
    engine = StrategyRankingEngine(
        strategies=[AlwaysLongStrategy],
        candles=CANDLES_20,
        **ENGINE_KWARGS,
    )
    result = engine.run()
    assert "monte_carlo" in result[0]


def test_result_entry_has_robustness():
    engine = StrategyRankingEngine(
        strategies=[AlwaysLongStrategy],
        candles=CANDLES_20,
        **ENGINE_KWARGS,
    )
    result = engine.run()
    assert "robustness" in result[0]


def test_result_entry_has_composite_score():
    engine = StrategyRankingEngine(
        strategies=[AlwaysLongStrategy],
        candles=CANDLES_20,
        **ENGINE_KWARGS,
    )
    result = engine.run()
    assert "composite_score" in result[0]


def test_result_entry_has_rank():
    engine = StrategyRankingEngine(
        strategies=[AlwaysLongStrategy],
        candles=CANDLES_20,
        **ENGINE_KWARGS,
    )
    result = engine.run()
    assert "rank" in result[0]


# ===========================================================================
# Part 2 — strategy_name correctness
# ===========================================================================

def test_strategy_name_matches_class_name():
    engine = StrategyRankingEngine(
        strategies=[AlwaysLongStrategy],
        candles=CANDLES_20,
        **ENGINE_KWARGS,
    )
    result = engine.run()
    assert result[0]["strategy_name"] == "AlwaysLongStrategy"


def test_strategy_names_both_present_two_strategies():
    engine = StrategyRankingEngine(
        strategies=[AlwaysLongStrategy, AlwaysFlatStrategy],
        candles=CANDLES_20,
        **ENGINE_KWARGS,
    )
    result = engine.run()
    names = {r["strategy_name"] for r in result}
    assert "AlwaysLongStrategy" in names
    assert "AlwaysFlatStrategy" in names


# ===========================================================================
# Part 3 — backtest sub-dict keys
# ===========================================================================

def test_backtest_has_return_pct():
    engine = StrategyRankingEngine(
        strategies=[AlwaysLongStrategy],
        candles=CANDLES_20,
        **ENGINE_KWARGS,
    )
    result = engine.run()
    assert "return_pct" in result[0]["backtest"]


def test_backtest_has_sharpe_ratio():
    engine = StrategyRankingEngine(
        strategies=[AlwaysLongStrategy],
        candles=CANDLES_20,
        **ENGINE_KWARGS,
    )
    result = engine.run()
    assert "sharpe_ratio" in result[0]["backtest"]


def test_backtest_has_calmar_ratio():
    engine = StrategyRankingEngine(
        strategies=[AlwaysLongStrategy],
        candles=CANDLES_20,
        **ENGINE_KWARGS,
    )
    result = engine.run()
    assert "calmar_ratio" in result[0]["backtest"]


def test_backtest_has_max_drawdown_pct():
    engine = StrategyRankingEngine(
        strategies=[AlwaysLongStrategy],
        candles=CANDLES_20,
        **ENGINE_KWARGS,
    )
    result = engine.run()
    assert "max_drawdown_pct" in result[0]["backtest"]


# ===========================================================================
# Part 4 — stability sub-dict keys
# ===========================================================================

def test_stability_has_stability_score():
    engine = StrategyRankingEngine(
        strategies=[AlwaysLongStrategy],
        candles=CANDLES_20,
        **ENGINE_KWARGS,
    )
    result = engine.run()
    assert "stability_score" in result[0]["stability"]


# ===========================================================================
# Part 5 — walk_forward sub-dict keys
# ===========================================================================

def test_walk_forward_has_mean_test_sharpe():
    engine = StrategyRankingEngine(
        strategies=[AlwaysLongStrategy],
        candles=CANDLES_20,
        **ENGINE_KWARGS,
    )
    result = engine.run()
    assert "mean_test_sharpe" in result[0]["walk_forward"]


def test_walk_forward_has_performance_decay():
    engine = StrategyRankingEngine(
        strategies=[AlwaysLongStrategy],
        candles=CANDLES_20,
        **ENGINE_KWARGS,
    )
    result = engine.run()
    assert "performance_decay" in result[0]["walk_forward"]


# ===========================================================================
# Part 6 — monte_carlo sub-dict keys
# ===========================================================================

def test_monte_carlo_has_mean_sharpe():
    engine = StrategyRankingEngine(
        strategies=[AlwaysLongStrategy],
        candles=CANDLES_20,
        **ENGINE_KWARGS,
    )
    result = engine.run()
    assert "mean_sharpe" in result[0]["monte_carlo"]


def test_monte_carlo_has_sharpe_variance():
    engine = StrategyRankingEngine(
        strategies=[AlwaysLongStrategy],
        candles=CANDLES_20,
        **ENGINE_KWARGS,
    )
    result = engine.run()
    assert "sharpe_variance" in result[0]["monte_carlo"]


def test_monte_carlo_has_probability_of_loss():
    engine = StrategyRankingEngine(
        strategies=[AlwaysLongStrategy],
        candles=CANDLES_20,
        **ENGINE_KWARGS,
    )
    result = engine.run()
    assert "probability_of_loss" in result[0]["monte_carlo"]


# ===========================================================================
# Part 7 — Single strategy: rank is 1
# ===========================================================================

def test_single_strategy_rank_is_one():
    engine = StrategyRankingEngine(
        strategies=[AlwaysLongStrategy],
        candles=CANDLES_20,
        **ENGINE_KWARGS,
    )
    result = engine.run()
    assert result[0]["rank"] == 1


# ===========================================================================
# Part 8 — Composite score formula correctness
# ===========================================================================

def test_composite_score_matches_formula_single_strategy():
    """composite_score must equal the formula applied to the sub-dict values."""
    engine = StrategyRankingEngine(
        strategies=[AlwaysLongStrategy],
        candles=CANDLES_20,
        **ENGINE_KWARGS,
    )
    result = engine.run()
    entry = result[0]

    sharpe_ratio     = entry["backtest"]["sharpe_ratio"]
    calmar_ratio     = entry["backtest"]["calmar_ratio"]
    max_drawdown_pct = entry["backtest"]["max_drawdown_pct"]
    stability_score  = entry["stability"]["stability_score"]
    performance_decay = entry["walk_forward"]["performance_decay"]
    robustness_score  = entry["robustness"]

    expected = (
        1.0 * sharpe_ratio
        + 0.8 * calmar_ratio
        + 1.2 * stability_score
        + 1.5 * robustness_score
        - 1.0 * abs(max_drawdown_pct)
        - 1.0 * abs(performance_decay)
    )
    assert entry["composite_score"] == pytest.approx(expected, rel=1e-9)


def test_composite_score_matches_reference_implementation():
    """composite_score must match the reference implementation."""
    engine = StrategyRankingEngine(
        strategies=[AlwaysLongStrategy],
        candles=CANDLES_20,
        **ENGINE_KWARGS,
    )
    result = engine.run()

    expected = _ref_composite_score(
        AlwaysLongStrategy,
        CANDLES_20,
        **ENGINE_KWARGS,
    )
    assert result[0]["composite_score"] == pytest.approx(expected, rel=1e-9)


def test_composite_score_formula_for_flat_strategy():
    """Verify formula correctness for AlwaysFlatStrategy too."""
    engine = StrategyRankingEngine(
        strategies=[AlwaysFlatStrategy],
        candles=CANDLES_20,
        **ENGINE_KWARGS,
    )
    result = engine.run()
    entry = result[0]

    sharpe_ratio     = entry["backtest"]["sharpe_ratio"]
    calmar_ratio     = entry["backtest"]["calmar_ratio"]
    max_drawdown_pct = entry["backtest"]["max_drawdown_pct"]
    stability_score  = entry["stability"]["stability_score"]
    performance_decay = entry["walk_forward"]["performance_decay"]
    robustness_score  = entry["robustness"]

    expected = (
        1.0 * sharpe_ratio
        + 0.8 * calmar_ratio
        + 1.2 * stability_score
        + 1.5 * robustness_score
        - 1.0 * abs(max_drawdown_pct)
        - 1.0 * abs(performance_decay)
    )
    assert entry["composite_score"] == pytest.approx(expected, rel=1e-9)


# ===========================================================================
# Part 9 — Two strategies: sorted descending by composite_score
# ===========================================================================

def test_two_strategies_sorted_descending():
    """Results must be sorted descending by composite_score."""
    engine = StrategyRankingEngine(
        strategies=[AlwaysLongStrategy, AlwaysFlatStrategy],
        candles=CANDLES_20,
        **ENGINE_KWARGS,
    )
    result = engine.run()
    assert result[0]["composite_score"] >= result[1]["composite_score"]


def test_two_strategies_rank_increments():
    """Rank must be 1 for first entry and 2 for second."""
    engine = StrategyRankingEngine(
        strategies=[AlwaysLongStrategy, AlwaysFlatStrategy],
        candles=CANDLES_20,
        **ENGINE_KWARGS,
    )
    result = engine.run()
    assert result[0]["rank"] == 1
    assert result[1]["rank"] == 2


def test_rank_increments_correctly_for_three_strategies():
    """Ranks must be 1, 2, 3 in order."""
    # Use three copies of the same strategy class to get three entries
    class StratA(AlwaysLongStrategy):
        pass

    class StratB(AlwaysLongStrategy):
        pass

    class StratC(AlwaysLongStrategy):
        pass

    engine = StrategyRankingEngine(
        strategies=[StratA, StratB, StratC],
        candles=CANDLES_20,
        **ENGINE_KWARGS,
    )
    result = engine.run()
    assert len(result) == 3
    assert result[0]["rank"] == 1
    assert result[1]["rank"] == 2
    assert result[2]["rank"] == 3


def test_higher_ranked_strategy_has_higher_or_equal_composite_score():
    """For every adjacent pair, rank[i].composite_score >= rank[i+1].composite_score."""
    engine = StrategyRankingEngine(
        strategies=[AlwaysLongStrategy, AlwaysFlatStrategy],
        candles=CANDLES_20,
        **ENGINE_KWARGS,
    )
    result = engine.run()
    for i in range(len(result) - 1):
        assert result[i]["composite_score"] >= result[i + 1]["composite_score"]


# ===========================================================================
# Part 10 — Deterministic ordering when seed fixed
# ===========================================================================

def test_deterministic_with_fixed_seed():
    """Two runs with the same seed must produce identical composite scores."""
    kwargs = dict(
        strategies=[AlwaysLongStrategy, AlwaysFlatStrategy],
        candles=CANDLES_20,
        initial_cash=1000,
        train_size=4,
        test_size=4,
        step_size=4,
        simulations=20,
        seed=99,
    )
    result1 = StrategyRankingEngine(**kwargs).run()
    result2 = StrategyRankingEngine(**kwargs).run()

    for r1, r2 in zip(result1, result2):
        assert r1["composite_score"] == pytest.approx(r2["composite_score"], rel=1e-12)
        assert r1["rank"] == r2["rank"]
        assert r1["strategy_name"] == r2["strategy_name"]


def test_different_seeds_may_differ():
    """Two runs with different seeds should (in general) differ for MC-sensitive metrics."""
    result_a = StrategyRankingEngine(
        strategies=[AlwaysLongStrategy],
        candles=CANDLES_20,
        initial_cash=1000,
        train_size=4,
        test_size=4,
        step_size=4,
        simulations=20,
        seed=1,
    ).run()
    result_b = StrategyRankingEngine(
        strategies=[AlwaysLongStrategy],
        candles=CANDLES_20,
        initial_cash=1000,
        train_size=4,
        test_size=4,
        step_size=4,
        simulations=20,
        seed=2,
    ).run()
    # Monte Carlo results may differ; we just verify both runs complete without error
    assert len(result_a) == 1
    assert len(result_b) == 1


# ===========================================================================
# Part 11 — Input candles not mutated
# ===========================================================================

def test_input_candles_not_mutated():
    """The engine must not modify the input candles list or its dicts."""
    original = [make_candle(f"2024-01-{i+1:02d}", float(100 + i * 5)) for i in range(20)]
    snapshot = copy.deepcopy(original)

    engine = StrategyRankingEngine(
        strategies=[AlwaysLongStrategy],
        candles=original,
        **ENGINE_KWARGS,
    )
    engine.run()

    assert original == snapshot, "Input candles were mutated by StrategyRankingEngine"


def test_input_candles_list_length_not_changed():
    """The length of the input candles list must remain unchanged."""
    original = [make_candle(f"2024-01-{i+1:02d}", float(100 + i * 5)) for i in range(20)]
    original_len = len(original)

    engine = StrategyRankingEngine(
        strategies=[AlwaysLongStrategy],
        candles=original,
        **ENGINE_KWARGS,
    )
    engine.run()

    assert len(original) == original_len


# ===========================================================================
# Part 12 — Empty strategies list raises ValueError
# ===========================================================================

def test_empty_strategies_raises_value_error():
    with pytest.raises(ValueError):
        StrategyRankingEngine(
            strategies=[],
            candles=CANDLES_20,
            **ENGINE_KWARGS,
        )


def test_empty_strategies_error_raised_at_construction():
    """ValueError must be raised in __init__, not deferred to run()."""
    with pytest.raises(ValueError):
        StrategyRankingEngine(strategies=[], candles=CANDLES_20, **ENGINE_KWARGS)


# ===========================================================================
# Part 13 — simulations < 1 propagates ValueError
# ===========================================================================

def test_simulations_zero_raises_value_error():
    """simulations=0 must propagate ValueError from MonteCarloEngine."""
    engine = StrategyRankingEngine(
        strategies=[AlwaysLongStrategy],
        candles=CANDLES_20,
        initial_cash=1000,
        train_size=4,
        test_size=4,
        step_size=4,
        simulations=0,
        seed=42,
    )
    with pytest.raises(ValueError):
        engine.run()


# ===========================================================================
# Part 14 — Stable sort: equal composite scores preserve insertion order
# ===========================================================================

def test_stable_sort_equal_scores_preserve_insertion_order():
    """
    When two strategies produce identical composite scores, the one that
    appears first in the input list must appear first in the output.

    We achieve identical scores by using two subclasses of AlwaysLongStrategy
    applied to the same candles with the same seed — they will produce
    bit-for-bit identical results.
    """
    class StratX(AlwaysLongStrategy):
        pass

    class StratY(AlwaysLongStrategy):
        pass

    engine = StrategyRankingEngine(
        strategies=[StratX, StratY],
        candles=CANDLES_20,
        **ENGINE_KWARGS,
    )
    result = engine.run()

    # Both strategies must have the same composite score
    assert result[0]["composite_score"] == pytest.approx(
        result[1]["composite_score"], rel=1e-9
    )

    # Insertion order must be preserved: StratX before StratY
    assert result[0]["strategy_name"] == "StratX"
    assert result[1]["strategy_name"] == "StratY"


# ===========================================================================
# Part 15 — robustness field is a float
# ===========================================================================

def test_robustness_field_is_float():
    engine = StrategyRankingEngine(
        strategies=[AlwaysLongStrategy],
        candles=CANDLES_20,
        **ENGINE_KWARGS,
    )
    result = engine.run()
    assert isinstance(result[0]["robustness"], float)


def test_composite_score_is_float():
    engine = StrategyRankingEngine(
        strategies=[AlwaysLongStrategy],
        candles=CANDLES_20,
        **ENGINE_KWARGS,
    )
    result = engine.run()
    assert isinstance(result[0]["composite_score"], float)


# ===========================================================================
# Part 16 — backtest values match Backtester directly
# ===========================================================================

def test_backtest_return_pct_matches_backtester():
    """backtest.return_pct must equal Backtester.run output directly."""
    bt = Backtester(1000)
    expected = bt.run(
        [copy.copy(c) for c in CANDLES_20],
        strategy=AlwaysLongStrategy(),
    )["return_pct"]

    engine = StrategyRankingEngine(
        strategies=[AlwaysLongStrategy],
        candles=CANDLES_20,
        **ENGINE_KWARGS,
    )
    result = engine.run()
    assert result[0]["backtest"]["return_pct"] == pytest.approx(expected, rel=1e-9)


def test_backtest_sharpe_ratio_matches_backtester():
    bt = Backtester(1000)
    expected = bt.run(
        [copy.copy(c) for c in CANDLES_20],
        strategy=AlwaysLongStrategy(),
    )["sharpe_ratio"]

    engine = StrategyRankingEngine(
        strategies=[AlwaysLongStrategy],
        candles=CANDLES_20,
        **ENGINE_KWARGS,
    )
    result = engine.run()
    assert result[0]["backtest"]["sharpe_ratio"] == pytest.approx(expected, rel=1e-9)


def test_backtest_max_drawdown_matches_backtester():
    bt = Backtester(1000)
    expected = bt.run(
        [copy.copy(c) for c in CANDLES_20],
        strategy=AlwaysLongStrategy(),
    )["max_drawdown_pct"]

    engine = StrategyRankingEngine(
        strategies=[AlwaysLongStrategy],
        candles=CANDLES_20,
        **ENGINE_KWARGS,
    )
    result = engine.run()
    assert result[0]["backtest"]["max_drawdown_pct"] == pytest.approx(expected, rel=1e-9)
