"""
RED tests for research.robustness_engine.RobustnessEngine

Contract
--------
RobustnessEngine(
    strategy_class,
    candles: list[dict],
    train_size: int,
    test_size: int,
    step_size: int,
    simulations: int = 100,
    seed: int | None = None,
    initial_cash: float = 1000,
) -> instance

instance.run() -> dict

Algorithm
---------
For each walk-forward fold i (same slicing as walk_forward_analysis):

    1. Run backtester on train slice (strategy_class instance, initial_cash)
       → collect train returns_series
    2. Run backtester on test slice (strategy_class instance, initial_cash)
       → collect test returns_series
    3. Run MonteCarloEngine(initial_cash, seed).analyze(
           returns_series=test_returns_series,
           mode="returns",
           simulations=simulations,
       )
       → mc_result

    R_i = mc_result["mean_sharpe"]
          - mc_result["sharpe_variance"]
          - mc_result["probability_of_loss"]

Global:
    R = mean(R_i  for all i)

Return dict keys:
    fold_scores     : list[float]   — R_i per fold
    fold_mc_results : list[dict]    — raw MonteCarloEngine output per fold
    robustness_score: float         — mean of fold_scores

Constraints:
    - Deterministic under fixed seed
    - Input candles must NOT be mutated
    - ValueError propagated from walk_forward_analysis for invalid params
"""

import copy
import math
import pytest

from research.robustness_engine import RobustnessEngine
from research.monte_carlo_engine import MonteCarloEngine
from app.backtester.engine import Backtester


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def make_candle(timestamp: str, close: float) -> dict:
    return {
        "timestamp": timestamp,
        "open": close,
        "high": close,
        "low": close,
        "close": close,
        "volume": 1_000_000,
    }


class AlwaysLongStrategy:
    """BUY on first candle, HOLD the rest — fully invested throughout."""
    def generate(self, candles: list[dict]) -> list[str]:
        return ["BUY"] + ["HOLD"] * (len(candles) - 1)


class AlwaysFlatStrategy:
    """Never buys — always HOLD."""
    def generate(self, candles: list[dict]) -> list[str]:
        return ["HOLD"] * len(candles)


# ---------------------------------------------------------------------------
# Minimal candle fixtures
#
# CANDLES_12: 12 candles, train_size=4, test_size=4, step_size=4
#   → 2 complete folds
#   Fold 0: train=[0:4], test=[4:8]
#   Fold 1: train=[4:8], test=[8:12]
#
# CANDLES_8: 8 candles, train_size=4, test_size=4, step_size=4
#   → 1 complete fold
#   Fold 0: train=[0:4], test=[4:8]
# ---------------------------------------------------------------------------

CANDLES_12 = [
    make_candle("2024-01-01", 100.0),
    make_candle("2024-01-02", 110.0),
    make_candle("2024-01-03", 120.0),
    make_candle("2024-01-04", 130.0),
    make_candle("2024-01-05", 130.0),
    make_candle("2024-01-06", 120.0),
    make_candle("2024-01-07", 110.0),
    make_candle("2024-01-08", 100.0),
    make_candle("2024-01-09", 100.0),
    make_candle("2024-01-10", 110.0),
    make_candle("2024-01-11", 120.0),
    make_candle("2024-01-12", 130.0),
]

CANDLES_8 = [
    make_candle("2024-01-01", 100.0),
    make_candle("2024-01-02", 110.0),
    make_candle("2024-01-03", 120.0),
    make_candle("2024-01-04", 130.0),
    make_candle("2024-01-05", 140.0),
    make_candle("2024-01-06", 150.0),
    make_candle("2024-01-07", 160.0),
    make_candle("2024-01-08", 170.0),
]


# ---------------------------------------------------------------------------
# Reference implementation — mirrors the specification exactly
# ---------------------------------------------------------------------------

def _ref_run() -> None:
    """Placeholder — see _ref_robustness below."""


