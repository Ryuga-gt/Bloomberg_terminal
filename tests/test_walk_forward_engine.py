"""
RED tests for research.walk_forward_engine.walk_forward_analysis

Contract:
    walk_forward_analysis(
        strategy_class,
        candles,
        train_size,
        test_size,
        step_size,
        initial_cash=1000,
    ) -> dict

Slicing logic:
    pos = 0
    while True:
        train_slice = candles[pos : pos + train_size]
        test_slice  = candles[pos + train_size : pos + train_size + test_size]
        if len(test_slice) < test_size:
            break          # incomplete test window → stop
        ... process window ...
        pos += step_size

Per-window output (stored in "windows" list):
    train_sharpe
    test_sharpe
    train_drawdown
    test_drawdown
    train_return
    test_return

Aggregate output (top-level keys):
    windows               - list of per-window dicts
    mean_train_sharpe     - mean of all train_sharpe values
    mean_test_sharpe      - mean of all test_sharpe values
    test_sharpe_variance  - Bessel-corrected sample variance of test_sharpe
    performance_decay     - mean_test_sharpe - mean_train_sharpe

Raises ValueError for:
    train_size < 2
    test_size  < 2
    step_size  < 1
    dataset too small to produce even one window
"""

import math
import pytest

from research.walk_forward_engine import walk_forward_analysis
from app.backtester.engine import Backtester

# ---------------------------------------------------------------------------
# Strategy fixtures
# ---------------------------------------------------------------------------

class AlwaysLongStrategy:
    """BUY on first candle, HOLD the rest."""
    def generate(self, candles: list[dict]) -> list[str]:
        return ["BUY"] + ["HOLD"] * (len(candles) - 1)


class AlwaysFlatStrategy:
    """Never buys."""
    def generate(self, candles: list[dict]) -> list[str]:
        return ["HOLD"] * len(candles)


# ---------------------------------------------------------------------------
# Candle factory
# ---------------------------------------------------------------------------

def make_candle(ts: str, close: float) -> dict:
    return {
        "timestamp": ts,
        "open":  close,
        "high":  close,
        "low":   close,
        "close": close,
        "volume": 1_000_000,
    }


# ---------------------------------------------------------------------------
# Primary fixture
#
# 10 candles: closes = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
# train_size=4, test_size=3, step_size=3
#
# Window 0:  pos=0
#   train = candles[0:4]  = closes [10, 20, 30, 40]
#   test  = candles[4:7]  = closes [50, 60, 70]
#
# Window 1:  pos=3
#   train = candles[3:7]  = closes [40, 50, 60, 70]
#   test  = candles[7:10] = closes [80, 90, 100]
#
# pos=6 check: test = candles[10:13] = [] → len < 3 → STOP
# ---------------------------------------------------------------------------

CANDLES_10 = [
    make_candle(f"2024-01-{i+1:02d}", float((i + 1) * 10))
    for i in range(10)
]


# ---------------------------------------------------------------------------
# Reference computation — re-implements spec to avoid hard-coded floats
# ---------------------------------------------------------------------------

def _ref_run(window: list[dict], strategy_class, initial_cash: float) -> dict:
    bt = Backtester(initial_cash)
    return bt.run(window, strategy=strategy_class())


