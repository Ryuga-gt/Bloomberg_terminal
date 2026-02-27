"""
Tests for execution.capital_allocator.CapitalAllocator

Contract
--------
CapitalAllocator(mode: str = "equal")
    mode must be "equal", "sharpe", or "robustness" → ValueError otherwise

    compute_weights(ranking_results: list[dict]) -> dict[str, float]
        ranking_results must not be empty → ValueError
        Weights sum to 1.0 (within 1e-9)
        Input not mutated
        Deterministic

Modes
-----
equal      : w_i = 1/N for all i
sharpe     : w_i = sharpe_i / sum(positive sharpes); fallback equal if all <= 0
robustness : w_i = robustness_i / sum(positive robustness); fallback equal if all <= 0
"""

import pytest

from execution.capital_allocator import CapitalAllocator


# ---------------------------------------------------------------------------
# Helpers to build minimal ranking_results entries
# ---------------------------------------------------------------------------

def make_result(name: str, sharpe: float, robustness: float) -> dict:
    return {
        "strategy_name": name,
        "backtest": {
            "sharpe_ratio":    sharpe,
            "calmar_ratio":    0.0,
            "return_pct":      0.0,
            "max_drawdown_pct": 0.0,
        },
        "robustness": robustness,
        "composite_score": 0.0,
        "rank": 1,
    }


# ===========================================================================
# Part 1 — Validation: mode
# ===========================================================================

def test_invalid_mode_raises():
    with pytest.raises(ValueError):
        CapitalAllocator(mode="momentum")


def test_invalid_mode_empty_string_raises():
    with pytest.raises(ValueError):
        CapitalAllocator(mode="")


def test_equal_mode_valid():
    a = CapitalAllocator(mode="equal")
    assert a.mode == "equal"


def test_sharpe_mode_valid():
    a = CapitalAllocator(mode="sharpe")
    assert a.mode == "sharpe"


def test_robustness_mode_valid():
    a = CapitalAllocator(mode="robustness")
    assert a.mode == "robustness"


def test_default_mode_is_equal():
    a = CapitalAllocator()
    assert a.mode == "equal"


# ===========================================================================
# Part 2 — Validation: empty ranking_results
# ===========================================================================

def test_empty_ranking_results_raises():
    a = CapitalAllocator()
    with pytest.raises(ValueError):
        a.compute_weights([])


# ===========================================================================
# Part 3 — Equal weighting
# ===========================================================================

def test_equal_two_strategies():
    results = [
        make_result("A", sharpe=1.0, robustness=0.5),
        make_result("B", sharpe=2.0, robustness=0.3),
    ]
    weights = CapitalAllocator(mode="equal").compute_weights(results)
    assert weights["A"] == pytest.approx(0.5)
    assert weights["B"] == pytest.approx(0.5)


def test_equal_three_strategies():
    results = [make_result(f"S{i}", sharpe=float(i), robustness=float(i))
               for i in range(1, 4)]
    weights = CapitalAllocator(mode="equal").compute_weights(results)
    for name in ["S1", "S2", "S3"]:
        assert weights[name] == pytest.approx(1.0 / 3)


def test_equal_five_strategies():
    results = [make_result(f"S{i}", sharpe=1.0, robustness=1.0)
               for i in range(5)]
    weights = CapitalAllocator(mode="equal").compute_weights(results)
    for r in results:
        assert weights[r["strategy_name"]] == pytest.approx(0.2)


def test_equal_single_strategy_weight_is_one():
    results = [make_result("Solo", sharpe=1.0, robustness=1.0)]
    weights = CapitalAllocator(mode="equal").compute_weights(results)
    assert weights["Solo"] == pytest.approx(1.0)


# ===========================================================================
# Part 4 — Sharpe weighting: basic proportional
# ===========================================================================

def test_sharpe_two_strategies_proportional():
    """sharpe A=1, B=3 → w_A=0.25, w_B=0.75."""
    results = [
        make_result("A", sharpe=1.0, robustness=0.0),
        make_result("B", sharpe=3.0, robustness=0.0),
    ]
    weights = CapitalAllocator(mode="sharpe").compute_weights(results)
    assert weights["A"] == pytest.approx(0.25)
    assert weights["B"] == pytest.approx(0.75)


def test_sharpe_equal_sharpes_equal_weights():
    results = [
        make_result("A", sharpe=2.0, robustness=0.0),
        make_result("B", sharpe=2.0, robustness=0.0),
    ]
    weights = CapitalAllocator(mode="sharpe").compute_weights(results)
    assert weights["A"] == pytest.approx(0.5)
    assert weights["B"] == pytest.approx(0.5)