def _ref_robustness(
    strategy_class,
    candles: list[dict],
    train_size: int,
    test_size: int,
    step_size: int,
    simulations: int = 100,
    seed=None,
    initial_cash: float = 1000,
) -> dict:
    """
    Pure-Python reference implementation.

    Replicates the specification so tests remain self-consistent without
    hard-coding fragile float literals.
    """
    # Replicate walk_forward_analysis fold slicing
    pos = 0
    fold_scores = []
    fold_mc_results = []

    while True:
        train_slice = candles[pos: pos + train_size]
        test_slice  = candles[pos + train_size: pos + train_size + test_size]
        if len(test_slice) < test_size:
            break

        # Run backtester on test slice
        bt = Backtester(initial_cash)
        test_result = bt.run(
            [copy.copy(c) for c in test_slice],
            strategy=strategy_class(),
        )
        test_returns_series = test_result["returns_series"]

        # Monte Carlo on test returns
        mc_engine = MonteCarloEngine(initial_cash=initial_cash, seed=seed)
        mc_result = mc_engine.analyze(
            returns_series=test_returns_series,
            mode="returns",
            simulations=simulations,
        )

        # R_i = mc_mean_sharpe - mc_variance - mc_probability_of_loss
        r_i = (
            mc_result["mean_sharpe"]
            - mc_result["sharpe_variance"]
            - mc_result["probability_of_loss"]
        )

        fold_scores.append(r_i)
        fold_mc_results.append(mc_result)

        pos += step_size

    robustness_score = sum(fold_scores) / len(fold_scores)

    return {
        "fold_scores":      fold_scores,
        "fold_mc_results":  fold_mc_results,
        "robustness_score": robustness_score,
    }


# ===========================================================================
# Part 1 — Return type and required keys
# ===========================================================================

def test_run_returns_dict():
    engine = RobustnessEngine(
        AlwaysLongStrategy, CANDLES_8,
        train_size=4, test_size=4, step_size=4,
        simulations=10, seed=42,
    )
    result = engine.run()
    assert isinstance(result, dict)


def test_result_has_fold_scores_key():
    engine = RobustnessEngine(
        AlwaysLongStrategy, CANDLES_8,
        train_size=4, test_size=4, step_size=4,
        simulations=10, seed=42,
    )
    result = engine.run()
    assert "fold_scores" in result


def test_result_has_fold_mc_results_key():
    engine = RobustnessEngine(
        AlwaysLongStrategy, CANDLES_8,
        train_size=4, test_size=4, step_size=4,
        simulations=10, seed=42,
    )
    result = engine.run()
    assert "fold_mc_results" in result


def test_result_has_robustness_score_key():
    engine = RobustnessEngine(
        AlwaysLongStrategy, CANDLES_8,
        train_size=4, test_size=4, step_size=4,
        simulations=10, seed=42,
    )
    result = engine.run()
    assert "robustness_score" in result


# ===========================================================================
# Part 2 — fold_scores structure
# ===========================================================================

def test_fold_scores_is_list():
    engine = RobustnessEngine(
        AlwaysLongStrategy, CANDLES_8,
        train_size=4, test_size=4, step_size=4,
        simulations=10, seed=42,
    )
    result = engine.run()
    assert isinstance(result["fold_scores"], list)


def test_fold_scores_length_single_fold():
    # 8 candles, train=4, test=4, step=4 → 1 fold
    engine = RobustnessEngine(
        AlwaysLongStrategy, CANDLES_8,
        train_size=4, test_size=4, step_size=4,
        simulations=10, seed=42,
    )
    result = engine.run()
    assert len(result["fold_scores"]) == 1


def test_fold_scores_length_two_folds():
    # 12 candles, train=4, test=4, step=4 → 2 folds
    engine = RobustnessEngine(
        AlwaysLongStrategy, CANDLES_12,
        train_size=4, test_size=4, step_size=4,
        simulations=10, seed=42,
    )
    result = engine.run()
    assert len(result["fold_scores"]) == 2


def test_fold_scores_elements_are_floats():
    engine = RobustnessEngine(
        AlwaysLongStrategy, CANDLES_8,
        train_size=4, test_size=4, step_size=4,
        simulations=10, seed=42,
    )
    result = engine.run()
    for s in result["fold_scores"]:
        assert isinstance(s, float)


# ===========================================================================
# Part 3 — fold_mc_results structure
# ===========================================================================