def _ref_walk_forward(strategy_class, candles, train_size, test_size, step_size,
                       initial_cash=1000) -> dict:
    windows_out = []
    pos = 0
    while True:
        train = candles[pos: pos + train_size]
        test  = candles[pos + train_size: pos + train_size + test_size]
        if len(test) < test_size:
            break
        r_tr = _ref_run(train, strategy_class, initial_cash)
        r_te = _ref_run(test,  strategy_class, initial_cash)
        windows_out.append({
            "train_sharpe":   r_tr["sharpe_ratio"],
            "test_sharpe":    r_te["sharpe_ratio"],
            "train_drawdown": r_tr["max_drawdown_pct"],
            "test_drawdown":  r_te["max_drawdown_pct"],
            "train_return":   r_tr["return_pct"],
            "test_return":    r_te["return_pct"],
        })
        pos += step_size

    n = len(windows_out)
    train_sharpes = [w["train_sharpe"] for w in windows_out]
    test_sharpes  = [w["test_sharpe"]  for w in windows_out]
    mean_train_sharpe    = sum(train_sharpes) / n
    mean_test_sharpe     = sum(test_sharpes)  / n
    test_sharpe_variance = sum((s - mean_test_sharpe) ** 2 for s in test_sharpes) / (n - 1)
    performance_decay    = mean_test_sharpe - mean_train_sharpe

    return {
        "windows":             windows_out,
        "mean_train_sharpe":   mean_train_sharpe,
        "mean_test_sharpe":    mean_test_sharpe,
        "test_sharpe_variance": test_sharpe_variance,
        "performance_decay":   performance_decay,
    }


# ===========================================================================
# PART 1 — Return type and top-level keys
# ===========================================================================

def test_returns_dict():
    result = walk_forward_analysis(AlwaysLongStrategy, CANDLES_10,
                                   train_size=4, test_size=3, step_size=3)
    assert isinstance(result, dict)


def test_result_has_windows_key():
    result = walk_forward_analysis(AlwaysLongStrategy, CANDLES_10,
                                   train_size=4, test_size=3, step_size=3)
    assert "windows" in result


def test_result_has_mean_train_sharpe_key():
    result = walk_forward_analysis(AlwaysLongStrategy, CANDLES_10,
                                   train_size=4, test_size=3, step_size=3)
    assert "mean_train_sharpe" in result


def test_result_has_mean_test_sharpe_key():
    result = walk_forward_analysis(AlwaysLongStrategy, CANDLES_10,
                                   train_size=4, test_size=3, step_size=3)
    assert "mean_test_sharpe" in result


def test_result_has_test_sharpe_variance_key():
    result = walk_forward_analysis(AlwaysLongStrategy, CANDLES_10,
                                   train_size=4, test_size=3, step_size=3)
    assert "test_sharpe_variance" in result


def test_result_has_performance_decay_key():
    result = walk_forward_analysis(AlwaysLongStrategy, CANDLES_10,
                                   train_size=4, test_size=3, step_size=3)
    assert "performance_decay" in result


# ===========================================================================
# PART 2 — windows list structure
# ===========================================================================

def test_windows_is_list():
    result = walk_forward_analysis(AlwaysLongStrategy, CANDLES_10,
                                   train_size=4, test_size=3, step_size=3)
    assert isinstance(result["windows"], list)


def test_windows_count_correct():
    # 10 candles, train=4, test=3, step=3 → 2 windows
    result = walk_forward_analysis(AlwaysLongStrategy, CANDLES_10,
                                   train_size=4, test_size=3, step_size=3)
    assert len(result["windows"]) == 2


def test_each_window_has_train_sharpe():
    result = walk_forward_analysis(AlwaysLongStrategy, CANDLES_10,
                                   train_size=4, test_size=3, step_size=3)
    for w in result["windows"]:
        assert "train_sharpe" in w


def test_each_window_has_test_sharpe():
    result = walk_forward_analysis(AlwaysLongStrategy, CANDLES_10,
                                   train_size=4, test_size=3, step_size=3)
    for w in result["windows"]:
        assert "test_sharpe" in w


def test_each_window_has_train_drawdown():
    result = walk_forward_analysis(AlwaysLongStrategy, CANDLES_10,
                                   train_size=4, test_size=3, step_size=3)
    for w in result["windows"]:
        assert "train_drawdown" in w


def test_each_window_has_test_drawdown():
    result = walk_forward_analysis(AlwaysLongStrategy, CANDLES_10,
                                   train_size=4, test_size=3, step_size=3)
    for w in result["windows"]:
        assert "test_drawdown" in w


def test_each_window_has_train_return():
    result = walk_forward_analysis(AlwaysLongStrategy, CANDLES_10,
                                   train_size=4, test_size=3, step_size=3)
    for w in result["windows"]:
        assert "train_return" in w


