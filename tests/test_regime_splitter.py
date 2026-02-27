"""
RED tests for research.regime_splitter.split_into_time_windows

Contract:
    split_into_time_windows(candles: list[dict], window_size: int)
        -> list[list[dict]]

Requirements:
    - Deterministic
    - Does NOT mutate input list or any candle dict
    - Splits candles sequentially (chronological order)
    - Each window must have at least 2 candles
    - Raises ValueError if total candles < window_size
    - Raises ValueError if window_size < 2
    - Last window is allowed only if len >= 2 (short tail with 1 candle is dropped)
    - Returns windows in chronological order
"""

import pytest

from research.regime_splitter import split_into_time_windows

# ---------------------------------------------------------------------------
# Shared candle factory
# ---------------------------------------------------------------------------

def make_candles(n: int) -> list[dict]:
    """Return n minimal candles with sequential timestamps and close = i+1."""
    return [
        {
            "timestamp": f"2024-01-{i+1:02d}",
            "open":  float(i + 1),
            "high":  float(i + 1),
            "low":   float(i + 1),
            "close": float(i + 1),
            "volume": 1_000_000,
        }
        for i in range(n)
    ]


# ---------------------------------------------------------------------------
# Return type
# ---------------------------------------------------------------------------

def test_returns_list():
    candles = make_candles(6)
    result = split_into_time_windows(candles, window_size=3)
    assert isinstance(result, list)


def test_each_window_is_list():
    candles = make_candles(6)
    result = split_into_time_windows(candles, window_size=3)
    for w in result:
        assert isinstance(w, list)


# ---------------------------------------------------------------------------
# Equal-size windows (no remainder)
# 6 candles, window_size=3 → 2 windows of 3
# ---------------------------------------------------------------------------

def test_equal_windows_count():
    candles = make_candles(6)
    result = split_into_time_windows(candles, window_size=3)
    assert len(result) == 2


def test_equal_windows_each_length():
    candles = make_candles(6)
    result = split_into_time_windows(candles, window_size=3)
    for w in result:
        assert len(w) == 3


def test_equal_windows_correct_candles_first():
    candles = make_candles(6)
    result = split_into_time_windows(candles, window_size=3)
    # First window must be candles[0:3]
    assert result[0] == candles[0:3]


def test_equal_windows_correct_candles_second():
    candles = make_candles(6)
    result = split_into_time_windows(candles, window_size=3)
    # Second window must be candles[3:6]
    assert result[1] == candles[3:6]


# ---------------------------------------------------------------------------
# Shorter last window (remainder >= 2 is kept)
# 7 candles, window_size=3 → windows [0:3], [3:6], [6:7]
# [6:7] has length 1 → dropped → 2 windows
# 8 candles, window_size=3 → windows [0:3], [3:6], [6:8]
# [6:8] has length 2 → KEPT → 3 windows
# ---------------------------------------------------------------------------

def test_short_tail_of_one_is_dropped():
    candles = make_candles(7)
    result = split_into_time_windows(candles, window_size=3)
    assert len(result) == 2


def test_short_tail_of_two_is_kept():
    candles = make_candles(8)
    result = split_into_time_windows(candles, window_size=3)
    assert len(result) == 3


def test_short_tail_of_two_content():
    candles = make_candles(8)
    result = split_into_time_windows(candles, window_size=3)
    # Last window should be candles[6:8]
    assert result[-1] == candles[6:8]


def test_short_tail_of_two_length():
    candles = make_candles(8)
    result = split_into_time_windows(candles, window_size=3)
    assert len(result[-1]) == 2


# ---------------------------------------------------------------------------
# Chronological order
# ---------------------------------------------------------------------------

def test_windows_in_chronological_order():
    candles = make_candles(9)
    result = split_into_time_windows(candles, window_size=3)
    # Each window's first candle close should be strictly increasing
    first_closes = [w[0]["close"] for w in result]
    assert first_closes == sorted(first_closes)


def test_windows_cover_all_candles_no_overlap():
    candles = make_candles(6)
    result = split_into_time_windows(candles, window_size=2)
    # Flatten and check every candle appears exactly once
    flat = [c for w in result for c in w]
    assert flat == candles


# ---------------------------------------------------------------------------
# Minimum window_size = 2 (the smallest valid window produces 1 window per pair)
# ---------------------------------------------------------------------------

def test_window_size_two_on_two_candles():
    candles = make_candles(2)
    result = split_into_time_windows(candles, window_size=2)
    assert len(result) == 1
    assert result[0] == candles


def test_window_size_two_on_four_candles():
    candles = make_candles(4)
    result = split_into_time_windows(candles, window_size=2)
    assert len(result) == 2
    assert result[0] == candles[0:2]
    assert result[1] == candles[2:4]


# ---------------------------------------------------------------------------
# ValueError: window_size < 2
# ---------------------------------------------------------------------------

def test_raises_for_window_size_one():
    candles = make_candles(10)
    with pytest.raises(ValueError):
        split_into_time_windows(candles, window_size=1)


def test_raises_for_window_size_zero():
    candles = make_candles(10)
    with pytest.raises(ValueError):
        split_into_time_windows(candles, window_size=0)


def test_raises_for_negative_window_size():
    candles = make_candles(10)
    with pytest.raises(ValueError):
        split_into_time_windows(candles, window_size=-5)


# ---------------------------------------------------------------------------
# ValueError: total candles < window_size
# ---------------------------------------------------------------------------

def test_raises_when_candles_less_than_window_size():
    candles = make_candles(3)
    with pytest.raises(ValueError):
        split_into_time_windows(candles, window_size=5)


def test_raises_when_candles_equal_to_one():
    candles = make_candles(1)
    with pytest.raises(ValueError):
        split_into_time_windows(candles, window_size=2)


def test_raises_when_empty_candles():
    with pytest.raises(ValueError):
        split_into_time_windows([], window_size=2)


# ---------------------------------------------------------------------------
# Input list must NOT be mutated
# ---------------------------------------------------------------------------

def test_input_list_not_mutated_length():
    candles = make_candles(6)
    original_len = len(candles)
    split_into_time_windows(candles, window_size=3)
    assert len(candles) == original_len


def test_input_list_not_mutated_order():
    candles = make_candles(6)
    original_closes = [c["close"] for c in candles]
    split_into_time_windows(candles, window_size=3)
    for i, c in enumerate(candles):
        assert c["close"] == original_closes[i]


def test_input_candle_dicts_not_mutated():
    candles = make_candles(6)
    original_keys_per_candle = [set(c.keys()) for c in candles]
    original_closes = [c["close"] for c in candles]
    split_into_time_windows(candles, window_size=3)
    for i, c in enumerate(candles):
        assert set(c.keys()) == original_keys_per_candle[i]
        assert c["close"] == original_closes[i]


# ---------------------------------------------------------------------------
# Determinism — same inputs must produce identical outputs
# ---------------------------------------------------------------------------

def test_deterministic_output():
    candles = make_candles(9)
    result1 = split_into_time_windows(candles, window_size=3)
    result2 = split_into_time_windows(candles, window_size=3)
    assert result1 == result2


# ---------------------------------------------------------------------------
# Windows are independent copies (modifying a returned window does not
# alter the original candles list or other windows)
# ---------------------------------------------------------------------------

def test_returned_windows_are_independent_copies():
    candles = make_candles(6)
    result = split_into_time_windows(candles, window_size=3)
    # Mutate the first candle in the first window
    result[0][0]["close"] = 9999.0
    # Original candles[0] must be unchanged
    assert candles[0]["close"] == 1.0
