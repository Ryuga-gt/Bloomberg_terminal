"""
Tests for execution.execution_gateway.ExecutionGateway

Contract
--------
ExecutionGateway(strategy_class: type, initial_cash: float = 1000)

    on_candle(candle: dict) -> None
        Processes one candle; calls strategy.generate_signal(candle).
        Signals: "BUY" | "SELL" | "HOLD"
        All-in execution model.
        Redundant signals silently ignored.
        Candle must contain "close" → KeyError otherwise.

    get_state() -> dict
        Returns:
            cash, position_size, equity, equity_curve,
            trade_history, state

Validation
----------
    initial_cash <= 0 → ValueError
    candle without "close" → KeyError

Test strategies defined in this file:
    AlwaysBuyFirst   — BUY on first candle, HOLD thereafter
    AlwaysBuyHold    — BUY on every candle (tests redundant BUY)
    AlwaysBuySell    — alternates BUY / SELL
    AlwaysFlat       — always HOLD
"""

import pytest

from execution.execution_gateway import ExecutionGateway


# ---------------------------------------------------------------------------
# Candle factory
# ---------------------------------------------------------------------------

def make_candle(close: float) -> dict:
    return {
        "open":   close,
        "high":   close,
        "low":    close,
        "close":  close,
        "volume": 1_000_000,
    }


# ---------------------------------------------------------------------------
# Test strategy classes
# ---------------------------------------------------------------------------

class AlwaysBuyFirst:
    """BUY on the first candle, HOLD on all subsequent candles."""
    def __init__(self):
        self._called = False

    def generate_signal(self, candle: dict) -> str:
        if not self._called:
            self._called = True
            return "BUY"
        return "HOLD"


class AlwaysBuyHold:
    """Always returns BUY (tests redundant BUY when already LONG)."""
    def generate_signal(self, candle: dict) -> str:
        return "BUY"


class AlwaysBuySell:
    """Alternates BUY / SELL starting with BUY."""
    def __init__(self):
        self._count = 0

    def generate_signal(self, candle: dict) -> str:
        signal = "BUY" if self._count % 2 == 0 else "SELL"
        self._count += 1
        return signal


class AlwaysFlat:
    """Always returns HOLD — never trades."""
    def generate_signal(self, candle: dict) -> str:
        return "HOLD"


class AlwaysSell:
    """Always returns SELL (tests redundant SELL when FLAT)."""
    def generate_signal(self, candle: dict) -> str:
        return "SELL"


# ===========================================================================
# Part 1 — Validation
# ===========================================================================

def test_initial_cash_zero_raises_value_error():
    with pytest.raises(ValueError):
        ExecutionGateway(AlwaysFlat, initial_cash=0)


def test_initial_cash_negative_raises_value_error():
    with pytest.raises(ValueError):
        ExecutionGateway(AlwaysFlat, initial_cash=-100)


def test_candle_without_close_raises_key_error():
    gateway = ExecutionGateway(AlwaysFlat)
    with pytest.raises(KeyError):
        gateway.on_candle({"open": 100, "high": 100, "low": 100})


def test_candle_empty_dict_raises_key_error():
    gateway = ExecutionGateway(AlwaysFlat)
    with pytest.raises(KeyError):
        gateway.on_candle({})


# ===========================================================================
# Part 2 — BUY on first candle allocates shares correctly
# ===========================================================================

def test_buy_first_candle_shares_allocated():
    """BUY at price 100 with cash 1000 → 10 shares."""
    gateway = ExecutionGateway(AlwaysBuyFirst, initial_cash=1000)
    gateway.on_candle(make_candle(100.0))
    state = gateway.get_state()
    assert state["position_size"] == pytest.approx(10.0)


def test_buy_first_candle_cash_is_zero():
    gateway = ExecutionGateway(AlwaysBuyFirst, initial_cash=1000)
    gateway.on_candle(make_candle(100.0))
    state = gateway.get_state()
    assert state["cash"] == pytest.approx(0.0)


def test_buy_first_candle_state_is_long():
    gateway = ExecutionGateway(AlwaysBuyFirst, initial_cash=1000)
    gateway.on_candle(make_candle(100.0))
    state = gateway.get_state()
    assert state["state"] == "LONG"


def test_buy_first_candle_trade_history_length_one():
    gateway = ExecutionGateway(AlwaysBuyFirst, initial_cash=1000)
    gateway.on_candle(make_candle(100.0))
    state = gateway.get_state()
    assert len(state["trade_history"]) == 1