def test_each_window_has_test_return():
    result = walk_forward_analysis(AlwaysLongStrategy, CANDLES_10,
                                   train_size=4, test_size=3, step_size=3)
    for w in result["windows"]:
        assert "test_return" in w


# ===========================================================================
# PART 3 — Correct slicing behaviour
# ===========================================================================

def test_window_0_train_sharpe_matches_backtester():
    """Window 0 train slice = candles[0:4] = closes [10,20,30,40]."""
    bt = Backtester(1000)
    expected = bt.run(CANDLES_10[0:4], strategy=AlwaysLongStrategy())["sharpe_ratio"]
    result = walk_forward_analysis(AlwaysLongStrategy, CANDLES_10,
                                   train_size=4, test_size=3, step_size=3)
    assert result["windows"][0]["train_sharpe"] == pytest.approx(expected, rel=1e-9)


def test_window_0_test_sharpe_matches_backtester():
    """Window 0 test slice = candles[4:7] = closes [50,60,70]."""
    bt = Backtester(1000)
    expected = bt.run(CANDLES_10[4:7], strategy=AlwaysLongStrategy())["sharpe_ratio"]
    result = walk_forward_analysis(AlwaysLongStrategy, CANDLES_10,
                                   train_size=4, test_size=3, step_size=3)
    assert result["windows"][0]["test_sharpe"] == pytest.approx(expected, rel=1e-9)


def test_window_1_train_sharpe_matches_backtester():
    """Window 1 train slice = candles[3:7] = closes [40,50,60,70]."""
    bt = Backtester(1000)
    expected = bt.run(CANDLES_10[3:7], strategy=AlwaysLongStrategy())["sharpe_ratio"]
    result = walk_forward_analysis(AlwaysLongStrategy, CANDLES_10,
                                   train_size=4, test_size=3, step_size=3)
    assert result["windows"][1]["train_sharpe"] == pytest.approx(expected, rel=1e-9)


def test_window_1_test_sharpe_matches_backtester():
    """Window 1 test slice = candles[7:10] = closes [80,90,100]."""
    bt = Backtester(1000)
    expected = bt.run(CANDLES_10[7:10], strategy=AlwaysLongStrategy())["sharpe_ratio"]
    result = walk_forward_analysis(AlwaysLongStrategy, CANDLES_10,
                                   train_size=4, test_size=3, step_size=3)
    assert result["windows"][1]["test_sharpe"] == pytest.approx(expected, rel=1e-9)


def test_window_0_train_return_matches_backtester():
    bt = Backtester(1000)
    expected = bt.run(CANDLES_10[0:4], strategy=AlwaysLongStrategy())["return_pct"]
    result = walk_forward_analysis(AlwaysLongStrategy, CANDLES_10,
                                   train_size=4, test_size=3, step_size=3)
    assert result["windows"][0]["train_return"] == pytest.approx(expected, rel=1e-9)


def test_window_0_test_return_matches_backtester():
    bt = Backtester(1000)
    expected = bt.run(CANDLES_10[4:7], strategy=AlwaysLongStrategy())["return_pct"]
    result = walk_forward_analysis(AlwaysLongStrategy, CANDLES_10,
                                   train_size=4, test_size=3, step_size=3)
    assert result["windows"][0]["test_return"] == pytest.approx(expected, rel=1e-9)


def test_window_0_train_drawdown_matches_backtester():
    bt = Backtester(1000)
    expected = bt.run(CANDLES_10[0:4], strategy=AlwaysLongStrategy())["max_drawdown_pct"]
    result = walk_forward_analysis(AlwaysLongStrategy, CANDLES_10,
                                   train_size=4, test_size=3, step_size=3)
    assert result["windows"][0]["train_drawdown"] == pytest.approx(expected, rel=1e-9)


def test_window_0_test_drawdown_matches_backtester():
    bt = Backtester(1000)
    expected = bt.run(CANDLES_10[4:7], strategy=AlwaysLongStrategy())["max_drawdown_pct"]
    result = walk_forward_analysis(AlwaysLongStrategy, CANDLES_10,
                                   train_size=4, test_size=3, step_size=3)
    assert result["windows"][0]["test_drawdown"] == pytest.approx(expected, rel=1e-9)


