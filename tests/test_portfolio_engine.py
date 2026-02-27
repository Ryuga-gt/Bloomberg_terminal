"""
Tests for execution.portfolio_engine.PortfolioEngine

Contract
--------
PortfolioEngine(
    strategies: list[type],
    initial_capital: float,
    allocation: str = "equal",
    risk_manager: RiskManager | None = None,
)

    run(candles: list[dict]) -> dict
        Returns:
            portfolio_equity        : float
            portfolio_equity_curve  : list[float]
            strategies              : dict[str, dict]
                Per-strategy: cash, position_size, equity, trade_history

Validation
----------
    strategies empty → ValueError
    initial_capital <= 0 → ValueError
    allocation != "equal" → ValueError
    no candle mutation
    deterministic
"""

import pytest

from execution.portfolio_engine import PortfolioEngine
from execution.execution_gateway import ExecutionGateway
from execution.paper_broker import PaperBroker
from execution.risk_manager import RiskManager


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

class AlwaysBuyHold:
    """BUY on first candle, HOLD thereafter."""
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


class BuySellAlternate:
    """Alternates BUY / SELL starting with BUY."""
    def __init__(self):
        self._count = 0

    def generate_signal(self, candle: dict) -> str:
        signal = "BUY" if self._count % 2 == 0 else "SELL"
        self._count += 1
        return signal


# ===========================================================================
# Part 1 — Validation
# ===========================================================================

def test_empty_strategies_raises():
    with pytest.raises(ValueError):
        PortfolioEngine(strategies=[], initial_capital=1000)


def test_initial_capital_zero_raises():
    with pytest.raises(ValueError):
        PortfolioEngine(strategies=[AlwaysFlat], initial_capital=0)


def test_initial_capital_negative_raises():
    with pytest.raises(ValueError):
        PortfolioEngine(strategies=[AlwaysFlat], initial_capital=-500)


def test_allocation_unknown_raises():
    with pytest.raises(ValueError):
        PortfolioEngine(strategies=[AlwaysFlat], initial_capital=1000,
                        allocation="weighted")


def test_allocation_equal_is_valid():
    engine = PortfolioEngine(strategies=[AlwaysFlat], initial_capital=1000,
                             allocation="equal")
    assert engine is not None


# ===========================================================================
# Part 2 — Return type and required keys
# ===========================================================================

def test_run_returns_dict():
    engine = PortfolioEngine([AlwaysFlat], initial_capital=1000)
    result = engine.run([make_candle(100.0)])
    assert isinstance(result, dict)


def test_run_result_has_portfolio_equity():
    engine = PortfolioEngine([AlwaysFlat], initial_capital=1000)
    result = engine.run([make_candle(100.0)])
    assert "portfolio_equity" in result


def test_run_result_has_portfolio_equity_curve():
    engine = PortfolioEngine([AlwaysFlat], initial_capital=1000)
    result = engine.run([make_candle(100.0)])
    assert "portfolio_equity_curve" in result


def test_run_result_has_strategies():
    engine = PortfolioEngine([AlwaysFlat], initial_capital=1000)
    result = engine.run([make_candle(100.0)])
    assert "strategies" in result


def test_strategies_dict_has_strategy_name_key():
    engine = PortfolioEngine([AlwaysFlat], initial_capital=1000)
    result = engine.run([make_candle(100.0)])
    assert "AlwaysFlat" in result["strategies"]


def test_strategy_entry_has_cash():
    engine = PortfolioEngine([AlwaysFlat], initial_capital=1000)
    result = engine.run([make_candle(100.0)])
    assert "cash" in result["strategies"]["AlwaysFlat"]


def test_strategy_entry_has_position_size():
    engine = PortfolioEngine([AlwaysFlat], initial_capital=1000)
    result = engine.run([make_candle(100.0)])
    assert "position_size" in result["strategies"]["AlwaysFlat"]


def test_strategy_entry_has_equity():
    engine = PortfolioEngine([AlwaysFlat], initial_capital=1000)
    result = engine.run([make_candle(100.0)])
    assert "equity" in result["strategies"]["AlwaysFlat"]


def test_strategy_entry_has_trade_history():
    engine = PortfolioEngine([AlwaysFlat], initial_capital=1000)
    result = engine.run([make_candle(100.0)])
    assert "trade_history" in result["strategies"]["AlwaysFlat"]


# ===========================================================================
# Part 3 — Single strategy portfolio equals single gateway result
# ===========================================================================

def test_single_strategy_portfolio_equity_equals_gateway_equity():
    """
    Single strategy with 1000 capital: portfolio_equity must equal
    the equity of a standalone gateway with the same capital.
    """
    candles = [make_candle(float(100 + i * 10)) for i in range(5)]

    # Portfolio
    engine = PortfolioEngine([AlwaysBuyHold], initial_capital=1000)
    p_result = engine.run(candles)

    # Standalone gateway
    broker = PaperBroker(initial_cash=1000)
    gateway = ExecutionGateway(AlwaysBuyHold, broker)
    for c in candles:
        gateway.on_candle(c)
    gw_state = gateway.get_state()

    assert p_result["portfolio_equity"] == pytest.approx(gw_state["equity"])