def test_buy_first_candle_trade_type_is_buy():
    gateway = ExecutionGateway(AlwaysBuyFirst, initial_cash=1000)
    gateway.on_candle(make_candle(100.0))
    state = gateway.get_state()
    assert state["trade_history"][0]["type"] == "BUY"


def test_buy_first_candle_trade_price_correct():
    gateway = ExecutionGateway(AlwaysBuyFirst, initial_cash=1000)
    gateway.on_candle(make_candle(100.0))
    state = gateway.get_state()
    assert state["trade_history"][0]["price"] == pytest.approx(100.0)


def test_buy_first_candle_trade_shares_correct():
    gateway = ExecutionGateway(AlwaysBuyFirst, initial_cash=1000)
    gateway.on_candle(make_candle(100.0))
    state = gateway.get_state()
    assert state["trade_history"][0]["shares"] == pytest.approx(10.0)


def test_buy_first_candle_trade_cash_after_is_zero():
    gateway = ExecutionGateway(AlwaysBuyFirst, initial_cash=1000)
    gateway.on_candle(make_candle(100.0))
    state = gateway.get_state()
    assert state["trade_history"][0]["cash_after"] == pytest.approx(0.0)


# ===========================================================================
# Part 3 — SELL closes position
# ===========================================================================

def test_sell_closes_position_position_size_zero():
    gateway = ExecutionGateway(AlwaysBuySell, initial_cash=1000)
    gateway.on_candle(make_candle(100.0))  # BUY
    gateway.on_candle(make_candle(200.0))  # SELL
    state = gateway.get_state()
    assert state["position_size"] == pytest.approx(0.0)


def test_sell_closes_position_state_is_flat():
    gateway = ExecutionGateway(AlwaysBuySell, initial_cash=1000)
    gateway.on_candle(make_candle(100.0))  # BUY
    gateway.on_candle(make_candle(200.0))  # SELL
    state = gateway.get_state()
    assert state["state"] == "FLAT"


def test_sell_closes_position_cash_correct():
    """Buy 10 shares at 100, sell at 200 → cash = 2000."""
    gateway = ExecutionGateway(AlwaysBuySell, initial_cash=1000)
    gateway.on_candle(make_candle(100.0))  # BUY → 10 shares
    gateway.on_candle(make_candle(200.0))  # SELL → 10 * 200 = 2000
    state = gateway.get_state()
    assert state["cash"] == pytest.approx(2000.0)


def test_sell_trade_history_length_two():
    gateway = ExecutionGateway(AlwaysBuySell, initial_cash=1000)
    gateway.on_candle(make_candle(100.0))  # BUY
    gateway.on_candle(make_candle(200.0))  # SELL
    state = gateway.get_state()
    assert len(state["trade_history"]) == 2


def test_sell_trade_type_is_sell():
    gateway = ExecutionGateway(AlwaysBuySell, initial_cash=1000)
    gateway.on_candle(make_candle(100.0))  # BUY
    gateway.on_candle(make_candle(200.0))  # SELL
    state = gateway.get_state()
    assert state["trade_history"][1]["type"] == "SELL"


def test_sell_trade_price_correct():
    gateway = ExecutionGateway(AlwaysBuySell, initial_cash=1000)
    gateway.on_candle(make_candle(100.0))  # BUY
    gateway.on_candle(make_candle(200.0))  # SELL
    state = gateway.get_state()
    assert state["trade_history"][1]["price"] == pytest.approx(200.0)


# ===========================================================================
# Part 4 — Redundant BUY ignored
# ===========================================================================

def test_redundant_buy_ignored_trade_history_length_one():
    """AlwaysBuyHold sends BUY every candle; only first should execute."""
    gateway = ExecutionGateway(AlwaysBuyHold, initial_cash=1000)
    gateway.on_candle(make_candle(100.0))  # BUY → LONG
    gateway.on_candle(make_candle(110.0))  # BUY again → ignored
    gateway.on_candle(make_candle(120.0))  # BUY again → ignored
    state = gateway.get_state()
    assert len(state["trade_history"]) == 1


def test_redundant_buy_ignored_position_unchanged():
    gateway = ExecutionGateway(AlwaysBuyHold, initial_cash=1000)
    gateway.on_candle(make_candle(100.0))  # BUY → 10 shares
    gateway.on_candle(make_candle(110.0))  # BUY → ignored
    state = gateway.get_state()
    assert state["position_size"] == pytest.approx(10.0)