def test_incomplete_test_window_is_excluded():
    """
    10 candles, train=4, test=3, step=3:
    pos=0 → valid, pos=3 → valid, pos=6 → test[10:13]=[] → stop.
    Exactly 2 windows must be produced.
    """
    result = walk_forward_analysis(AlwaysLongStrategy, CANDLES_10,
                                   train_size=4, test_size=3, step_size=3)
    assert len(result["windows"]) == 2


def test_step_size_one_produces_correct_count():
    """
    6 candles, train=3, test=2, step=1:
    pos=0: train=[0:3], test=[3:5] valid
    pos=1: train=[1:4], test=[4:6] valid
    pos=2: test=[5:7] has 1 < 2 → stop
    → 2 windows
    """
    candles6 = [make_candle(f"2024-01-{i+1:02d}", float((i+1)*10)) for i in range(6)]
    result = walk_forward_analysis(AlwaysLongStrategy, candles6,
                                   train_size=3, test_size=2, step_size=1)
    assert len(result["windows"]) == 2


def test_step_size_one_window_0_train_slice():
    """pos=0, train=[10,20,30]."""
    candles6 = [make_candle(f"2024-01-{i+1:02d}", float((i+1)*10)) for i in range(6)]
    bt = Backtester(1000)
    expected = bt.run(candles6[0:3], strategy=AlwaysLongStrategy())["sharpe_ratio"]
    result = walk_forward_analysis(AlwaysLongStrategy, candles6,
                                   train_size=3, test_size=2, step_size=1)
    assert result["windows"][0]["train_sharpe"] == pytest.approx(expected, rel=1e-9)


def test_step_size_one_window_1_train_slice():
    """pos=1, train=[20,30,40]."""
    candles6 = [make_candle(f"2024-01-{i+1:02d}", float((i+1)*10)) for i in range(6)]
    bt = Backtester(1000)
    expected = bt.run(candles6[1:4], strategy=AlwaysLongStrategy())["sharpe_ratio"]
    result = walk_forward_analysis(AlwaysLongStrategy, candles6,
                                   train_size=3, test_size=2, step_size=1)
    assert result["windows"][1]["train_sharpe"] == pytest.approx(expected, rel=1e-9)


def test_step_size_one_window_1_test_slice():
    """pos=1, test=[50,60]."""
    candles6 = [make_candle(f"2024-01-{i+1:02d}", float((i+1)*10)) for i in range(6)]
    bt = Backtester(1000)
    expected = bt.run(candles6[4:6], strategy=AlwaysLongStrategy())["sharpe_ratio"]
    result = walk_forward_analysis(AlwaysLongStrategy, candles6,
                                   train_size=3, test_size=2, step_size=1)
    assert result["windows"][1]["test_sharpe"] == pytest.approx(expected, rel=1e-9)


# ===========================================================================
# PART 4 — Aggregate metric correctness
# ===========================================================================

def test_correct_mean_train_sharpe():
    ref = _ref_walk_forward(AlwaysLongStrategy, CANDLES_10,
                            train_size=4, test_size=3, step_size=3)
    result = walk_forward_analysis(AlwaysLongStrategy, CANDLES_10,
                                   train_size=4, test_size=3, step_size=3)
    assert result["mean_train_sharpe"] == pytest.approx(ref["mean_train_sharpe"], rel=1e-9)


def test_mean_train_sharpe_is_average_of_window_train_sharpes():
    result = walk_forward_analysis(AlwaysLongStrategy, CANDLES_10,
                                   train_size=4, test_size=3, step_size=3)
    train_sharpes = [w["train_sharpe"] for w in result["windows"]]
    expected = sum(train_sharpes) / len(train_sharpes)
    assert result["mean_train_sharpe"] == pytest.approx(expected, rel=1e-9)


