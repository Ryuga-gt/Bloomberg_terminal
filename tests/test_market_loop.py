"""
Tests for execution.market_loop.MarketLoop

Contract
--------
MarketLoop(gateway: ExecutionGateway)

    run(candles: list[dict]) -> dict
        Feeds every candle to gateway.on_candle() in order.
        Returns gateway.get_state() after all candles are processed.
        Does not mutate input candles.
        Deterministic.
"""

import pytest

from execution.market_loop import MarketLoop
from execution.execution_gateway import ExecutionGateway
from execution.paper_broker import PaperBroker


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
# Helper
# ---------------------------------------------------------------------------

def make_gateway(strategy_class, initial_cash=1000):
    broker = PaperBroker(initial_cash=initial_cash)
    return ExecutionGateway(strategy_class, broker)


# ---------------------------------------------------------------------------
# Test strategy classes
# ---------------------------------------------------------------------------

class AlwaysBuyFirst:
    """BUY on the first candle, HOLD thereafter."""
    def __init__(self):
        self._called = False

    def generate_signal(self, candle: dict) -> str:
        if not self._called:
            self._called = True
            return "BUY"
        return "HOLD"


class AlwaysFlat:
    """Always HOLD — never trades."""
    def generate_signal(self, candle: dict) -> str:
        return "HOLD"


class AlwaysBuySell:
    """Alternates BUY / SELL starting with BUY."""
    def __init__(self):
        self._count = 0

    def generate_signal(self, candle: dict) -> str:
        signal = "BUY" if self._count % 2 == 0 else "SELL"
        self._count += 1
        return signal


# ===========================================================================
# Part 1 — run() returns a dict
# ===========================================================================

def test_run_returns_dict():
    gateway = make_gateway(AlwaysFlat)
    loop = MarketLoop(gateway)
    result = loop.run([make_candle(100.0)])
    assert isinstance(result, dict)


def test_run_result_has_required_keys():
    gateway = make_gateway(AlwaysFlat)
    loop = MarketLoop(gateway)
    result = loop.run([make_candle(100.0)])
    for key in ("cash", "position_size", "equity", "equity_curve",
                "trade_history", "state"):
        assert key in result


# ===========================================================================
# Part 2 — Loop processes all candles
# ===========================================================================

def test_equity_curve_length_matches_candle_count():
    candles = [make_candle(float(100 + i * 10)) for i in range(5)]
    gateway = make_gateway(AlwaysFlat)
    loop = MarketLoop(gateway)
    result = loop.run(candles)
    assert len(result["equity_curve"]) == 5


def test_equity_curve_length_one_candle():
    gateway = make_gateway(AlwaysFlat)
    loop = MarketLoop(gateway)
    result = loop.run([make_candle(100.0)])
    assert len(result["equity_curve"]) == 1


def test_equity_curve_length_ten_candles():
    candles = [make_candle(float(100 + i)) for i in range(10)]
    gateway = make_gateway(AlwaysFlat)
    loop = MarketLoop(gateway)
    result = loop.run(candles)
    assert len(result["equity_curve"]) == 10


def test_empty_candles_returns_empty_equity_curve():
    gateway = make_gateway(AlwaysFlat)
    loop = MarketLoop(gateway)
    result = loop.run([])
    assert result["equity_curve"] == []


# ===========================================================================
# Part 3 — Deterministic behavior
# ===========================================================================

def test_deterministic_same_candles_same_result():
    candles = [make_candle(float(100 + i * 10)) for i in range(5)]

    gateway1 = make_gateway(AlwaysBuyFirst)
    result1 = MarketLoop(gateway1).run(candles)

    gateway2 = make_gateway(AlwaysBuyFirst)
    result2 = MarketLoop(gateway2).run(candles)

    assert result1["equity_curve"] == pytest.approx(result2["equity_curve"])
    assert result1["trade_history"] == result2["trade_history"]
    assert result1["cash"] == pytest.approx(result2["cash"])
    assert result1["position_size"] == pytest.approx(result2["position_size"])


# ===========================================================================
# Part 4 — Final state equals manual sequential on_candle calls
# ===========================================================================

