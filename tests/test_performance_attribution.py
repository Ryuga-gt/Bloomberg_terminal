"""
Tests for analytics.performance_attribution.PerformanceAttribution
"""

import pytest

from analytics.performance_attribution import PerformanceAttribution


# ===========================================================================
# Part 1 — Validation
# ===========================================================================

def test_empty_portfolio_curve_raises():
    with pytest.raises(ValueError):
        PerformanceAttribution([], {"A": []})


def test_empty_strategy_curves_raises():
    with pytest.raises(ValueError):
        PerformanceAttribution([1000.0, 1100.0], {})


def test_mismatched_length_raises():
    with pytest.raises(ValueError):
        PerformanceAttribution(
            [1000.0, 1100.0, 1200.0],
            {"A": [500.0, 550.0]}  # length 2 vs 3
        )


def test_valid_construction():
    pa = PerformanceAttribution(
        [1000.0, 1100.0],
        {"A": [500.0, 550.0], "B": [500.0, 550.0]}
    )
    assert pa is not None


# ===========================================================================
# Part 2 — compute() return type and keys
# ===========================================================================

def test_compute_returns_dict():
    pa = PerformanceAttribution(
        [1000.0, 1100.0],
        {"A": [500.0, 550.0], "B": [500.0, 550.0]}
    )
    result = pa.compute()
    assert isinstance(result, dict)


def test_compute_keys_match_strategy_names():
    pa = PerformanceAttribution(
        [1000.0, 1100.0],
        {"Alpha": [500.0, 550.0], "Beta": [500.0, 550.0]}
    )
    result = pa.compute()
    assert set(result.keys()) == {"Alpha", "Beta"}


def test_compute_entry_has_absolute_return():
    pa = PerformanceAttribution(
        [1000.0, 1100.0],
        {"A": [500.0, 550.0]}
    )
    result = pa.compute()
    assert "absolute_return" in result["A"]


def test_compute_entry_has_contribution_pct():
    pa = PerformanceAttribution(
        [1000.0, 1100.0],
        {"A": [500.0, 550.0]}
    )
    result = pa.compute()
    assert "contribution_pct" in result["A"]


def test_compute_entry_has_allocation_effect():
    pa = PerformanceAttribution(
        [1000.0, 1100.0],
        {"A": [500.0, 550.0]}
    )
    result = pa.compute()
    assert "allocation_effect" in result["A"]


def test_compute_entry_has_selection_effect():
    pa = PerformanceAttribution(
        [1000.0, 1100.0],
        {"A": [500.0, 550.0]}
    )
    result = pa.compute()
    assert "selection_effect" in result["A"]


# ===========================================================================
# Part 3 — Equal curves: contribution_pct = 0.5 each
# ===========================================================================

def test_equal_curves_contribution_pct():
    """
    Portfolio: 1000 → 1100 (abs return = 100)
    A: 500 → 550 (abs return = 50)
    B: 500 → 550 (abs return = 50)
    contribution_pct_A = 50/100 = 0.5
    """
    pa = PerformanceAttribution(
        [1000.0, 1100.0],
        {"A": [500.0, 550.0], "B": [500.0, 550.0]}
    )
    result = pa.compute()
    assert result["A"]["contribution_pct"] == pytest.approx(0.5)
    assert result["B"]["contribution_pct"] == pytest.approx(0.5)


def test_equal_curves_absolute_return():
    pa = PerformanceAttribution(
        [1000.0, 1100.0],
        {"A": [500.0, 550.0], "B": [500.0, 550.0]}
    )
    result = pa.compute()
    assert result["A"]["absolute_return"] == pytest.approx(50.0)
    assert result["B"]["absolute_return"] == pytest.approx(50.0)


# ===========================================================================
# Part 4 — One outperformer
# ===========================================================================

def test_one_outperformer_higher_contribution():
    """
    Portfolio: 1000 → 1200 (abs return = 200)
    A: 500 → 700 (abs return = 200) → contribution = 1.0
    B: 500 → 500 (abs return = 0)   → contribution = 0.0
    """
    pa = PerformanceAttribution(
        [1000.0, 1200.0],
        {"A": [500.0, 700.0], "B": [500.0, 500.0]}
    )
    result = pa.compute()
    assert result["A"]["contribution_pct"] == pytest.approx(1.0)
    assert result["B"]["contribution_pct"] == pytest.approx(0.0)


# ===========================================================================
# Part 5 — Contribution sums to 1 (when portfolio return != 0)
# ===========================================================================

def test_contribution_pct_sums_to_one():
    pa = PerformanceAttribution(
        [1000.0, 1200.0],
        {"A": [500.0, 650.0], "B": [500.0, 550.0]}
    )
    result = pa.compute()
    total = sum(v["contribution_pct"] for v in result.values())
    assert total == pytest.approx(1.0)


def test_contribution_pct_sums_to_one_three_strategies():
    pa = PerformanceAttribution(
        [1500.0, 1800.0],
        {
            "A": [500.0, 600.0],
            "B": [500.0, 600.0],
            "C": [500.0, 600.0],
        }
    )
    result = pa.compute()
    total = sum(v["contribution_pct"] for v in result.values())
    assert total == pytest.approx(1.0)


# ===========================================================================
# Part 6 — Zero portfolio return → contribution_pct = 0
# ===========================================================================

def test_zero_portfolio_return_contribution_is_zero():
    pa = PerformanceAttribution(
        [1000.0, 1000.0],
        {"A": [500.0, 500.0], "B": [500.0, 500.0]}
    )
    result = pa.compute()
    for v in result.values():
        assert v["contribution_pct"] == pytest.approx(0.0)


# ===========================================================================
# Part 7 — Determinism and no mutation
# ===========================================================================

def test_deterministic():
    portfolio = [1000.0, 1100.0, 1200.0]
    strategies = {"A": [500.0, 550.0, 600.0], "B": [500.0, 550.0, 600.0]}
    pa1 = PerformanceAttribution(portfolio, strategies)
    pa2 = PerformanceAttribution(portfolio, strategies)
    r1 = pa1.compute()
    r2 = pa2.compute()
    assert r1["A"]["contribution_pct"] == pytest.approx(r2["A"]["contribution_pct"])


def test_no_mutation_portfolio():
    portfolio = [1000.0, 1100.0]
    original = list(portfolio)
    PerformanceAttribution(portfolio, {"A": [500.0, 550.0]})
    assert portfolio == original


def test_no_mutation_strategy_curves():
    strategies = {"A": [500.0, 550.0]}
    original = list(strategies["A"])
    PerformanceAttribution([1000.0, 1100.0], strategies)
    assert strategies["A"] == original