# ===========================================================================
# Part 5 — Redundant SELL ignored
# ===========================================================================

def test_redundant_sell_ignored_trade_history_empty():
    """AlwaysSell sends SELL every candle; none should execute (starts FLAT)."""
    gateway = ExecutionGateway(AlwaysSell, initial_cash=1000)
    gateway.on_candle(make_candle(100.0))
    gateway.on_candle(make_candle(110.0))
    state = gateway.get_state()
    assert len(state["trade_history"]) == 0


def test_redundant_sell_after_close_ignored():
    """BUY then SELL then SELL again — second SELL must be ignored."""
    gateway = ExecutionGateway(AlwaysBuySell, initial_cash=1000)
    gateway.on_candle(make_candle(100.0))  # BUY
    gateway.on_candle(make_candle(200.0))  # SELL → FLAT
    gateway.on_candle(make_candle(300.0))  # BUY (3rd candle, count=2 → even → BUY)
    gateway.on_candle(make_candle(400.0))  # SELL
    # Only 4 trades total (2 BUY + 2 SELL)
    state = gateway.get_state()
    assert len(state["trade_history"]) == 4


# ===========================================================================
# Part 6 — Equity updates correctly
# ===========================================================================

def test_equity_before_any_candle_not_in_curve():
    gateway = ExecutionGateway(AlwaysFlat, initial_cash=1000)
    state = gateway.get_state()
    assert state["equity_curve"] == []


def test_equity_flat_strategy_equals_initial_cash():
    gateway = ExecutionGateway(AlwaysFlat, initial_cash=1000)
    gateway.on_candle(make_candle(100.0))
    state = gateway.get_state()
    assert state["equity"] == pytest.approx(1000.0)


def test_equity_after_buy_equals_initial_cash():
    """After BUY at 100 with 1000 cash: equity = 0 + 10 * 100 = 1000."""
    gateway = ExecutionGateway(AlwaysBuyFirst, initial_cash=1000)
    gateway.on_candle(make_candle(100.0))
    state = gateway.get_state()
    assert state["equity"] == pytest.approx(1000.0)


def test_equity_increases_with_price_rise():
    """Buy at 100, price rises to 200: equity = 0 + 10 * 200 = 2000."""
    gateway = ExecutionGateway(AlwaysBuyFirst, initial_cash=1000)
    gateway.on_candle(make_candle(100.0))  # BUY
    gateway.on_candle(make_candle(200.0))  # HOLD
    state = gateway.get_state()
    assert state["equity"] == pytest.approx(2000.0)


def test_equity_after_sell_equals_cash():
    """After SELL, equity = cash (no position)."""
    gateway = ExecutionGateway(AlwaysBuySell, initial_cash=1000)
    gateway.on_candle(make_candle(100.0))  # BUY
    gateway.on_candle(make_candle(200.0))  # SELL → cash = 2000
    state = gateway.get_state()
    assert state["equity"] == pytest.approx(state["cash"])


# ===========================================================================
# Part 7 — equity_curve length matches number of candles
# ===========================================================================

def test_equity_curve_length_one_candle():
    gateway = ExecutionGateway(AlwaysFlat, initial_cash=1000)
    gateway.on_candle(make_candle(100.0))
    state = gateway.get_state()
    assert len(state["equity_curve"]) == 1


def test_equity_curve_length_five_candles():
    gateway = ExecutionGateway(AlwaysFlat, initial_cash=1000)
    for price in [100, 110, 120, 130, 140]:
        gateway.on_candle(make_candle(float(price)))
    state = gateway.get_state()
    assert len(state["equity_curve"]) == 5


def test_equity_curve_values_flat_strategy():
    """Flat strategy: equity_curve should be constant at initial_cash."""
    gateway = ExecutionGateway(AlwaysFlat, initial_cash=1000)
    for price in [100, 200, 300]:
        gateway.on_candle(make_candle(float(price)))
    state = gateway.get_state()
    assert all(v == pytest.approx(1000.0) for v in state["equity_curve"])


def test_equity_curve_values_after_buy():
    """Buy at 100 (10 shares), then prices 110, 120 → equity 1100, 1200."""
    gateway = ExecutionGateway(AlwaysBuyFirst, initial_cash=1000)
    gateway.on_candle(make_candle(100.0))  # BUY → equity 1000
    gateway.on_candle(make_candle(110.0))  # HOLD → equity 1100
    gateway.on_candle(make_candle(120.0))  # HOLD → equity 1200
    state = gateway.get_state()
    assert state["equity_curve"] == pytest.approx([1000.0, 1100.0, 1200.0])