def test_sharpe_single_positive_gets_all_weight():
    """Only A has positive sharpe → A gets weight 1.0, B gets 0.0."""
    results = [
        make_result("A", sharpe=2.0, robustness=0.0),
        make_result("B", sharpe=-1.0, robustness=0.0),
    ]
    weights = CapitalAllocator(mode="sharpe").compute_weights(results)
    assert weights["A"] == pytest.approx(1.0)
    assert weights["B"] == pytest.approx(0.0)


def test_sharpe_zero_sharpe_excluded():
    """sharpe=0 is not > 0, so excluded from weighting."""
    results = [
        make_result("A", sharpe=0.0, robustness=0.0),
        make_result("B", sharpe=4.0, robustness=0.0),
    ]
    weights = CapitalAllocator(mode="sharpe").compute_weights(results)
    assert weights["A"] == pytest.approx(0.0)
    assert weights["B"] == pytest.approx(1.0)


# ===========================================================================
# Part 5 — Sharpe fallback when all <= 0
# ===========================================================================

def test_sharpe_all_negative_fallback_equal():
    results = [
        make_result("A", sharpe=-1.0, robustness=0.0),
        make_result("B", sharpe=-2.0, robustness=0.0),
    ]
    weights = CapitalAllocator(mode="sharpe").compute_weights(results)
    assert weights["A"] == pytest.approx(0.5)
    assert weights["B"] == pytest.approx(0.5)


def test_sharpe_all_zero_fallback_equal():
    results = [
        make_result("A", sharpe=0.0, robustness=0.0),
        make_result("B", sharpe=0.0, robustness=0.0),
        make_result("C", sharpe=0.0, robustness=0.0),
    ]
    weights = CapitalAllocator(mode="sharpe").compute_weights(results)
    for name in ["A", "B", "C"]:
        assert weights[name] == pytest.approx(1.0 / 3)


# ===========================================================================
# Part 6 — Robustness weighting: basic proportional
# ===========================================================================

def test_robustness_two_strategies_proportional():
    """robustness A=1, B=4 → w_A=0.2, w_B=0.8."""
    results = [
        make_result("A", sharpe=0.0, robustness=1.0),
        make_result("B", sharpe=0.0, robustness=4.0),
    ]
    weights = CapitalAllocator(mode="robustness").compute_weights(results)
    assert weights["A"] == pytest.approx(0.2)
    assert weights["B"] == pytest.approx(0.8)


def test_robustness_equal_scores_equal_weights():
    results = [
        make_result("A", sharpe=0.0, robustness=3.0),
        make_result("B", sharpe=0.0, robustness=3.0),
    ]
    weights = CapitalAllocator(mode="robustness").compute_weights(results)
    assert weights["A"] == pytest.approx(0.5)
    assert weights["B"] == pytest.approx(0.5)


def test_robustness_single_positive_gets_all_weight():
    results = [
        make_result("A", sharpe=0.0, robustness=5.0),
        make_result("B", sharpe=0.0, robustness=-1.0),
    ]
    weights = CapitalAllocator(mode="robustness").compute_weights(results)
    assert weights["A"] == pytest.approx(1.0)
    assert weights["B"] == pytest.approx(0.0)


def test_robustness_zero_excluded():
    results = [
        make_result("A", sharpe=0.0, robustness=0.0),
        make_result("B", sharpe=0.0, robustness=2.0),
    ]
    weights = CapitalAllocator(mode="robustness").compute_weights(results)
    assert weights["A"] == pytest.approx(0.0)
    assert weights["B"] == pytest.approx(1.0)


# ===========================================================================
# Part 7 — Robustness fallback when all <= 0
# ===========================================================================

def test_robustness_all_negative_fallback_equal():
    results = [
        make_result("A", sharpe=0.0, robustness=-0.5),
        make_result("B", sharpe=0.0, robustness=-1.0),
    ]
    weights = CapitalAllocator(mode="robustness").compute_weights(results)
    assert weights["A"] == pytest.approx(0.5)
    assert weights["B"] == pytest.approx(0.5)


def test_robustness_all_zero_fallback_equal():
    results = [
        make_result("A", sharpe=0.0, robustness=0.0),
        make_result("B", sharpe=0.0, robustness=0.0),
    ]
    weights = CapitalAllocator(mode="robustness").compute_weights(results)
    assert weights["A"] == pytest.approx(0.5)
    assert weights["B"] == pytest.approx(0.5)


# ===========================================================================
# Part 8 — Weights sum to 1.0
# ===========================================================================

def test_equal_weights_sum_to_one_two():
    results = [make_result("A", 1.0, 1.0), make_result("B", 2.0, 2.0)]
    weights = CapitalAllocator(mode="equal").compute_weights(results)
    assert sum(weights.values()) == pytest.approx(1.0, abs=1e-9)


