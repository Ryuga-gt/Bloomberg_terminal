"""
Tests for analytics.rolling_metrics.RollingMetrics
"""

import pytest

from analytics.rolling_metrics import RollingMetrics


# ===========================================================================
# Part 1 — Validation
# ===========================================================================

def test_empty_curve_raises():
    with pytest.raises(ValueError):
        RollingMetrics([])


def test_non_positive_raises():
    with pytest.raises(ValueError):
        RollingMetrics([1000.0, 0.0])


def test_window_less_than_2_raises_vol():
    rm = RollingMetrics([1000.0, 1100.0, 1200.0])
    with pytest.raises(ValueError):
        rm.rolling_volatility(1)


def test_window_less_than_2_raises_sharpe():
    rm = RollingMetrics([1000.0, 1100.0, 1200.0])
    with pytest.raises(ValueError):
        rm.rolling_sharpe(1)


def test_window_less_than_2_raises_mdd():
    rm = RollingMetrics([1000.0, 1100.0, 1200.0])
    with pytest.raises(ValueError):
        rm.rolling_max_drawdown(1)


# ===========================================================================
# Part 2 — Return length matches equity curve
# ===========================================================================

def test_rolling_vol_length_matches_curve():
    curve = [1000.0 + i * 10 for i in range(10)]
    rm = RollingMetrics(curve)
    result = rm.rolling_volatility(3)
    assert len(result) == len(curve)


def test_rolling_sharpe_length_matches_curve():
    curve = [1000.0 + i * 10 for i in range(10)]
    rm = RollingMetrics(curve)
    result = rm.rolling_sharpe(3)
    assert len(result) == len(curve)


def test_rolling_mdd_length_matches_curve():
    curve = [1000.0 + i * 10 for i in range(10)]
    rm = RollingMetrics(curve)
    result = rm.rolling_max_drawdown(3)
    assert len(result) == len(curve)


# ===========================================================================
# Part 3 — Padding with None at the beginning
# ===========================================================================

def test_rolling_vol_first_window_entries_are_none():
    """window=3: first 3 entries should be None."""
    curve = [1000.0 + i * 10 for i in range(10)]
    rm = RollingMetrics(curve)
    result = rm.rolling_volatility(3)
    # rolling_vol aligns to equity_curve[i+1], so first window entries None
    assert result[0] is None
    assert result[1] is None
    assert result[2] is None


def test_rolling_sharpe_first_window_entries_are_none():
    curve = [1000.0 + i * 10 for i in range(10)]
    rm = RollingMetrics(curve)
    result = rm.rolling_sharpe(3)
    assert result[0] is None
    assert result[1] is None
    assert result[2] is None


def test_rolling_mdd_first_window_minus_one_entries_are_none():
    """window=3: first window-1=2 entries should be None."""
    curve = [1000.0 + i * 10 for i in range(10)]
    rm = RollingMetrics(curve)
    result = rm.rolling_max_drawdown(3)
    assert result[0] is None
    assert result[1] is None
    assert result[2] is not None


# ===========================================================================
# Part 4 — Non-None values are floats
# ===========================================================================

def test_rolling_vol_non_none_are_floats():
    curve = [1000.0, 1100.0, 1050.0, 1200.0, 1150.0, 1300.0]
    rm = RollingMetrics(curve)
    result = rm.rolling_volatility(3)
    for v in result:
        if v is not None:
            assert isinstance(v, float)


def test_rolling_sharpe_non_none_are_floats():
    curve = [1000.0, 1100.0, 1050.0, 1200.0, 1150.0, 1300.0]
    rm = RollingMetrics(curve)
    result = rm.rolling_sharpe(3)
    for v in result:
        if v is not None:
            assert isinstance(v, float)


def test_rolling_mdd_non_none_are_non_positive():
    curve = [1000.0, 1100.0, 1050.0, 1200.0, 1150.0, 1300.0]
    rm = RollingMetrics(curve)
    result = rm.rolling_max_drawdown(3)
    for v in result:
        if v is not None:
            assert v <= 0.0 + 1e-12


# ===========================================================================
# Part 5 — Flat curve: vol = 0, sharpe = 0
# ===========================================================================

def test_rolling_vol_flat_curve_is_zero():
    curve = [1000.0] * 10
    rm = RollingMetrics(curve)
    result = rm.rolling_volatility(3)
    for v in result:
        if v is not None:
            assert v == pytest.approx(0.0)


def test_rolling_sharpe_flat_curve_is_zero():
    curve = [1000.0] * 10
    rm = RollingMetrics(curve)
    result = rm.rolling_sharpe(3)
    for v in result:
        if v is not None:
            assert v == pytest.approx(0.0)


def test_rolling_mdd_monotonic_rising_is_zero():
    curve = [1000.0 + i * 10 for i in range(10)]
    rm = RollingMetrics(curve)
    result = rm.rolling_max_drawdown(3)
    for v in result:
        if v is not None:
            assert v == pytest.approx(0.0)


# ===========================================================================
# Part 6 — Small window edge case (window=2)
# ===========================================================================

def test_rolling_vol_window2():
    curve = [1000.0, 1100.0, 1050.0, 1200.0]
    rm = RollingMetrics(curve)
    result = rm.rolling_volatility(2)
    assert len(result) == 4
    assert result[0] is None
    assert result[1] is None
    assert result[2] is not None
    assert result[3] is not None


def test_rolling_mdd_window2():
    curve = [1000.0, 1100.0, 1050.0, 1200.0]
    rm = RollingMetrics(curve)
    result = rm.rolling_max_drawdown(2)
    assert result[0] is None
    assert result[1] is not None


# ===========================================================================
# Part 7 — Determinism
# ===========================================================================

def test_deterministic():
    curve = [1000.0, 1100.0, 1050.0, 1200.0, 1150.0]
    rm1 = RollingMetrics(curve)
    rm2 = RollingMetrics(curve)
    r1 = rm1.rolling_sharpe(3)
    r2 = rm2.rolling_sharpe(3)
    for a, b in zip(r1, r2):
        if a is None:
            assert b is None
        else:
            assert a == pytest.approx(b)


# ===========================================================================
# Part 8 — No mutation
# ===========================================================================

def test_no_mutation():
    curve = [1000.0, 1100.0, 1050.0]
    original = list(curve)
    rm = RollingMetrics(curve)
    rm.rolling_volatility(2)
    assert curve == original
