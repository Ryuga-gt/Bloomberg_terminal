"""
Tests for analytics.drawdown_analytics.DrawdownAnalytics
"""

import pytest

from analytics.drawdown_analytics import DrawdownAnalytics


# ===========================================================================
# Part 1 — Validation
# ===========================================================================

def test_empty_raises():
    with pytest.raises(ValueError):
        DrawdownAnalytics([])


def test_non_positive_raises():
    with pytest.raises(ValueError):
        DrawdownAnalytics([1000.0, 0.0])


def test_single_element_valid():
    da = DrawdownAnalytics([1000.0])
    assert da is not None


# ===========================================================================
# Part 2 — drawdown_series
# ===========================================================================

def test_drawdown_series_length_matches_curve():
    curve = [1000.0, 1100.0, 1050.0, 1200.0]
    da = DrawdownAnalytics(curve)
    assert len(da.drawdown_series()) == len(curve)


def test_drawdown_series_monotonic_rising_all_zero():
    curve = [1000.0, 1100.0, 1200.0, 1300.0]
    da = DrawdownAnalytics(curve)
    for v in da.drawdown_series():
        assert v == pytest.approx(0.0)


def test_drawdown_series_first_element_zero():
    """First element is always 0 (no prior peak)."""
    da = DrawdownAnalytics([1000.0, 900.0, 800.0])
    assert da.drawdown_series()[0] == pytest.approx(0.0)


def test_drawdown_series_values_non_positive():
    curve = [1000.0, 1100.0, 900.0, 1050.0]
    da = DrawdownAnalytics(curve)
    for v in da.drawdown_series():
        assert v <= 0.0 + 1e-12


def test_drawdown_series_correct_values():
    """
    curve = [1000, 1100, 990, 1100]
    peak  = [1000, 1100, 1100, 1100]
    dd    = [0, 0, (990-1100)/1100, 0]
    """
    curve = [1000.0, 1100.0, 990.0, 1100.0]
    da = DrawdownAnalytics(curve)
    series = da.drawdown_series()
    assert series[0] == pytest.approx(0.0)
    assert series[1] == pytest.approx(0.0)
    assert series[2] == pytest.approx((990 - 1100) / 1100)
    assert series[3] == pytest.approx(0.0)


# ===========================================================================
# Part 3 — max_drawdown
# ===========================================================================

def test_max_drawdown_monotonic_rising_is_zero():
    da = DrawdownAnalytics([1000.0, 1100.0, 1200.0])
    assert da.max_drawdown() == pytest.approx(0.0)


def test_max_drawdown_single_dip():
    """1000 → 1100 → 880 → max_dd = (880-1100)/1100."""
    da = DrawdownAnalytics([1000.0, 1100.0, 880.0])
    expected = (880 - 1100) / 1100
    assert da.max_drawdown() == pytest.approx(expected)


def test_max_drawdown_is_negative():
    da = DrawdownAnalytics([1000.0, 1100.0, 900.0, 1200.0])
    assert da.max_drawdown() < 0


def test_max_drawdown_multiple_peaks():
    """Two dips; the deeper one should be max_drawdown."""
    curve = [1000.0, 1200.0, 1100.0, 1300.0, 1000.0]
    da = DrawdownAnalytics(curve)
    # Dip 1: (1100-1200)/1200 = -8.33%
    # Dip 2: (1000-1300)/1300 = -23.08%
    assert da.max_drawdown() == pytest.approx((1000 - 1300) / 1300)


# ===========================================================================
# Part 4 — average_drawdown
# ===========================================================================

def test_average_drawdown_no_drawdown_is_zero():
    da = DrawdownAnalytics([1000.0, 1100.0, 1200.0])
    assert da.average_drawdown() == pytest.approx(0.0)


def test_average_drawdown_negative():
    da = DrawdownAnalytics([1000.0, 1100.0, 900.0, 1200.0, 1000.0])
    assert da.average_drawdown() < 0


# ===========================================================================
# Part 5 — max_drawdown_duration
# ===========================================================================

def test_max_drawdown_duration_no_drawdown_is_zero():
    da = DrawdownAnalytics([1000.0, 1100.0, 1200.0])
    assert da.max_drawdown_duration() == 0


def test_max_drawdown_duration_with_recovery():
    """
    1000 → 1100 → 880 → 1100
    Peak at index 1 (1100), trough at index 2 (880), recovery at index 3.
    Duration = 3 - 1 = 2.
    """
    da = DrawdownAnalytics([1000.0, 1100.0, 880.0, 1100.0])
    assert da.max_drawdown_duration() == 2


def test_max_drawdown_duration_no_recovery():
    """No recovery → duration = n - 1 - peak_idx."""
    da = DrawdownAnalytics([1000.0, 1100.0, 900.0])
    # Peak at index 1, no recovery → duration = 3 - 1 - 1 = 1
    assert da.max_drawdown_duration() == 1


# ===========================================================================
# Part 6 — recovery_time
# ===========================================================================

def test_recovery_time_no_drawdown_is_zero():
    da = DrawdownAnalytics([1000.0, 1100.0, 1200.0])
    assert da.recovery_time() == 0


def test_recovery_time_with_recovery():
    """Trough at index 2, recovery at index 3 → recovery_time = 1."""
    da = DrawdownAnalytics([1000.0, 1100.0, 880.0, 1100.0])
    assert da.recovery_time() == 1


def test_recovery_time_no_recovery():
    """No recovery → periods remaining from trough."""
    da = DrawdownAnalytics([1000.0, 1100.0, 900.0])
    # Trough at index 2, no recovery → n - 1 - trough_idx = 3 - 1 - 2 = 0
    assert da.recovery_time() == 0


# ===========================================================================
# Part 7 — determinism and no mutation
# ===========================================================================

def test_deterministic():
    curve = [1000.0, 1100.0, 900.0, 1200.0]
    da1 = DrawdownAnalytics(curve)
    da2 = DrawdownAnalytics(curve)
    assert da1.max_drawdown() == pytest.approx(da2.max_drawdown())


def test_no_mutation():
    curve = [1000.0, 1100.0, 900.0]
    original = list(curve)
    DrawdownAnalytics(curve)
    assert curve == original