def test_sharpe_weights_sum_to_one():
    results = [
        make_result("A", sharpe=1.0, robustness=0.0),
        make_result("B", sharpe=3.0, robustness=0.0),
        make_result("C", sharpe=2.0, robustness=0.0),
    ]
    weights = CapitalAllocator(mode="sharpe").compute_weights(results)
    assert sum(weights.values()) == pytest.approx(1.0, abs=1e-9)


def test_robustness_weights_sum_to_one():
    results = [
        make_result("A", sharpe=0.0, robustness=1.0),
        make_result("B", sharpe=0.0, robustness=2.0),
        make_result("C", sharpe=0.0, robustness=3.0),
    ]
    weights = CapitalAllocator(mode="robustness").compute_weights(results)
    assert sum(weights.values()) == pytest.approx(1.0, abs=1e-9)


def test_sharpe_fallback_weights_sum_to_one():
    results = [
        make_result("A", sharpe=-1.0, robustness=0.0),
        make_result("B", sharpe=-2.0, robustness=0.0),
        make_result("C", sharpe=-3.0, robustness=0.0),
    ]
    weights = CapitalAllocator(mode="sharpe").compute_weights(results)
    assert sum(weights.values()) == pytest.approx(1.0, abs=1e-9)


# ===========================================================================
# Part 9 — Determinism
# ===========================================================================

def test_deterministic_equal():
    results = [make_result("A", 1.0, 1.0), make_result("B", 2.0, 2.0)]
    a = CapitalAllocator(mode="equal")
    w1 = a.compute_weights(results)
    w2 = a.compute_weights(results)
    assert w1 == w2


def test_deterministic_sharpe():
    results = [make_result("A", 1.0, 0.0), make_result("B", 3.0, 0.0)]
    a = CapitalAllocator(mode="sharpe")
    w1 = a.compute_weights(results)
    w2 = a.compute_weights(results)
    assert w1 == w2


def test_deterministic_robustness():
    results = [make_result("A", 0.0, 1.0), make_result("B", 0.0, 4.0)]
    a = CapitalAllocator(mode="robustness")
    w1 = a.compute_weights(results)
    w2 = a.compute_weights(results)
    assert w1 == w2


# ===========================================================================
# Part 10 — No mutation of input
# ===========================================================================

def test_compute_weights_does_not_mutate_input():
    results = [
        make_result("A", sharpe=1.0, robustness=0.5),
        make_result("B", sharpe=2.0, robustness=0.3),
    ]
    import copy
    originals = copy.deepcopy(results)
    CapitalAllocator(mode="sharpe").compute_weights(results)
    assert results == originals


# ===========================================================================
# Part 11 — Mixed negative and positive values
# ===========================================================================

def test_sharpe_mixed_only_positive_weighted():
    """A=2, B=-1, C=3 → only A and C weighted: w_A=2/5, w_C=3/5, w_B=0."""
    results = [
        make_result("A", sharpe=2.0, robustness=0.0),
        make_result("B", sharpe=-1.0, robustness=0.0),
        make_result("C", sharpe=3.0, robustness=0.0),
    ]
    weights = CapitalAllocator(mode="sharpe").compute_weights(results)
    assert weights["A"] == pytest.approx(2.0 / 5.0)
    assert weights["B"] == pytest.approx(0.0)
    assert weights["C"] == pytest.approx(3.0 / 5.0)


def test_robustness_mixed_only_positive_weighted():
    """A=1, B=-0.5, C=4 → w_A=1/5, w_B=0, w_C=4/5."""
    results = [
        make_result("A", sharpe=0.0, robustness=1.0),
        make_result("B", sharpe=0.0, robustness=-0.5),
        make_result("C", sharpe=0.0, robustness=4.0),
    ]
    weights = CapitalAllocator(mode="robustness").compute_weights(results)
    assert weights["A"] == pytest.approx(1.0 / 5.0)
    assert weights["B"] == pytest.approx(0.0)
    assert weights["C"] == pytest.approx(4.0 / 5.0)


# ===========================================================================
# Part 12 — Return type
# ===========================================================================

def test_compute_weights_returns_dict():
    results = [make_result("A", 1.0, 1.0)]
    weights = CapitalAllocator().compute_weights(results)
    assert isinstance(weights, dict)


def test_compute_weights_keys_match_strategy_names():
    results = [
        make_result("Alpha", 1.0, 1.0),
        make_result("Beta", 2.0, 2.0),
    ]
    weights = CapitalAllocator().compute_weights(results)
    assert set(weights.keys()) == {"Alpha", "Beta"}