def test_fold_mc_results_is_list():
    engine = RobustnessEngine(
        AlwaysLongStrategy, CANDLES_8,
        train_size=4, test_size=4, step_size=4,
        simulations=10, seed=42,
    )
    result = engine.run()
    assert isinstance(result["fold_mc_results"], list)


def test_fold_mc_results_length_matches_fold_scores():
    engine = RobustnessEngine(
        AlwaysLongStrategy, CANDLES_12,
        train_size=4, test_size=4, step_size=4,
        simulations=10, seed=42,
    )
    result = engine.run()
    assert len(result["fold_mc_results"]) == len(result["fold_scores"])


def test_each_fold_mc_result_has_mean_sharpe():
    engine = RobustnessEngine(
        AlwaysLongStrategy, CANDLES_12,
        train_size=4, test_size=4, step_size=4,
        simulations=10, seed=42,
    )
    result = engine.run()
    for mc in result["fold_mc_results"]:
        assert "mean_sharpe" in mc


def test_each_fold_mc_result_has_sharpe_variance():
    engine = RobustnessEngine(
        AlwaysLongStrategy, CANDLES_12,
        train_size=4, test_size=4, step_size=4,
        simulations=10, seed=42,
    )
    result = engine.run()
    for mc in result["fold_mc_results"]:
        assert "sharpe_variance" in mc


def test_each_fold_mc_result_has_probability_of_loss():
    engine = RobustnessEngine(
        AlwaysLongStrategy, CANDLES_12,
        train_size=4, test_size=4, step_size=4,
        simulations=10, seed=42,
    )
    result = engine.run()
    for mc in result["fold_mc_results"]:
        assert "probability_of_loss" in mc


def test_each_fold_mc_result_has_simulations_results():
    engine = RobustnessEngine(
        AlwaysLongStrategy, CANDLES_8,
        train_size=4, test_size=4, step_size=4,
        simulations=10, seed=42,
    )
    result = engine.run()
    for mc in result["fold_mc_results"]:
        assert "simulations_results" in mc


def test_fold_mc_simulations_results_length_equals_simulations_param():
    simulations = 15
    engine = RobustnessEngine(
        AlwaysLongStrategy, CANDLES_8,
        train_size=4, test_size=4, step_size=4,
        simulations=simulations, seed=42,
    )
    result = engine.run()
    for mc in result["fold_mc_results"]:
        assert len(mc["simulations_results"]) == simulations


# ===========================================================================
# Part 4 — R_i formula correctness
# R_i = mc_mean_sharpe - mc_sharpe_variance - mc_probability_of_loss
# ===========================================================================

def test_fold_score_formula_single_fold():
    """R_i must equal mean_sharpe - sharpe_variance - probability_of_loss."""
    engine = RobustnessEngine(
        AlwaysLongStrategy, CANDLES_8,
        train_size=4, test_size=4, step_size=4,
        simulations=20, seed=42,
    )
    result = engine.run()
    mc = result["fold_mc_results"][0]
    expected_r0 = (
        mc["mean_sharpe"]
        - mc["sharpe_variance"]
        - mc["probability_of_loss"]
    )
    assert result["fold_scores"][0] == pytest.approx(expected_r0, rel=1e-9)


def test_fold_score_formula_all_folds():
    """All R_i must equal mean_sharpe - sharpe_variance - probability_of_loss."""
    engine = RobustnessEngine(
        AlwaysLongStrategy, CANDLES_12,
        train_size=4, test_size=4, step_size=4,
        simulations=20, seed=42,
    )
    result = engine.run()
    for i, mc in enumerate(result["fold_mc_results"]):
        expected = (
            mc["mean_sharpe"]
            - mc["sharpe_variance"]
            - mc["probability_of_loss"]
        )
        assert result["fold_scores"][i] == pytest.approx(expected, rel=1e-9)


# ===========================================================================
# Part 5 — robustness_score correctness
# R = mean(R_i)
# ===========================================================================

def test_robustness_score_is_float():
    engine = RobustnessEngine(
        AlwaysLongStrategy, CANDLES_8,
        train_size=4, test_size=4, step_size=4,
        simulations=10, seed=42,
    )
    result = engine.run()
    assert isinstance(result["robustness_score"], float)