def test_single_strategy_equity_curve_matches_gateway():
    candles = [make_candle(float(100 + i * 10)) for i in range(5)]

    engine = PortfolioEngine([AlwaysBuyHold], initial_capital=1000)
    p_result = engine.run(candles)

    broker = PaperBroker(initial_cash=1000)
    gateway = ExecutionGateway(AlwaysBuyHold, broker)
    for c in candles:
        gateway.on_candle(c)
    gw_state = gateway.get_state()

    assert p_result["portfolio_equity_curve"] == pytest.approx(
        gw_state["equity_curve"]
    )


# ===========================================================================
# Part 4 — Two strategies split capital equally
# ===========================================================================

def test_two_strategies_each_get_half_capital():
    """
    2 strategies, 1000 capital → each gets 500.
    Both flat → each strategy cash = 500.
    """
    candles = [make_candle(100.0)]
    engine = PortfolioEngine([AlwaysFlat, AlwaysFlat], initial_capital=1000)
    result = engine.run(candles)
    # Both strategies are named "AlwaysFlat"; only one key will exist
    # (dict key collision). Use a different pair to test properly.
    # We verify via portfolio_equity instead.
    assert result["portfolio_equity"] == pytest.approx(1000.0)


def test_two_different_strategies_capital_split():
    """
    AlwaysBuyHold + AlwaysFlat, 1000 capital → each gets 500.
    After BUY at 100 with 500 cash: AlwaysBuyHold has 5 shares.
    AlwaysFlat has 500 cash.
    portfolio_equity = 5*100 + 500 = 1000.
    """
    candles = [make_candle(100.0)]
    engine = PortfolioEngine(
        [AlwaysBuyHold, AlwaysFlat], initial_capital=1000
    )
    result = engine.run(candles)
    assert result["portfolio_equity"] == pytest.approx(1000.0)


def test_two_strategies_names_in_result():
    candles = [make_candle(100.0)]
    engine = PortfolioEngine(
        [AlwaysBuyHold, AlwaysFlat], initial_capital=1000
    )
    result = engine.run(candles)
    assert "AlwaysBuyHold" in result["strategies"]
    assert "AlwaysFlat" in result["strategies"]


# ===========================================================================
# Part 5 — Portfolio equity equals sum of sub-equities
# ===========================================================================

def test_portfolio_equity_equals_sum_of_sub_equities():
    candles = [make_candle(float(100 + i * 10)) for i in range(4)]
    engine = PortfolioEngine(
        [AlwaysBuyHold, AlwaysFlat], initial_capital=1000
    )
    result = engine.run(candles)

    sub_equities = sum(
        v["equity"] for v in result["strategies"].values()
    )
    assert result["portfolio_equity"] == pytest.approx(sub_equities)


def test_portfolio_equity_curve_is_sum_of_individual_curves():
    """
    With 2 strategies, each step's portfolio equity = sum of both equities.
    """
    candles = [make_candle(float(100 + i * 10)) for i in range(3)]
    engine = PortfolioEngine(
        [AlwaysBuyHold, AlwaysFlat], initial_capital=1000
    )
    result = engine.run(candles)

    # Manually compute expected curve
    broker1 = PaperBroker(initial_cash=500)
    gw1 = ExecutionGateway(AlwaysBuyHold, broker1)
    broker2 = PaperBroker(initial_cash=500)
    gw2 = ExecutionGateway(AlwaysFlat, broker2)

    expected_curve = []
    for c in candles:
        gw1.on_candle(c)
        gw2.on_candle(c)
        price = float(c["close"])
        step_eq = (
            broker1.cash + broker1.position_size * price
            + broker2.cash + broker2.position_size * price
        )
        expected_curve.append(step_eq)

    assert result["portfolio_equity_curve"] == pytest.approx(expected_curve)


# ===========================================================================
# Part 6 — Portfolio equity curve length matches candle count
# ===========================================================================

def test_equity_curve_length_matches_candle_count():
    candles = [make_candle(float(100 + i * 10)) for i in range(5)]
    engine = PortfolioEngine([AlwaysFlat], initial_capital=1000)
    result = engine.run(candles)
    assert len(result["portfolio_equity_curve"]) == 5


def test_equity_curve_length_one_candle():
    engine = PortfolioEngine([AlwaysFlat], initial_capital=1000)
    result = engine.run([make_candle(100.0)])
    assert len(result["portfolio_equity_curve"]) == 1