def test_run_result_equals_manual_sequential_calls():
    candles = [make_candle(float(100 + i * 10)) for i in range(4)]

    # Manual sequential
    gateway_manual = make_gateway(AlwaysBuyFirst)
    for c in candles:
        gateway_manual.on_candle(c)
    manual_state = gateway_manual.get_state()

    # Via MarketLoop
    gateway_loop = make_gateway(AlwaysBuyFirst)
    loop_state = MarketLoop(gateway_loop).run(candles)

    assert loop_state["equity_curve"] == pytest.approx(manual_state["equity_curve"])
    assert loop_state["cash"] == pytest.approx(manual_state["cash"])
    assert loop_state["position_size"] == pytest.approx(manual_state["position_size"])
    assert loop_state["trade_history"] == manual_state["trade_history"]
    assert loop_state["state"] == manual_state["state"]


# ===========================================================================
# Part 5 — No candle mutation
# ===========================================================================

def test_run_does_not_mutate_candles():
    candles = [make_candle(float(100 + i * 10)) for i in range(3)]
    originals = [dict(c) for c in candles]
    gateway = make_gateway(AlwaysBuyFirst)
    MarketLoop(gateway).run(candles)
    for original, candle in zip(originals, candles):
        assert candle == original


# ===========================================================================
# Part 6 — Works with flat strategy
# ===========================================================================

def test_flat_strategy_zero_trades():
    candles = [make_candle(float(100 + i * 10)) for i in range(5)]
    gateway = make_gateway(AlwaysFlat)
    result = MarketLoop(gateway).run(candles)
    assert len(result["trade_history"]) == 0


def test_flat_strategy_cash_unchanged():
    candles = [make_candle(float(100 + i * 10)) for i in range(5)]
    gateway = make_gateway(AlwaysFlat, initial_cash=1000)
    result = MarketLoop(gateway).run(candles)
    assert result["cash"] == pytest.approx(1000.0)


def test_flat_strategy_equity_curve_constant():
    candles = [make_candle(float(100 + i * 10)) for i in range(3)]
    gateway = make_gateway(AlwaysFlat, initial_cash=1000)
    result = MarketLoop(gateway).run(candles)
    assert all(v == pytest.approx(1000.0) for v in result["equity_curve"])


def test_flat_strategy_state_is_flat():
    candles = [make_candle(float(100 + i * 10)) for i in range(3)]
    gateway = make_gateway(AlwaysFlat)
    result = MarketLoop(gateway).run(candles)
    assert result["state"] == "FLAT"


# ===========================================================================
# Part 7 — Works with buy-hold strategy
# ===========================================================================

def test_buy_hold_strategy_one_trade():
    candles = [make_candle(float(100 + i * 10)) for i in range(5)]
    gateway = make_gateway(AlwaysBuyFirst, initial_cash=1000)
    result = MarketLoop(gateway).run(candles)
    assert len(result["trade_history"]) == 1


def test_buy_hold_strategy_state_is_long():
    candles = [make_candle(float(100 + i * 10)) for i in range(5)]
    gateway = make_gateway(AlwaysBuyFirst, initial_cash=1000)
    result = MarketLoop(gateway).run(candles)
    assert result["state"] == "LONG"


def test_buy_hold_equity_curve_grows_with_price():
    """Buy at 100 (10 shares), prices 110, 120, 130, 140 → equity grows."""
    candles = [make_candle(float(100 + i * 10)) for i in range(5)]
    gateway = make_gateway(AlwaysBuyFirst, initial_cash=1000)
    result = MarketLoop(gateway).run(candles)
    curve = result["equity_curve"]
    assert curve == pytest.approx([1000.0, 1100.0, 1200.0, 1300.0, 1400.0])


def test_buy_hold_final_equity_correct():
    """Buy 10 shares at 100, final price 140 → equity = 1400."""
    candles = [make_candle(float(100 + i * 10)) for i in range(5)]
    gateway = make_gateway(AlwaysBuyFirst, initial_cash=1000)
    result = MarketLoop(gateway).run(candles)
    assert result["equity"] == pytest.approx(1400.0)


# ===========================================================================
# Part 8 — run() returns final state (not intermediate)
# ===========================================================================

def test_run_returns_state_after_last_candle():
    """The returned state must reflect the last candle's price."""
    candles = [make_candle(100.0), make_candle(200.0), make_candle(300.0)]
    gateway = make_gateway(AlwaysBuyFirst, initial_cash=1000)
    result = MarketLoop(gateway).run(candles)
    # Bought 10 shares at 100, final price 300 → equity = 3000
    assert result["equity"] == pytest.approx(3000.0)
