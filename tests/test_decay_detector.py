"""
Tests for execution.decay_detector.PerformanceDecayDetector

Contract
--------
PerformanceDecayDetector(threshold: float, metric: str = "sharpe")
    metric must be "sharpe" or "robustness" → ValueError otherwise

    is_decayed(ranking_result: dict) -> bool
        Returns True when metric_value < threshold
        Does not mutate input
        Deterministic
"""

import pytest
import copy

from execution.decay_detector import PerformanceDecayDetector


# ---------------------------------------------------------------------------
# Helper to build minimal ranking_result entries
# ---------------------------------------------------------------------------

def make_result(sharpe: float, robustness: float) -> dict:
    return {
        "strategy_name": "TestStrategy",
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
# Part 1 — Validation: metric
# ===========================================================================

def test_invalid_metric_raises():
    with pytest.raises(ValueError):
        PerformanceDecayDetector(threshold=0.5, metric="calmar")


def test_invalid_metric_empty_raises():
    with pytest.raises(ValueError):
        PerformanceDecayDetector(threshold=0.5, metric="")


def test_sharpe_metric_valid():
    d = PerformanceDecayDetector(threshold=0.5, metric="sharpe")
    assert d.metric == "sharpe"


def test_robustness_metric_valid():
    d = PerformanceDecayDetector(threshold=0.5, metric="robustness")
    assert d.metric == "robustness"


def test_default_metric_is_sharpe():
    d = PerformanceDecayDetector(threshold=0.5)
    assert d.metric == "sharpe"


def test_threshold_stored():
    d = PerformanceDecayDetector(threshold=1.5)
    assert d.threshold == pytest.approx(1.5)


# ===========================================================================
# Part 2 — Sharpe detection
# ===========================================================================

def test_sharpe_below_threshold_is_decayed():
    d = PerformanceDecayDetector(threshold=1.0, metric="sharpe")
    result = make_result(sharpe=0.5, robustness=2.0)
    assert d.is_decayed(result) is True


def test_sharpe_above_threshold_not_decayed():
    d = PerformanceDecayDetector(threshold=1.0, metric="sharpe")
    result = make_result(sharpe=1.5, robustness=2.0)
    assert d.is_decayed(result) is False


def test_sharpe_negative_below_threshold_is_decayed():
    d = PerformanceDecayDetector(threshold=0.0, metric="sharpe")
    result = make_result(sharpe=-0.5, robustness=2.0)
    assert d.is_decayed(result) is True


def test_sharpe_zero_below_positive_threshold_is_decayed():
    d = PerformanceDecayDetector(threshold=0.1, metric="sharpe")
    result = make_result(sharpe=0.0, robustness=2.0)
    assert d.is_decayed(result) is True


# ===========================================================================
# Part 3 — Sharpe equality edge case
# ===========================================================================

def test_sharpe_equal_to_threshold_not_decayed():
    """Decay rule is strict: metric < threshold. Equal is NOT decayed."""
    d = PerformanceDecayDetector(threshold=1.0, metric="sharpe")
    result = make_result(sharpe=1.0, robustness=2.0)
    assert d.is_decayed(result) is False


# ===========================================================================
# Part 4 — Robustness detection
# ===========================================================================

def test_robustness_below_threshold_is_decayed():
    d = PerformanceDecayDetector(threshold=0.5, metric="robustness")
    result = make_result(sharpe=2.0, robustness=0.3)
    assert d.is_decayed(result) is True


def test_robustness_above_threshold_not_decayed():
    d = PerformanceDecayDetector(threshold=0.5, metric="robustness")
    result = make_result(sharpe=2.0, robustness=0.8)
    assert d.is_decayed(result) is False


def test_robustness_negative_below_zero_threshold_is_decayed():
    d = PerformanceDecayDetector(threshold=0.0, metric="robustness")
    result = make_result(sharpe=2.0, robustness=-0.1)
    assert d.is_decayed(result) is True


def test_robustness_equal_to_threshold_not_decayed():
    d = PerformanceDecayDetector(threshold=0.5, metric="robustness")
    result = make_result(sharpe=2.0, robustness=0.5)
    assert d.is_decayed(result) is False


# ===========================================================================
# Part 5 — Negative threshold allowed
# ===========================================================================

def test_negative_threshold_sharpe_above_is_not_decayed():
    d = PerformanceDecayDetector(threshold=-1.0, metric="sharpe")
    result = make_result(sharpe=-0.5, robustness=0.0)
    assert d.is_decayed(result) is False


def test_negative_threshold_sharpe_below_is_decayed():
    d = PerformanceDecayDetector(threshold=-1.0, metric="sharpe")
    result = make_result(sharpe=-2.0, robustness=0.0)
    assert d.is_decayed(result) is True


# ===========================================================================
# Part 6 — Deterministic
# ===========================================================================

def test_deterministic_same_result_same_output():
    d = PerformanceDecayDetector(threshold=1.0, metric="sharpe")
    result = make_result(sharpe=0.5, robustness=2.0)
    r1 = d.is_decayed(result)
    r2 = d.is_decayed(result)
    assert r1 == r2


# ===========================================================================
# Part 7 — No mutation of input
# ===========================================================================

def test_is_decayed_does_not_mutate_input():
    d = PerformanceDecayDetector(threshold=1.0, metric="sharpe")
    result = make_result(sharpe=0.5, robustness=2.0)
    original = copy.deepcopy(result)
    d.is_decayed(result)
    assert result == original