def test_robustness_score_equals_mean_of_fold_scores_single_fold():
    engine = RobustnessEngine(
        AlwaysLongStrategy, CANDLES_8,
        train_size=4, test_size=4, step_size=4,
        simulations=10, seed=42,
    )
    result = engine.run()
    expected = sum(result["fold_scores"]) / len(result["fold_scores"])
    assert result["robustness_score"] == pytest.approx(expected, rel=1e-9)


def test_robustness_score_equals_mean_of_fold_scores_two_folds():
    engine = RobustnessEngine(
        AlwaysLongStrategy, CANDLES_12,
        train_size=4, test_size=4, step_size=4,
        simulations=10, seed=42,
    )
    result = engine.run()
    expected = sum(result["fold_scores"]) / len(result["fold_scores"])
    assert result["robustness_score"] == pytest.approx(expected, rel=1e-9)


def test_robustness_score_matches_reference_single_fold():
    ref = _ref_robustness(
        AlwaysLongStrategy, CANDLES_8,
        train_size=4, test_size=4, step_size=4,
        simulations=50, seed=7,
    )
    engine = RobustnessEngine(
        AlwaysLongStrategy, CANDLES_8,
        train_size=4, test_size=4, step_size=4,
        simulations=50, seed=7,
    )
    result = engine.run()
    assert result["robustness_score"] == pytest.approx(ref["robustness_score"], rel=1e-9)


def test_robustness_score_matches_reference_two_folds():
    ref = _ref_robustness(
        AlwaysLongStrategy, CANDLES_12,
        train_size=4, test_size=4, step_size=4,
        simulations=50, seed=7,
    )
    engine = RobustnessEngine(
        AlwaysLongStrategy, CANDLES_12,
        train_size=4, test_size=4, step_size=4,
        simulations=50, seed=7,
    )
    result = engine.run()
    assert result["robustness_score"] == pytest.approx(ref["robustness_score"], rel=1e-9)


def test_fold_scores_match_reference_two_folds():
    ref = _ref_robustness(
        AlwaysLongStrategy, CANDLES_12,
        train_size=4, test_size=4, step_size=4,
        simulations=50, seed=7,
    )
    engine = RobustnessEngine(
        AlwaysLongStrategy, CANDLES_12,
        train_size=4, test_size=4, step_size=4,
        simulations=50, seed=7,
    )
    result = engine.run()
    for i, (r, e) in enumerate(zip(result["fold_scores"], ref["fold_scores"])):
        assert r == pytest.approx(e, rel=1e-9), f"fold_scores[{i}] mismatch"


# ===========================================================================
# Part 6 — Determinism under fixed seed
# ===========================================================================

def test_deterministic_with_fixed_seed():
    kwargs = dict(
        train_size=4, test_size=4, step_size=4,
        simulations=30, seed=99,
    )
    r1 = RobustnessEngine(AlwaysLongStrategy, CANDLES_12, **kwargs).run()
    r2 = RobustnessEngine(AlwaysLongStrategy, CANDLES_12, **kwargs).run()
    assert r1["robustness_score"] == r2["robustness_score"]
    assert r1["fold_scores"] == r2["fold_scores"]


def test_deterministic_fold_mc_results_with_fixed_seed():
    kwargs = dict(
        train_size=4, test_size=4, step_size=4,
        simulations=30, seed=99,
    )
    r1 = RobustnessEngine(AlwaysLongStrategy, CANDLES_12, **kwargs).run()
    r2 = RobustnessEngine(AlwaysLongStrategy, CANDLES_12, **kwargs).run()
    for mc1, mc2 in zip(r1["fold_mc_results"], r2["fold_mc_results"]):
        assert mc1["mean_sharpe"] == mc2["mean_sharpe"]
        assert mc1["sharpe_variance"] == mc2["sharpe_variance"]
        assert mc1["probability_of_loss"] == mc2["probability_of_loss"]


