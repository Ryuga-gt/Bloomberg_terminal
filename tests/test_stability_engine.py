"""
RED tests for research.stability_engine.analyze_strategy

Contract:
    analyze_strategy(strategy_class, candles, window_size, initial_cash=1000)
        -> dict

Steps (specification):
    1. Split candles into time windows via split_into_time_windows(candles, window_size)
    2. For each window:
       - Instantiate Backtester(initial_cash)
       - Run strategy (strategy_class()) via bt.run(window, strategy=instance)
       - Collect: sharpe_ratio, max_drawdown_pct, return_pct
    3. Compute:
       - mean_sharpe    = mean of all window sharpe_ratios
       - sharpe_variance = sum((s - mean_sharpe)**2 for s in sharpes) / (n - 1)   # Bessel-corrected
       - worst_drawdown  = min of all window max_drawdown_pct  (most negative)
    4. stability_score = mean_sharpe - sharpe_variance - abs(worst_drawdown) / 100

Return dict must contain:
    regime_metrics   - list of per-window metric dicts
    mean_sharpe
    sharpe_variance
    worst_drawdown
    stability_score
"""

import math
import pytest

from research.stability_engine import analyze_strategy
from app.backtester.engine import Backtester

# ---------------------------------------------------------------------------
# Shared strategy fixtures
# ---------------------------------------------------------------------------

class AlwaysLongStrategy:
    """BUY on first candle, HOLD the rest — fully invested throughout."""
    def generate(self, candles: list[dict]) -> list[str]:
        return ["BUY"] + ["HOLD"] * (len(candles) - 1)


class AlwaysFlatStrategy:
    """Never buys — always HOLD."""
    def generate(self, candles: list[dict]) -> list[str]:
        return ["HOLD"] * len(candles)


# ---------------------------------------------------------------------------
# Shared candle fixtures
#
# CANDLES_6 — 6 candles, window_size=3 → 2 windows of 3 candles
#
# Window 0: closes [100, 110, 120]
#   AlwaysLongStrategy: BUY@100 → 10 shares, exit@120 → 1200
#   equity_curve = [1000, 1100, 1200]
#   returns      = [0.0, 0.1, 1/11]
#   mean_r       = (0 + 0.1 + 1/11) / 3
#   var_r        = sum((r - mean_r)**2 for r) / 2
#   sharpe_w0    = mean_r / sqrt(var_r)
#   max_drawdown = 0.0  (monotonic)
#
# Window 1: closes [120, 110, 100]
#   AlwaysLongStrategy: BUY@120 → 8.333 shares, exit@100 → 833.33
#   equity_curve = [1000, 916.67, 833.33]
#   returns      = [0.0, -1/12, -1/11]
#   sharpe_w1    = (negative value)
#   max_drawdown = (100-120)/120 * 100 = -16.667%
#
# These values are computed by the reference formula below to avoid
# hard-coding floating-point constants that could diverge from the
# implementation.
# ---------------------------------------------------------------------------

def make_candle(timestamp: str, close: float) -> dict:
    return {
        "timestamp": timestamp,
        "open": close,
        "high": close,
        "low":  close,
        "close": close,
        "volume": 1_000_000,
    }


CANDLES_6 = [
    make_candle("2024-01-01", 100.0),
    make_candle("2024-01-02", 110.0),
    make_candle("2024-01-03", 120.0),
    make_candle("2024-01-04", 120.0),
    make_candle("2024-01-05", 110.0),
    make_candle("2024-01-06", 100.0),
]

# ---------------------------------------------------------------------------
# Reference computation helper
# Re-implements the specification so tests are self-consistent without
# hard-coding fragile float literals.
# ---------------------------------------------------------------------------

def _ref_run_window(window: list[dict], strategy_class, initial_cash: float) -> dict:
    bt = Backtester(initial_cash)
    return bt.run(window, strategy=strategy_class())


def _ref_analyze(strategy_class, candles, window_size, initial_cash=1000):
    """Pure-Python reference implementation of the specification."""
    from research.regime_splitter import split_into_time_windows
    windows = split_into_time_windows(candles, window_size)
    metrics = [_ref_run_window(w, strategy_class, initial_cash) for w in windows]
    sharpes = [m["sharpe_ratio"] for m in metrics]
    drawdowns = [m["max_drawdown_pct"] for m in metrics]
    n = len(sharpes)
    mean_sharpe = sum(sharpes) / n
    sharpe_variance = sum((s - mean_sharpe) ** 2 for s in sharpes) / (n - 1)
    worst_drawdown = min(drawdowns)
    stability_score = mean_sharpe - sharpe_variance - abs(worst_drawdown) / 100
    return {
        "regime_metrics": metrics,
        "mean_sharpe": mean_sharpe,
        "sharpe_variance": sharpe_variance,
        "worst_drawdown": worst_drawdown,
        "stability_score": stability_score,
    }