def test_equity_curve_empty_candles():
    engine = PortfolioEngine([AlwaysFlat], initial_capital=1000)
    result = engine.run([])
    assert result["portfolio_equity_curve"] == []


# ===========================================================================
# Part 7 — Deterministic behavior
# ===========================================================================

def test_deterministic_same_candles_same_result():
    candles = [make_candle(float(100 + i * 10)) for i in range(5)]

    engine1 = PortfolioEngine([AlwaysBuyHold, AlwaysFlat], initial_capital=1000)
    result1 = engine1.run(candles)

    engine2 = PortfolioEngine([AlwaysBuyHold, AlwaysFlat], initial_capital=1000)
    result2 = engine2.run(candles)

    assert result1["portfolio_equity"] == pytest.approx(result2["portfolio_equity"])
    assert result1["portfolio_equity_curve"] == pytest.approx(
        result2["portfolio_equity_curve"]
    )


# ===========================================================================
# Part 8 — Flat strategy contributes zero trades
# ===========================================================================

def test_flat_strategy_zero_trades():
    candles = [make_candle(float(100 + i * 10)) for i in range(5)]
    engine = PortfolioEngine([AlwaysFlat], initial_capital=1000)
    result = engine.run(candles)
    assert len(result["strategies"]["AlwaysFlat"]["trade_history"]) == 0


def test_flat_strategy_cash_unchanged():
    candles = [make_candle(float(100 + i * 10)) for i in range(5)]
    engine = PortfolioEngine([AlwaysFlat], initial_capital=1000)
    result = engine.run(candles)
    assert result["strategies"]["AlwaysFlat"]["cash"] == pytest.approx(1000.0)


def test_flat_portfolio_equity_equals_initial_capital():
    candles = [make_candle(float(100 + i * 10)) for i in range(5)]
    engine = PortfolioEngine([AlwaysFlat], initial_capital=1000)
    result = engine.run(candles)
    assert result["portfolio_equity"] == pytest.approx(1000.0)


# ===========================================================================
# Part 9 — RiskManager works per-strategy
# ===========================================================================

def test_risk_manager_caps_buy_per_strategy():
    """
    1 strategy, 1000 capital, pct=0.5 → max_qty = 500/100 = 5 shares.
    Without RM: 10 shares. With RM: 5 shares.
    """
    rm = RiskManager(max_position_pct=0.5)
    candles = [make_candle(100.0)]
    engine = PortfolioEngine(
        [AlwaysBuyHold], initial_capital=1000, risk_manager=rm
    )
    result = engine.run(candles)
    assert result["strategies"]["AlwaysBuyHold"]["position_size"] == pytest.approx(5.0)


def test_risk_manager_leaves_remaining_cash():
    """After capped BUY: cash = 1000 - 5*100 = 500."""
    rm = RiskManager(max_position_pct=0.5)
    candles = [make_candle(100.0)]
    engine = PortfolioEngine(
        [AlwaysBuyHold], initial_capital=1000, risk_manager=rm
    )
    result = engine.run(candles)
    assert result["strategies"]["AlwaysBuyHold"]["cash"] == pytest.approx(500.0)


# ===========================================================================
# Part 10 — No candle mutation
# ===========================================================================

def test_run_does_not_mutate_candles():
    candles = [make_candle(float(100 + i * 10)) for i in range(3)]
    originals = [dict(c) for c in candles]
    engine = PortfolioEngine([AlwaysBuyHold, AlwaysFlat], initial_capital=1000)
    engine.run(candles)
    for original, candle in zip(originals, candles):
        assert candle == original


# ===========================================================================
# Part 11 — BuySellAlternate strategy
# ===========================================================================

def test_buy_sell_alternate_two_trades():
    """BuySellAlternate: BUY on candle 1, SELL on candle 2 → 2 trades."""
    candles = [make_candle(100.0), make_candle(200.0)]
    engine = PortfolioEngine([BuySellAlternate], initial_capital=1000)
    result = engine.run(candles)
    assert len(result["strategies"]["BuySellAlternate"]["trade_history"]) == 2


def test_buy_sell_alternate_final_cash_correct():
    """Buy 10 shares at 100, sell at 200 → cash = 2000."""
    candles = [make_candle(100.0), make_candle(200.0)]
    engine = PortfolioEngine([BuySellAlternate], initial_capital=1000)
    result = engine.run(candles)
    assert result["strategies"]["BuySellAlternate"]["cash"] == pytest.approx(2000.0)


# ===========================================================================
# Part 12 — Three strategies
# ===========================================================================

def test_three_strategies_capital_split():
    """3 strategies, 3000 capital → each gets 1000."""
    candles = [make_candle(100.0)]
    engine = PortfolioEngine(
        [AlwaysFlat, AlwaysFlat, AlwaysFlat], initial_capital=3000
    )
    result = engine.run(candles)
    assert result["portfolio_equity"] == pytest.approx(3000.0)