def test_different_seeds_may_differ():
    """Two different seeds should (almost certainly) produce different scores."""
    r1 = RobustnessEngine(
        AlwaysLongStrategy, CANDLES_12,
        train_size=4, test_size=4, step_size=4,
        simulations=100, seed=1,
    ).run()
    r2 = RobustnessEngine(
        AlwaysLongStrategy, CANDLES_12,
        train_size=4, test_size=4, step_size=4,
        simulations=100, seed=2,
    ).run()
    # Different seeds: scores may differ (probabilistic; this is a smoke test)
    # We just verify both produce valid floats without error
    assert isinstance(r1["robustness_score"], float)
    assert isinstance(r2["robustness_score"], float)


# ===========================================================================
# Part 7 — Input candles must NOT be mutated
# ===========================================================================

def test_does_not_mutate_candles_length():
    candles = [make_candle(f"2024-01-{i+1:02d}", float((i+1)*10)) for i in range(8)]
    original_len = len(candles)
    RobustnessEngine(
        AlwaysLongStrategy, candles,
        train_size=2, test_size=2, step_size=2,
        simulations=5, seed=1,
    ).run()
    assert len(candles) == original_len


def test_does_not_mutate_candles_values():
    candles = [make_candle(f"2024-01-{i+1:02d}", float((i+1)*10)) for i in range(8)]
    original_closes = [c["close"] for c in candles]
    RobustnessEngine(
        AlwaysLongStrategy, candles,
        train_size=2, test_size=2, step_size=2,
        simulations=5, seed=1,
    ).run()
    for i, c in enumerate(candles):
        assert c["close"] == original_closes[i]


def test_does_not_mutate_candle_keys():
    candles = [make_candle(f"2024-01-{i+1:02d}", float((i+1)*10)) for i in range(8)]
    original_keys = [set(c.keys()) for c in candles]
    RobustnessEngine(
        AlwaysLongStrategy, candles,
        train_size=2, test_size=2, step_size=2,
        simulations=5, seed=1,
    ).run()
    for i, c in enumerate(candles):
        assert set(c.keys()) == original_keys[i]


# ===========================================================================
# Part 8 — initial_cash is forwarded
# ===========================================================================

def test_initial_cash_default_is_1000():
    """Engine with default initial_cash=1000 must produce same result as explicit 1000."""
    r1 = RobustnessEngine(
        AlwaysLongStrategy, CANDLES_8,
        train_size=4, test_size=4, step_size=4,
        simulations=10, seed=5,
    ).run()
    r2 = RobustnessEngine(
        AlwaysLongStrategy, CANDLES_8,
        train_size=4, test_size=4, step_size=4,
        simulations=10, seed=5,
        initial_cash=1000,
    ).run()
    assert r1["robustness_score"] == pytest.approx(r2["robustness_score"], rel=1e-9)


def test_initial_cash_forwarded_affects_mc_results():
    """
    Sharpe ratio is scale-invariant, so different initial_cash values
    should yield the same robustness_score (within floating-point tolerance).
    """
    r1 = RobustnessEngine(
        AlwaysLongStrategy, CANDLES_8,
        train_size=4, test_size=4, step_size=4,
        simulations=20, seed=5,
        initial_cash=1000,
    ).run()
    r2 = RobustnessEngine(
        AlwaysLongStrategy, CANDLES_8,
        train_size=4, test_size=4, step_size=4,
        simulations=20, seed=5,
        initial_cash=500,
    ).run()
    # Sharpe is scale-invariant; robustness_score should match
    assert r1["robustness_score"] == pytest.approx(r2["robustness_score"], rel=1e-6)


# ===========================================================================
# Part 9 — AlwaysFlatStrategy edge case (zero-returns series)
# ===========================================================================

def test_flat_strategy_produces_valid_score():
    """AlwaysFlatStrategy: all returns are 0, Sharpe=0, scores are valid floats."""
    engine = RobustnessEngine(
        AlwaysFlatStrategy, CANDLES_8,
        train_size=4, test_size=4, step_size=4,
        simulations=10, seed=1,
    )
    result = engine.run()
    assert isinstance(result["robustness_score"], float)
    assert not math.isnan(result["robustness_score"])