# ---------------------------------------------------------------------------
# Return type and required keys
# ---------------------------------------------------------------------------

def test_returns_dict():
    result = analyze_strategy(AlwaysLongStrategy, CANDLES_6, window_size=3)
    assert isinstance(result, dict)


def test_result_has_regime_metrics_key():
    result = analyze_strategy(AlwaysLongStrategy, CANDLES_6, window_size=3)
    assert "regime_metrics" in result


def test_result_has_mean_sharpe_key():
    result = analyze_strategy(AlwaysLongStrategy, CANDLES_6, window_size=3)
    assert "mean_sharpe" in result


def test_result_has_sharpe_variance_key():
    result = analyze_strategy(AlwaysLongStrategy, CANDLES_6, window_size=3)
    assert "sharpe_variance" in result


def test_result_has_worst_drawdown_key():
    result = analyze_strategy(AlwaysLongStrategy, CANDLES_6, window_size=3)
    assert "worst_drawdown" in result


def test_result_has_stability_score_key():
    result = analyze_strategy(AlwaysLongStrategy, CANDLES_6, window_size=3)
    assert "stability_score" in result


# ---------------------------------------------------------------------------
# regime_metrics structure
# ---------------------------------------------------------------------------

def test_regime_metrics_is_list():
    result = analyze_strategy(AlwaysLongStrategy, CANDLES_6, window_size=3)
    assert isinstance(result["regime_metrics"], list)


def test_regime_metrics_length_equals_window_count():
    # 6 candles, window_size=3 → 2 windows
    result = analyze_strategy(AlwaysLongStrategy, CANDLES_6, window_size=3)
    assert len(result["regime_metrics"]) == 2


def test_each_regime_metric_has_sharpe_ratio():
    result = analyze_strategy(AlwaysLongStrategy, CANDLES_6, window_size=3)
    for m in result["regime_metrics"]:
        assert "sharpe_ratio" in m


def test_each_regime_metric_has_max_drawdown_pct():
    result = analyze_strategy(AlwaysLongStrategy, CANDLES_6, window_size=3)
    for m in result["regime_metrics"]:
        assert "max_drawdown_pct" in m


def test_each_regime_metric_has_return_pct():
    result = analyze_strategy(AlwaysLongStrategy, CANDLES_6, window_size=3)
    for m in result["regime_metrics"]:
        assert "return_pct" in m


# ---------------------------------------------------------------------------
# Correct mean_sharpe
# mean_sharpe = (sharpe_w0 + sharpe_w1) / 2
# ---------------------------------------------------------------------------

def test_correct_mean_sharpe():
    ref = _ref_analyze(AlwaysLongStrategy, CANDLES_6, window_size=3)
    result = analyze_strategy(AlwaysLongStrategy, CANDLES_6, window_size=3)
    assert result["mean_sharpe"] == pytest.approx(ref["mean_sharpe"], rel=1e-9)


def test_mean_sharpe_is_average_of_window_sharpes():
    result = analyze_strategy(AlwaysLongStrategy, CANDLES_6, window_size=3)
    sharpes = [m["sharpe_ratio"] for m in result["regime_metrics"]]
    expected_mean = sum(sharpes) / len(sharpes)
    assert result["mean_sharpe"] == pytest.approx(expected_mean, rel=1e-9)


# ---------------------------------------------------------------------------
# Correct sharpe_variance — Bessel-corrected (divide by n-1)
# ---------------------------------------------------------------------------

def test_correct_sharpe_variance():
    ref = _ref_analyze(AlwaysLongStrategy, CANDLES_6, window_size=3)
    result = analyze_strategy(AlwaysLongStrategy, CANDLES_6, window_size=3)
    assert result["sharpe_variance"] == pytest.approx(ref["sharpe_variance"], rel=1e-9)


def test_sharpe_variance_uses_bessel_correction():
    """
    Variance must use (n-1) denominator, NOT n.
    With 2 windows and sharpes [s0, s1]:
        mean = (s0 + s1) / 2
        bessel_var = ((s0-mean)^2 + (s1-mean)^2) / 1
        biased_var = ((s0-mean)^2 + (s1-mean)^2) / 2
    bessel_var = 2 * biased_var  (they differ by factor 2)
    """
    result = analyze_strategy(AlwaysLongStrategy, CANDLES_6, window_size=3)
    sharpes = [m["sharpe_ratio"] for m in result["regime_metrics"]]
    n = len(sharpes)
    mean = sum(sharpes) / n
    bessel_var = sum((s - mean) ** 2 for s in sharpes) / (n - 1)
    biased_var = sum((s - mean) ** 2 for s in sharpes) / n
    # The result must match bessel, not biased
    assert result["sharpe_variance"] == pytest.approx(bessel_var, rel=1e-9)
    # Confirm they actually differ (so the test is non-trivial) — only when sharpes differ
    if sharpes[0] != sharpes[1]:
        assert abs(result["sharpe_variance"] - biased_var) > 1e-12


