"""
Tests for analytics.var_engine.ValueAtRisk
"""

import math
import pytest

from analytics.var_engine import ValueAtRisk


# ===========================================================================
# Part 1 — Validation
# ===========================================================================

def test_too_short_raises():
    with pytest.raises(ValueError):
        ValueAtRisk([0.01])


def test_empty_raises():
    with pytest.raises(ValueError):
        ValueAtRisk([])


def test_invalid_confidence_zero_raises_hist():
    var = ValueAtRisk([0.01, 0.02, -0.01])
    with pytest.raises(ValueError):
        var.historical_var(0.0)


def test_invalid_confidence_one_raises_hist():
    var = ValueAtRisk([0.01, 0.02, -0.01])
    with pytest.raises(ValueError):
        var.historical_var(1.0)


def test_invalid_confidence_zero_raises_param():
    var = ValueAtRisk([0.01, 0.02, -0.01])
    with pytest.raises(ValueError):
        var.parametric_var(0.0)


def test_invalid_confidence_one_raises_param():
    var = ValueAtRisk([0.01, 0.02, -0.01])
    with pytest.raises(ValueError):
        var.parametric_var(1.0)


# ===========================================================================
# Part 2 — Historical VaR: known dataset
# ===========================================================================

def test_historical_var_known_dataset():
    """
    10 returns: [-0.05, -0.04, -0.03, -0.02, -0.01, 0.01, 0.02, 0.03, 0.04, 0.05]
    95% VaR → 5th percentile → index floor(0.05 * 10) = 0 → -0.05
    """
    returns = [-0.05, -0.04, -0.03, -0.02, -0.01, 0.01, 0.02, 0.03, 0.04, 0.05]
    var = ValueAtRisk(returns)
    result = var.historical_var(0.95)
    assert result == pytest.approx(-0.05)


def test_historical_var_99():
    """
    10 returns sorted: [-0.05, ..., 0.05]
    99% VaR → 1st percentile → index floor(0.01 * 10) = 0 → -0.05
    """
    returns = [-0.05, -0.04, -0.03, -0.02, -0.01, 0.01, 0.02, 0.03, 0.04, 0.05]
    var = ValueAtRisk(returns)
    result = var.historical_var(0.99)
    assert result == pytest.approx(-0.05)


def test_historical_var_all_positive_returns():
    """All positive returns → VaR is the smallest positive return."""
    returns = [0.01, 0.02, 0.03, 0.04, 0.05]
    var = ValueAtRisk(returns)
    result = var.historical_var(0.95)
    assert result == pytest.approx(0.01)


def test_historical_var_is_negative_for_mixed_returns():
    returns = [0.05, -0.03, 0.02, -0.01, 0.04, -0.02, 0.01, 0.03, -0.04, 0.06]
    var = ValueAtRisk(returns)
    result = var.historical_var(0.95)
    assert result < 0


# ===========================================================================
# Part 3 — Parametric VaR
# ===========================================================================

def test_parametric_var_negative_for_normal_returns():
    """For a typical return distribution, 95% VaR should be negative."""
    returns = [0.01, -0.02, 0.03, -0.01, 0.02, -0.03, 0.01, -0.02, 0.02, -0.01]
    var = ValueAtRisk(returns)
    result = var.parametric_var(0.95)
    assert result < 0


def test_parametric_var_95_less_than_99():
    """Higher confidence → more extreme (more negative) VaR."""
    returns = [0.01, -0.02, 0.03, -0.01, 0.02, -0.03, 0.01, -0.02, 0.02, -0.01]
    var = ValueAtRisk(returns)
    var95 = var.parametric_var(0.95)
    var99 = var.parametric_var(0.99)
    assert var99 <= var95


def test_parametric_var_constant_returns_equals_mean():
    """Constant returns → sigma=0 → VaR = mu + z*0 = mu."""
    returns = [0.01] * 10
    var = ValueAtRisk(returns)
    result = var.parametric_var(0.95)
    assert result == pytest.approx(0.01)


# ===========================================================================
# Part 4 — Parametric approximates historical for normal returns
# ===========================================================================

def test_parametric_close_to_historical_for_large_normal_sample():
    """
    For a large normally distributed sample, parametric and historical
    VaR should be in the same ballpark (within 50% of each other).
    """
    import random
    rng = random.Random(42)
    # Generate ~200 normally distributed returns (mu=0.001, sigma=0.02)
    returns = [rng.gauss(0.001, 0.02) for _ in range(200)]
    var = ValueAtRisk(returns)
    hist = var.historical_var(0.95)
    param = var.parametric_var(0.95)
    # Both should be negative and within 50% of each other
    assert hist < 0
    assert param < 0
    assert abs(hist - param) < abs(hist) * 0.5


# ===========================================================================
# Part 5 — Determinism
# ===========================================================================

def test_deterministic():
    returns = [0.01, -0.02, 0.03, -0.01, 0.02]
    var = ValueAtRisk(returns)
    r1 = var.historical_var(0.95)
    r2 = var.historical_var(0.95)
    assert r1 == pytest.approx(r2)


# ===========================================================================
# Part 6 — No mutation
# ===========================================================================

def test_no_mutation():
    returns = [0.01, -0.02, 0.03]
    original = list(returns)
    ValueAtRisk(returns)
    assert returns == original