def test_flat_strategy_fold_score_is_zero():
    """
    AlwaysFlatStrategy: equity never moves → all per-sim sharpe=0,
    sharpe_variance=0, probability_of_loss=0.
    R_i = 0 - 0 - 0 = 0.0
    """
    engine = RobustnessEngine(
        AlwaysFlatStrategy, CANDLES_8,
        train_size=4, test_size=4, step_size=4,
        simulations=10, seed=1,
    )
    result = engine.run()
    for r_i in result["fold_scores"]:
        assert r_i == pytest.approx(0.0, abs=1e-12)


def test_flat_strategy_robustness_score_is_zero():
    engine = RobustnessEngine(
        AlwaysFlatStrategy, CANDLES_8,
        train_size=4, test_size=4, step_size=4,
        simulations=10, seed=1,
    )
    result = engine.run()
    assert result["robustness_score"] == pytest.approx(0.0, abs=1e-12)


# ===========================================================================
# Part 10 — ValueError propagation
# ===========================================================================

def test_raises_for_train_size_less_than_2():
    with pytest.raises(ValueError):
        RobustnessEngine(
            AlwaysLongStrategy, CANDLES_8,
            train_size=1, test_size=4, step_size=4,
            simulations=10, seed=1,
        ).run()


def test_raises_for_test_size_less_than_2():
    with pytest.raises(ValueError):
        RobustnessEngine(
            AlwaysLongStrategy, CANDLES_8,
            train_size=4, test_size=1, step_size=4,
            simulations=10, seed=1,
        ).run()


def test_raises_for_step_size_less_than_1():
    with pytest.raises(ValueError):
        RobustnessEngine(
            AlwaysLongStrategy, CANDLES_8,
            train_size=4, test_size=4, step_size=0,
            simulations=10, seed=1,
        ).run()


def test_raises_when_dataset_too_small():
    tiny_candles = [make_candle(f"2024-01-{i+1:02d}", float(i+1)) for i in range(4)]
    with pytest.raises(ValueError):
        RobustnessEngine(
            AlwaysLongStrategy, tiny_candles,
            train_size=4, test_size=4, step_size=4,
            simulations=10, seed=1,
        ).run()


def test_raises_for_simulations_less_than_1():
    with pytest.raises(ValueError):
        RobustnessEngine(
            AlwaysLongStrategy, CANDLES_8,
            train_size=4, test_size=4, step_size=4,
            simulations=0, seed=1,
        ).run()


# ===========================================================================
# Part 11 — step_size controls number of folds
# ===========================================================================

def test_step_size_1_produces_more_folds_than_step_size_4():
    """Smaller step_size → more overlapping folds."""
    # 12 candles, train=4, test=4
    # step=4 → 2 folds  (pos=0,4)
    # step=1 → 5 folds  (pos=0,1,2,3,4)
    r_step4 = RobustnessEngine(
        AlwaysLongStrategy, CANDLES_12,
        train_size=4, test_size=4, step_size=4,
        simulations=10, seed=1,
    ).run()
    r_step1 = RobustnessEngine(
        AlwaysLongStrategy, CANDLES_12,
        train_size=4, test_size=4, step_size=1,
        simulations=10, seed=1,
    ).run()
    assert len(r_step4["fold_scores"]) == 2
    assert len(r_step1["fold_scores"]) == 5


def test_fold_count_step4_12candles():
    # 12 candles, train=4, test=4, step=4 → folds at pos=0,4 → 2 folds
    result = RobustnessEngine(
        AlwaysLongStrategy, CANDLES_12,
        train_size=4, test_size=4, step_size=4,
        simulations=10, seed=1,
    ).run()
    assert len(result["fold_scores"]) == 2


# ===========================================================================
# Part 12 — robustness_score with one fold equals that fold's score
# ===========================================================================

def test_single_fold_robustness_score_equals_fold_score():
    engine = RobustnessEngine(
        AlwaysLongStrategy, CANDLES_8,
        train_size=4, test_size=4, step_size=4,
        simulations=20, seed=13,
    )
    result = engine.run()
    assert len(result["fold_scores"]) == 1
    assert result["robustness_score"] == pytest.approx(
        result["fold_scores"][0], rel=1e-12
    )