def test_sharpe_variance_is_non_negative():
    result = analyze_strategy(AlwaysLongStrategy, CANDLES_6, window_size=3)
    assert result["sharpe_variance"] >= 0.0


# ---------------------------------------------------------------------------
# Correct worst_drawdown
# worst_drawdown = min(max_drawdown_pct for each window)
# Window 0: monotonically rising → drawdown = 0.0
# Window 1: declining           → drawdown = (100-120)/120*100 = -16.667%
# worst_drawdown = -16.667%
# ---------------------------------------------------------------------------

def test_correct_worst_drawdown():
    ref = _ref_analyze(AlwaysLongStrategy, CANDLES_6, window_size=3)
    result = analyze_strategy(AlwaysLongStrategy, CANDLES_6, window_size=3)
    assert result["worst_drawdown"] == pytest.approx(ref["worst_drawdown"], rel=1e-9)


def test_worst_drawdown_is_minimum_of_window_drawdowns():
    result = analyze_strategy(AlwaysLongStrategy, CANDLES_6, window_size=3)
    drawdowns = [m["max_drawdown_pct"] for m in result["regime_metrics"]]
    assert result["worst_drawdown"] == min(drawdowns)


def test_worst_drawdown_is_negative_when_declining_window_present():
    result = analyze_strategy(AlwaysLongStrategy, CANDLES_6, window_size=3)
    assert result["worst_drawdown"] < 0.0


def test_worst_drawdown_is_zero_when_all_windows_monotonic():
    # All rising: closes [10, 20, 30, 40, 50, 60]
    candles = [make_candle(f"2024-01-{i+1:02d}", float((i+1)*10)) for i in range(6)]
    result = analyze_strategy(AlwaysLongStrategy, candles, window_size=3)
    assert result["worst_drawdown"] == 0.0


# ---------------------------------------------------------------------------
# Correct stability_score
# stability_score = mean_sharpe - sharpe_variance - abs(worst_drawdown) / 100
# ---------------------------------------------------------------------------

def test_correct_stability_score():
    ref = _ref_analyze(AlwaysLongStrategy, CANDLES_6, window_size=3)
    result = analyze_strategy(AlwaysLongStrategy, CANDLES_6, window_size=3)
    assert result["stability_score"] == pytest.approx(ref["stability_score"], rel=1e-9)


def test_stability_score_formula():
    """stability_score = mean_sharpe - sharpe_variance - abs(worst_drawdown)/100"""
    result = analyze_strategy(AlwaysLongStrategy, CANDLES_6, window_size=3)
    expected = (
        result["mean_sharpe"]
        - result["sharpe_variance"]
        - abs(result["worst_drawdown"]) / 100
    )
    assert result["stability_score"] == pytest.approx(expected, rel=1e-9)


def test_stability_score_is_float():
    result = analyze_strategy(AlwaysLongStrategy, CANDLES_6, window_size=3)
    assert isinstance(result["stability_score"], float)


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------

def test_deterministic_output():
    result1 = analyze_strategy(AlwaysLongStrategy, CANDLES_6, window_size=3)
    result2 = analyze_strategy(AlwaysLongStrategy, CANDLES_6, window_size=3)
    assert result1["mean_sharpe"] == result2["mean_sharpe"]
    assert result1["sharpe_variance"] == result2["sharpe_variance"]
    assert result1["worst_drawdown"] == result2["worst_drawdown"]
    assert result1["stability_score"] == result2["stability_score"]


# ---------------------------------------------------------------------------
# initial_cash parameter is forwarded to each Backtester
# Using initial_cash=500 must yield same sharpe/drawdown shapes but
# different absolute equity values.
# ---------------------------------------------------------------------------

def test_initial_cash_forwarded_to_backtester():
    result_1000 = analyze_strategy(AlwaysLongStrategy, CANDLES_6, window_size=3, initial_cash=1000)
    result_500  = analyze_strategy(AlwaysLongStrategy, CANDLES_6, window_size=3, initial_cash=500)
    # Sharpe ratio is scale-invariant — must match regardless of initial_cash
    for m1, m5 in zip(result_1000["regime_metrics"], result_500["regime_metrics"]):
        assert m1["sharpe_ratio"] == pytest.approx(m5["sharpe_ratio"], rel=1e-9)


# ---------------------------------------------------------------------------
# Input candles must NOT be mutated
# ---------------------------------------------------------------------------