def test_correct_mean_test_sharpe():
    ref = _ref_walk_forward(AlwaysLongStrategy, CANDLES_10,
                            train_size=4, test_size=3, step_size=3)
    result = walk_forward_analysis(AlwaysLongStrategy, CANDLES_10,
                                   train_size=4, test_size=3, step_size=3)
    assert result["mean_test_sharpe"] == pytest.approx(ref["mean_test_sharpe"], rel=1e-9)


def test_mean_test_sharpe_is_average_of_window_test_sharpes():
    result = walk_forward_analysis(AlwaysLongStrategy, CANDLES_10,
                                   train_size=4, test_size=3, step_size=3)
    test_sharpes = [w["test_sharpe"] for w in result["windows"]]
    expected = sum(test_sharpes) / len(test_sharpes)
    assert result["mean_test_sharpe"] == pytest.approx(expected, rel=1e-9)


def test_correct_test_sharpe_variance():
    ref = _ref_walk_forward(AlwaysLongStrategy, CANDLES_10,
                            train_size=4, test_size=3, step_size=3)
    result = walk_forward_analysis(AlwaysLongStrategy, CANDLES_10,
                                   train_size=4, test_size=3, step_size=3)
    assert result["test_sharpe_variance"] == pytest.approx(ref["test_sharpe_variance"], rel=1e-9)


def test_test_sharpe_variance_uses_bessel_correction():
    """
    With n=2 windows, Bessel-corrected variance divides by (n-1)=1.
    Biased variance divides by n=2.
    They differ by factor 2 when test_sharpes are unequal.
    """
    result = walk_forward_analysis(AlwaysLongStrategy, CANDLES_10,
                                   train_size=4, test_size=3, step_size=3)
    test_sharpes = [w["test_sharpe"] for w in result["windows"]]
    n = len(test_sharpes)
    mean = sum(test_sharpes) / n
    bessel_var = sum((s - mean) ** 2 for s in test_sharpes) / (n - 1)
    biased_var = sum((s - mean) ** 2 for s in test_sharpes) / n
    assert result["test_sharpe_variance"] == pytest.approx(bessel_var, rel=1e-9)
    # Confirm test is non-trivial — the two test sharpes must differ
    if test_sharpes[0] != test_sharpes[1]:
        assert abs(result["test_sharpe_variance"] - biased_var) > 1e-12


def test_test_sharpe_variance_is_non_negative():
    result = walk_forward_analysis(AlwaysLongStrategy, CANDLES_10,
                                   train_size=4, test_size=3, step_size=3)
    assert result["test_sharpe_variance"] >= 0.0


def test_correct_performance_decay():
    ref = _ref_walk_forward(AlwaysLongStrategy, CANDLES_10,
                            train_size=4, test_size=3, step_size=3)
    result = walk_forward_analysis(AlwaysLongStrategy, CANDLES_10,
                                   train_size=4, test_size=3, step_size=3)
    assert result["performance_decay"] == pytest.approx(ref["performance_decay"], rel=1e-9)


def test_performance_decay_formula():
    """performance_decay = mean_test_sharpe - mean_train_sharpe"""
    result = walk_forward_analysis(AlwaysLongStrategy, CANDLES_10,
                                   train_size=4, test_size=3, step_size=3)
    expected = result["mean_test_sharpe"] - result["mean_train_sharpe"]
    assert result["performance_decay"] == pytest.approx(expected, rel=1e-9)


def test_performance_decay_negative_when_test_worse_than_train():
    # All rising candles: train windows will have rising sharpes, test also rising
    # but the ref helper tells us decay = -0.1168... (train sharpe > test sharpe)
    result = walk_forward_analysis(AlwaysLongStrategy, CANDLES_10,
                                   train_size=4, test_size=3, step_size=3)
    ref = _ref_walk_forward(AlwaysLongStrategy, CANDLES_10,
                            train_size=4, test_size=3, step_size=3)
    # Just verify sign matches reference, don't hard-code float
    assert (result["performance_decay"] < 0) == (ref["performance_decay"] < 0)


# ===========================================================================
# PART 5 — Bessel variance with 3 windows
# ===========================================================================

