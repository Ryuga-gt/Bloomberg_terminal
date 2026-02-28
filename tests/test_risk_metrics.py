"""
Tests for analytics.risk_metrics.RiskMetrics
"""

import math
import pytest

from analytics.risk_metrics import RiskMetrics


# ===========================================================================
# Part 1 — Validation
# ===========================================================================

def test_too_short_raises():
    with pytest.raises(ValueError):
        RiskMetrics([1000.0])


def test_empty_raises():
    with pytest.raises(ValueError):
        RiskMetrics([])


def test_non_positive_value_raises():
    with pytest.raises(ValueError):
        RiskMetrics([1000.0, 0.0, 1100.0])


def test_negative_value_raises():
    with pytest.raises(ValueError):
        RiskMetrics([1000.0, -100.0])


def test_valid_two_element_curve():
    rm = RiskMetrics([1000.0, 1100.0])
    assert rm is not None


# ===========================================================================
# Part 2 — total_return
# ===========================================================================

def test_total_return_positive():
    rm = RiskMetrics([1000.0, 1100.0])
    assert rm.total_return() == pytest.approx(0.1)


def test_total_return_negative():
    rm = RiskMetrics([1000.0, 900.0])
    assert rm.total_return() == pytest.approx(-0.1)


def test_total_return_zero():
    rm = RiskMetrics([1000.0, 1000.0])
    assert rm.total_return() == pytest.approx(0.0)


def test_total_return_multi_step():
    """1000 → 1100 → 1210 → total return = 21%."""
    rm = RiskMetrics([1000.0, 1100.0, 1210.0])
    assert rm.total_return() == pytest.approx(0.21)


# ===========================================================================
# Part 3 — volatility
# ===========================================================================

def test_volatility_flat_curve_is_zero():
    """Flat curve → all returns = 0 → vol = 0."""
    rm = RiskMetrics([1000.0, 1000.0, 1000.0, 1000.0])
    assert rm.volatility() == pytest.approx(0.0)


def test_volatility_positive():
    rm = RiskMetrics([1000.0, 1100.0, 1050.0, 1150.0])
    assert rm.volatility() > 0


def test_volatility_symmetric_returns():
    """Returns +10%, -10%, +10%, -10% → non-zero vol."""
    curve = [1000.0]
    for _ in range(4):
        curve.append(curve[-1] * 1.1)
        curve.append(curve[-1] * 0.9)
    rm = RiskMetrics(curve)
    assert rm.volatility() > 0


# ===========================================================================
# Part 4 — sharpe
# ===========================================================================

def test_sharpe_zero_volatility_returns_zero():
    """Flat curve → vol = 0 → sharpe = 0."""
    rm = RiskMetrics([1000.0, 1000.0, 1000.0])
    assert rm.sharpe() == pytest.approx(0.0)


def test_sharpe_positive_for_rising_curve():
    rm = RiskMetrics([1000.0, 1010.0, 1020.0, 1030.0, 1040.0])
    assert rm.sharpe() > 0


def test_sharpe_negative_for_falling_curve():
    rm = RiskMetrics([1000.0, 990.0, 980.0, 970.0, 960.0])
    assert rm.sharpe() < 0


# ===========================================================================
# Part 5 — downside_deviation
# ===========================================================================

def test_downside_deviation_no_negative_returns_is_zero():
    """Monotonically rising → no negative returns → dd = 0."""
    rm = RiskMetrics([1000.0, 1010.0, 1020.0, 1030.0])
    assert rm.downside_deviation() == pytest.approx(0.0)


def test_downside_deviation_positive_when_negative_returns_exist():
    # Two negative returns needed for sample std to be non-zero
    rm = RiskMetrics([1000.0, 1100.0, 1050.0, 1150.0, 1080.0, 1200.0])
    assert rm.downside_deviation() > 0


# ===========================================================================
# Part 6 — sortino_ratio
# ===========================================================================

def test_sortino_zero_downside_returns_zero():
    rm = RiskMetrics([1000.0, 1010.0, 1020.0, 1030.0])
    assert rm.sortino_ratio() == pytest.approx(0.0)


def test_sortino_positive_for_rising_with_some_dips():
    rm = RiskMetrics([1000.0, 1100.0, 1050.0, 1200.0, 1180.0, 1300.0])
    # Mean return positive, downside deviation > 0 → sortino > 0
    assert rm.sortino_ratio() > 0


# ===========================================================================
# Part 7 — determinism
# ===========================================================================

def test_deterministic():
    curve = [1000.0, 1100.0, 1050.0, 1200.0]
    rm1 = RiskMetrics(curve)
    rm2 = RiskMetrics(curve)
    assert rm1.sharpe() == pytest.approx(rm2.sharpe())
    assert rm1.volatility() == pytest.approx(rm2.volatility())


# ===========================================================================
# Part 8 — no mutation
# ===========================================================================

def test_no_mutation_of_input():
    curve = [1000.0, 1100.0, 1050.0]
    original = list(curve)
    RiskMetrics(curve)
    assert curve == original