# ===========================================================================
# Part 8 — Flat strategy results in zero trades
# ===========================================================================

def test_flat_strategy_zero_trades():
    gateway = ExecutionGateway(AlwaysFlat, initial_cash=1000)
    for price in [100, 110, 120, 130]:
        gateway.on_candle(make_candle(float(price)))
    state = gateway.get_state()
    assert len(state["trade_history"]) == 0


def test_flat_strategy_state_remains_flat():
    gateway = ExecutionGateway(AlwaysFlat, initial_cash=1000)
    for price in [100, 110, 120]:
        gateway.on_candle(make_candle(float(price)))
    state = gateway.get_state()
    assert state["state"] == "FLAT"


def test_flat_strategy_cash_unchanged():
    gateway = ExecutionGateway(AlwaysFlat, initial_cash=1000)
    for price in [100, 110, 120]:
        gateway.on_candle(make_candle(float(price)))
    state = gateway.get_state()
    assert state["cash"] == pytest.approx(1000.0)


# ===========================================================================
# Part 9 — State string correctness
# ===========================================================================

def test_initial_state_is_flat():
    gateway = ExecutionGateway(AlwaysFlat, initial_cash=1000)
    state = gateway.get_state()
    assert state["state"] == "FLAT"


def test_state_is_long_after_buy():
    gateway = ExecutionGateway(AlwaysBuyFirst, initial_cash=1000)
    gateway.on_candle(make_candle(100.0))
    state = gateway.get_state()
    assert state["state"] == "LONG"


def test_state_is_flat_after_sell():
    gateway = ExecutionGateway(AlwaysBuySell, initial_cash=1000)
    gateway.on_candle(make_candle(100.0))  # BUY → LONG
    gateway.on_candle(make_candle(200.0))  # SELL → FLAT
    state = gateway.get_state()
    assert state["state"] == "FLAT"


# ===========================================================================
# Part 10 — Deterministic behavior
# ===========================================================================

def test_deterministic_same_candles_same_result():
    candles = [make_candle(float(100 + i * 10)) for i in range(5)]

    gateway1 = ExecutionGateway(AlwaysBuyFirst, initial_cash=1000)
    for c in candles:
        gateway1.on_candle(c)
    state1 = gateway1.get_state()

    gateway2 = ExecutionGateway(AlwaysBuyFirst, initial_cash=1000)
    for c in candles:
        gateway2.on_candle(c)
    state2 = gateway2.get_state()

    assert state1["equity_curve"] == pytest.approx(state2["equity_curve"])
    assert state1["trade_history"] == state2["trade_history"]
    assert state1["cash"] == pytest.approx(state2["cash"])
    assert state1["position_size"] == pytest.approx(state2["position_size"])


# ===========================================================================
# Part 11 — Input candles are not mutated
# ===========================================================================

def test_on_candle_does_not_mutate_input():
    candle = make_candle(100.0)
    original = dict(candle)
    gateway = ExecutionGateway(AlwaysBuyFirst, initial_cash=1000)
    gateway.on_candle(candle)
    assert candle == original


# ===========================================================================
# Part 12 — get_state returns copies (not internal references)
# ===========================================================================

def test_get_state_equity_curve_is_copy():
    gateway = ExecutionGateway(AlwaysFlat, initial_cash=1000)
    gateway.on_candle(make_candle(100.0))
    state = gateway.get_state()
    state["equity_curve"].append(9999.0)
    # Internal curve must not be affected
    state2 = gateway.get_state()
    assert len(state2["equity_curve"]) == 1


def test_get_state_trade_history_is_copy():
    gateway = ExecutionGateway(AlwaysBuyFirst, initial_cash=1000)
    gateway.on_candle(make_candle(100.0))
    state = gateway.get_state()
    state["trade_history"].append({"type": "FAKE"})
    state2 = gateway.get_state()
    assert len(state2["trade_history"]) == 1


# ===========================================================================
# Part 13 — default initial_cash is 1000
# ===========================================================================

def test_default_initial_cash_is_1000():
    gateway = ExecutionGateway(AlwaysFlat)
    state = gateway.get_state()
    assert state["cash"] == pytest.approx(1000.0)