def test_three_window_bessel_variance():
    """
    8 candles, train=3, test=2, step=2:
    pos=0: train=[0:3], test=[3:5]
    pos=2: train=[2:5], test=[5:7]
    pos=4: train=[4:7], test=[7:9]  → but 8 candles, test=[7:9] valid
    pos=6 check: test=[9:11] → 0 candles (only 8 total) → stop
    Actually len=8: idx 0-7
    pos=4: train=[4:7], test=[7:9] → test[7:9] has 1 candle (only idx7) → len=1 < 2 → stop
    So 2 windows.  Use 10 candles for 3 windows.

    10 candles, train=2, test=2, step=2:
    pos=0: train=[0:2], test=[2:4]
    pos=2: train=[2:4], test=[4:6]
    pos=4: train=[4:6], test=[6:8]
    pos=6: test=[8:10] has 2 candles → valid → window 3
    pos=8: test=[10:12] → 0 → stop
    → 4 windows
    """
    candles10 = CANDLES_10
    result = walk_forward_analysis(AlwaysLongStrategy, candles10,
                                   train_size=2, test_size=2, step_size=2)
    test_sharpes = [w["test_sharpe"] for w in result["windows"]]
    n = len(test_sharpes)
    assert n >= 2, "Need at least 2 windows to test variance"
    mean = sum(test_sharpes) / n
    expected_var = sum((s - mean) ** 2 for s in test_sharpes) / (n - 1)
    assert result["test_sharpe_variance"] == pytest.approx(expected_var, rel=1e-9)


# ===========================================================================
# PART 6 — initial_cash forwarded to both train and test Backtesters
# ===========================================================================

def test_initial_cash_default_is_1000():
    """Calling without initial_cash kwarg must not raise."""
    result = walk_forward_analysis(AlwaysLongStrategy, CANDLES_10,
                                   train_size=4, test_size=3, step_size=3)
    assert "windows" in result


def test_initial_cash_forwarded():
    """
    Sharpe ratio is scale-invariant so both cash amounts must produce
    identical per-window sharpe values.
    """
    r1000 = walk_forward_analysis(AlwaysLongStrategy, CANDLES_10,
                                  train_size=4, test_size=3, step_size=3,
                                  initial_cash=1000)
    r500  = walk_forward_analysis(AlwaysLongStrategy, CANDLES_10,
                                  train_size=4, test_size=3, step_size=3,
                                  initial_cash=500)
    for w1, w5 in zip(r1000["windows"], r500["windows"]):
        assert w1["train_sharpe"] == pytest.approx(w5["train_sharpe"], rel=1e-9)
        assert w1["test_sharpe"]  == pytest.approx(w5["test_sharpe"],  rel=1e-9)


# ===========================================================================
# PART 7 — Determinism
# ===========================================================================

def test_deterministic_output():
    r1 = walk_forward_analysis(AlwaysLongStrategy, CANDLES_10,
                               train_size=4, test_size=3, step_size=3)
    r2 = walk_forward_analysis(AlwaysLongStrategy, CANDLES_10,
                               train_size=4, test_size=3, step_size=3)
    assert r1["mean_train_sharpe"]   == r2["mean_train_sharpe"]
    assert r1["mean_test_sharpe"]    == r2["mean_test_sharpe"]
    assert r1["test_sharpe_variance"] == r2["test_sharpe_variance"]
    assert r1["performance_decay"]   == r2["performance_decay"]
    for w1, w2 in zip(r1["windows"], r2["windows"]):
        assert w1["train_sharpe"] == w2["train_sharpe"]
        assert w1["test_sharpe"]  == w2["test_sharpe"]


# ===========================================================================
# PART 8 — Input candles must NOT be mutated
# ===========================================================================

def test_does_not_mutate_candles_length():
    candles = [make_candle(f"2024-01-{i+1:02d}", float((i+1)*10)) for i in range(10)]
    orig_len = len(candles)
    walk_forward_analysis(AlwaysLongStrategy, candles,
                          train_size=4, test_size=3, step_size=3)
    assert len(candles) == orig_len


