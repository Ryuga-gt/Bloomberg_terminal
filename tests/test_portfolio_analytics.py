"""
Tests for analytics.portfolio_analytics.PortfolioAnalytics
"""

import pytest

from analytics.portfolio_analytics import PortfolioAnalytics


# ===========================================================================
# Part 1 — Validation (delegated to RiskMetrics)
# ===========================================================================

def test_too_short_raises():
    with pytest.raises(ValueError):
        PortfolioAnalytics([1000.0])


def test_non_positive_raises():
    with pytest.raises(ValueError):
        PortfolioAnalytics([1000.0, 0.0, 1100.0])


# ===========================================================================
# Part 2 — full_report() returns dict with required keys
# ===========================================================================

REQUIRED_KEYS = [
    "total_return",
    "cagr",
    "volatility",
    "sharpe",
    "sortino",
    "max_drawdown",
    "max_drawdown_duration",
    "var_95_hist",
    "var_95_param",
    "rolling_sharpe_20",
    "rolling_vol_20",
    "attribution",
]


def test_full_report_returns_dict():
    curve = [1000.0 + i * 10 for i in range(30)]
    pa = PortfolioAnalytics(curve)
    assert isinstance(pa.full_report(), dict)


def test_full_report_has_all_required_keys():
    curve = [1000.0 + i * 10 for i in range(30)]
    pa = PortfolioAnalytics(curve)
    report = pa.full_report()
    for key in REQUIRED_KEYS:
        assert key in report, f"Missing key: {key}"


# ===========================================================================
# Part 3 — rolling lists correct length
# ===========================================================================

def test_rolling_sharpe_20_length_matches_curve():
    curve = [1000.0 + i * 10 for i in range(30)]
    pa = PortfolioAnalytics(curve)
    report = pa.full_report()
    assert len(report["rolling_sharpe_20"]) == len(curve)


def test_rolling_vol_20_length_matches_curve():
    curve = [1000.0 + i * 10 for i in range(30)]
    pa = PortfolioAnalytics(curve)
    report = pa.full_report()
    assert len(report["rolling_vol_20"]) == len(curve)


def test_rolling_sharpe_short_curve_length_matches():
    """Short curve (< 20 candles) — window adapts."""
    curve = [1000.0 + i * 10 for i in range(5)]
    pa = PortfolioAnalytics(curve)
    report = pa.full_report()
    assert len(report["rolling_sharpe_20"]) == len(curve)


# ===========================================================================
# Part 4 — attribution is None when no strategy curves provided
# ===========================================================================

def test_attribution_none_without_strategy_curves():
    curve = [1000.0 + i * 10 for i in range(10)]
    pa = PortfolioAnalytics(curve)
    report = pa.full_report()
    assert report["attribution"] is None


def test_attribution_present_with_strategy_curves():
    curve = [1000.0 + i * 10 for i in range(10)]
    pa = PortfolioAnalytics(
        curve,
        strategy_equity_curves={"A": [500.0 + i * 5 for i in range(10)],
                                 "B": [500.0 + i * 5 for i in range(10)]}
    )
    report = pa.full_report()
    assert report["attribution"] is not None
    assert "A" in report["attribution"]
    assert "B" in report["attribution"]


# ===========================================================================
# Part 5 — Determinism
# ===========================================================================

def test_deterministic():
    curve = [1000.0, 1100.0, 1050.0, 1200.0, 1150.0, 1300.0,
             1250.0, 1400.0, 1350.0, 1500.0]
    pa1 = PortfolioAnalytics(curve)
    pa2 = PortfolioAnalytics(curve)
    r1 = pa1.full_report()
    r2 = pa2.full_report()
    assert r1["sharpe"] == pytest.approx(r2["sharpe"])
    assert r1["max_drawdown"] == pytest.approx(r2["max_drawdown"])
    assert r1["var_95_hist"] == pytest.approx(r2["var_95_hist"])


# ===========================================================================
# Part 6 — No mutation
# ===========================================================================

def test_no_mutation_of_curve():
    curve = [1000.0, 1100.0, 1050.0, 1200.0]
    original = list(curve)
    pa = PortfolioAnalytics(curve)
    pa.full_report()
    assert curve == original


# ===========================================================================
# Part 7 — Sanity checks on values
# ===========================================================================

def test_total_return_positive_for_rising_curve():
    curve = [1000.0 + i * 10 for i in range(10)]
    pa = PortfolioAnalytics(curve)
    assert pa.full_report()["total_return"] > 0


def test_max_drawdown_zero_for_monotonic_rising():
    curve = [1000.0 + i * 10 for i in range(10)]
    pa = PortfolioAnalytics(curve)
    assert pa.full_report()["max_drawdown"] == pytest.approx(0.0)


def test_var_95_hist_is_float_or_none():
    curve = [1000.0 + i * 10 for i in range(10)]
    pa = PortfolioAnalytics(curve)
    v = pa.full_report()["var_95_hist"]
    assert v is None or isinstance(v, float)


def test_max_drawdown_duration_non_negative():
    curve = [1000.0, 1100.0, 900.0, 1200.0, 1000.0, 1300.0]
    pa = PortfolioAnalytics(curve)
    assert pa.full_report()["max_drawdown_duration"] >= 0