def test_does_not_mutate_candles_length():
    candles = [make_candle(f"2024-01-{i+1:02d}", float((i+1)*10)) for i in range(6)]
    original_len = len(candles)
    analyze_strategy(AlwaysLongStrategy, candles, window_size=3)
    assert len(candles) == original_len


def test_does_not_mutate_candles_values():
    candles = [make_candle(f"2024-01-{i+1:02d}", float((i+1)*10)) for i in range(6)]
    original_closes = [c["close"] for c in candles]
    analyze_strategy(AlwaysLongStrategy, candles, window_size=3)
    for i, c in enumerate(candles):
        assert c["close"] == original_closes[i]


def test_does_not_mutate_candle_keys():
    candles = [make_candle(f"2024-01-{i+1:02d}", float((i+1)*10)) for i in range(6)]
    original_keys = [set(c.keys()) for c in candles]
    analyze_strategy(AlwaysLongStrategy, candles, window_size=3)
    for i, c in enumerate(candles):
        assert set(c.keys()) == original_keys[i]


# ---------------------------------------------------------------------------
# ValueError propagation for invalid window_size
# (must bubble up from split_into_time_windows)
# ---------------------------------------------------------------------------

def test_raises_for_window_size_one():
    candles = [make_candle(f"2024-01-{i+1:02d}", float((i+1)*10)) for i in range(6)]
    with pytest.raises(ValueError):
        analyze_strategy(AlwaysLongStrategy, candles, window_size=1)


def test_raises_for_window_size_larger_than_candles():
    candles = [make_candle(f"2024-01-{i+1:02d}", float((i+1)*10)) for i in range(3)]
    with pytest.raises(ValueError):
        analyze_strategy(AlwaysLongStrategy, candles, window_size=10)


def test_raises_for_negative_window_size():
    candles = [make_candle(f"2024-01-{i+1:02d}", float((i+1)*10)) for i in range(6)]
    with pytest.raises(ValueError):
        analyze_strategy(AlwaysLongStrategy, candles, window_size=-1)


# ---------------------------------------------------------------------------
# Three-window fixture for variance correctness with n=3
# 9 candles, window_size=3 → 3 windows
# Closes: [10,20,30], [30,40,50], [50,40,30]
# All strategies run via AlwaysLongStrategy
# ---------------------------------------------------------------------------

CANDLES_9 = [
    make_candle("2024-01-01", 10.0),
    make_candle("2024-01-02", 20.0),
    make_candle("2024-01-03", 30.0),
    make_candle("2024-01-04", 30.0),
    make_candle("2024-01-05", 40.0),
    make_candle("2024-01-06", 50.0),
    make_candle("2024-01-07", 50.0),
    make_candle("2024-01-08", 40.0),
    make_candle("2024-01-09", 30.0),
]


def test_three_window_mean_sharpe():
    ref = _ref_analyze(AlwaysLongStrategy, CANDLES_9, window_size=3)
    result = analyze_strategy(AlwaysLongStrategy, CANDLES_9, window_size=3)
    assert result["mean_sharpe"] == pytest.approx(ref["mean_sharpe"], rel=1e-9)


def test_three_window_sharpe_variance():
    ref = _ref_analyze(AlwaysLongStrategy, CANDLES_9, window_size=3)
    result = analyze_strategy(AlwaysLongStrategy, CANDLES_9, window_size=3)
    assert result["sharpe_variance"] == pytest.approx(ref["sharpe_variance"], rel=1e-9)


def test_three_window_worst_drawdown():
    ref = _ref_analyze(AlwaysLongStrategy, CANDLES_9, window_size=3)
    result = analyze_strategy(AlwaysLongStrategy, CANDLES_9, window_size=3)
    assert result["worst_drawdown"] == pytest.approx(ref["worst_drawdown"], rel=1e-9)


def test_three_window_stability_score():
    ref = _ref_analyze(AlwaysLongStrategy, CANDLES_9, window_size=3)
    result = analyze_strategy(AlwaysLongStrategy, CANDLES_9, window_size=3)
    assert result["stability_score"] == pytest.approx(ref["stability_score"], rel=1e-9)


def test_three_window_regime_metrics_length():
    result = analyze_strategy(AlwaysLongStrategy, CANDLES_9, window_size=3)
    assert len(result["regime_metrics"]) == 3


def test_three_window_variance_bessel_corrected():
    """With n=3 sharpes verify (n-1)=2 denominator."""
    result = analyze_strategy(AlwaysLongStrategy, CANDLES_9, window_size=3)
    sharpes = [m["sharpe_ratio"] for m in result["regime_metrics"]]
    n = len(sharpes)
    mean = sum(sharpes) / n
    expected_var = sum((s - mean) ** 2 for s in sharpes) / (n - 1)
    assert result["sharpe_variance"] == pytest.approx(expected_var, rel=1e-9)