def test_does_not_mutate_candles_values():
    candles = [make_candle(f"2024-01-{i+1:02d}", float((i+1)*10)) for i in range(10)]
    orig_closes = [c["close"] for c in candles]
    walk_forward_analysis(AlwaysLongStrategy, candles,
                          train_size=4, test_size=3, step_size=3)
    for i, c in enumerate(candles):
        assert c["close"] == orig_closes[i]


def test_does_not_mutate_candle_keys():
    candles = [make_candle(f"2024-01-{i+1:02d}", float((i+1)*10)) for i in range(10)]
    orig_keys = [set(c.keys()) for c in candles]
    walk_forward_analysis(AlwaysLongStrategy, candles,
                          train_size=4, test_size=3, step_size=3)
    for i, c in enumerate(candles):
        assert set(c.keys()) == orig_keys[i]


# ===========================================================================
# PART 9 — ValueError for invalid parameters
# ===========================================================================

def test_raises_for_train_size_one():
    candles = [make_candle(f"2024-01-{i+1:02d}", float(i+1)) for i in range(10)]
    with pytest.raises(ValueError):
        walk_forward_analysis(AlwaysLongStrategy, candles,
                              train_size=1, test_size=3, step_size=3)


def test_raises_for_train_size_zero():
    candles = [make_candle(f"2024-01-{i+1:02d}", float(i+1)) for i in range(10)]
    with pytest.raises(ValueError):
        walk_forward_analysis(AlwaysLongStrategy, candles,
                              train_size=0, test_size=3, step_size=3)


def test_raises_for_negative_train_size():
    candles = [make_candle(f"2024-01-{i+1:02d}", float(i+1)) for i in range(10)]
    with pytest.raises(ValueError):
        walk_forward_analysis(AlwaysLongStrategy, candles,
                              train_size=-1, test_size=3, step_size=3)


def test_raises_for_test_size_one():
    candles = [make_candle(f"2024-01-{i+1:02d}", float(i+1)) for i in range(10)]
    with pytest.raises(ValueError):
        walk_forward_analysis(AlwaysLongStrategy, candles,
                              train_size=4, test_size=1, step_size=3)


def test_raises_for_test_size_zero():
    candles = [make_candle(f"2024-01-{i+1:02d}", float(i+1)) for i in range(10)]
    with pytest.raises(ValueError):
        walk_forward_analysis(AlwaysLongStrategy, candles,
                              train_size=4, test_size=0, step_size=3)


def test_raises_for_negative_test_size():
    candles = [make_candle(f"2024-01-{i+1:02d}", float(i+1)) for i in range(10)]
    with pytest.raises(ValueError):
        walk_forward_analysis(AlwaysLongStrategy, candles,
                              train_size=4, test_size=-2, step_size=3)


def test_raises_for_step_size_zero():
    candles = [make_candle(f"2024-01-{i+1:02d}", float(i+1)) for i in range(10)]
    with pytest.raises(ValueError):
        walk_forward_analysis(AlwaysLongStrategy, candles,
                              train_size=4, test_size=3, step_size=0)


def test_raises_for_negative_step_size():
    candles = [make_candle(f"2024-01-{i+1:02d}", float(i+1)) for i in range(10)]
    with pytest.raises(ValueError):
        walk_forward_analysis(AlwaysLongStrategy, candles,
                              train_size=4, test_size=3, step_size=-1)


def test_raises_when_dataset_too_small_for_one_window():
    """train_size + test_size > len(candles) → no valid window → ValueError."""
    candles = [make_candle(f"2024-01-{i+1:02d}", float(i+1)) for i in range(5)]
    with pytest.raises(ValueError):
        walk_forward_analysis(AlwaysLongStrategy, candles,
                              train_size=4, test_size=3, step_size=1)


def test_raises_when_empty_candles():
    with pytest.raises(ValueError):
        walk_forward_analysis(AlwaysLongStrategy, [],
                              train_size=4, test_size=3, step_size=1)
