"""
Tests for execution.paper_broker.PaperBroker

Contract
--------
PaperBroker(initial_cash: float, slippage_pct: float = 0.0)

    execute_order(order: Order) -> Fill

Rules:
    BUY:  execution_price = price * (1 + slippage_pct)
          cost = execution_price * quantity
          cash -= cost; position += quantity
          Raises ValueError if cost > cash

    SELL: execution_price = price * (1 - slippage_pct)
          proceeds = execution_price * quantity
          cash += proceeds; position -= quantity
          Raises ValueError if quantity > position

Validation:
    initial_cash <= 0 → ValueError
    slippage_pct < 0  → ValueError
"""

import pytest

from execution.order import Order, Fill, BUY, SELL
from execution.paper_broker import PaperBroker


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def buy_order(quantity: float, price: float) -> Order:
    return Order(side=BUY, quantity=quantity, price=price)


def sell_order(quantity: float, price: float) -> Order:
    return Order(side=SELL, quantity=quantity, price=price)


# ===========================================================================
# Part 1 — Validation
# ===========================================================================

def test_initial_cash_zero_raises():
    with pytest.raises(ValueError):
        PaperBroker(initial_cash=0)


def test_initial_cash_negative_raises():
    with pytest.raises(ValueError):
        PaperBroker(initial_cash=-500)


def test_slippage_negative_raises():
    with pytest.raises(ValueError):
        PaperBroker(initial_cash=1000, slippage_pct=-0.01)


def test_default_slippage_is_zero():
    broker = PaperBroker(initial_cash=1000)
    order = buy_order(10.0, 100.0)
    fill = broker.execute_order(order)
    assert fill.price == pytest.approx(100.0)


# ===========================================================================
# Part 2 — BUY: cash and position updates
# ===========================================================================

def test_buy_updates_position():
    broker = PaperBroker(initial_cash=1000)
    broker.execute_order(buy_order(10.0, 100.0))
    assert broker.position_size == pytest.approx(10.0)


def test_buy_deducts_cash():
    broker = PaperBroker(initial_cash=1000)
    broker.execute_order(buy_order(10.0, 100.0))
    assert broker.cash == pytest.approx(0.0)


def test_buy_partial_cash_remaining():
    """Buy 5 shares at 100 with 1000 cash → 500 remaining."""
    broker = PaperBroker(initial_cash=1000)
    broker.execute_order(buy_order(5.0, 100.0))
    assert broker.cash == pytest.approx(500.0)
    assert broker.position_size == pytest.approx(5.0)


def test_buy_fill_side_is_buy():
    broker = PaperBroker(initial_cash=1000)
    fill = broker.execute_order(buy_order(10.0, 100.0))
    assert fill.side == BUY


def test_buy_fill_quantity_correct():
    broker = PaperBroker(initial_cash=1000)
    fill = broker.execute_order(buy_order(10.0, 100.0))
    assert fill.quantity == pytest.approx(10.0)


def test_buy_fill_price_correct_no_slippage():
    broker = PaperBroker(initial_cash=1000)
    fill = broker.execute_order(buy_order(10.0, 100.0))
    assert fill.price == pytest.approx(100.0)


def test_buy_fill_cash_change_negative():
    broker = PaperBroker(initial_cash=1000)
    fill = broker.execute_order(buy_order(10.0, 100.0))
    assert fill.cash_change == pytest.approx(-1000.0)


def test_buy_fill_position_change_positive():
    broker = PaperBroker(initial_cash=1000)
    fill = broker.execute_order(buy_order(10.0, 100.0))
    assert fill.position_change == pytest.approx(10.0)


def test_buy_fill_order_id_matches():
    broker = PaperBroker(initial_cash=1000)
    order = buy_order(10.0, 100.0)
    fill = broker.execute_order(order)
    assert fill.order_id == order.id


# ===========================================================================
# Part 3 — SELL: cash and position updates
# ===========================================================================

def test_sell_updates_position():
    broker = PaperBroker(initial_cash=1000)
    broker.execute_order(buy_order(10.0, 100.0))   # buy 10 shares
    broker.execute_order(sell_order(10.0, 100.0))  # sell all
    assert broker.position_size == pytest.approx(0.0)


def test_sell_adds_cash():
    """Buy 10 at 100, sell 10 at 200 → cash = 2000."""
    broker = PaperBroker(initial_cash=1000)
    broker.execute_order(buy_order(10.0, 100.0))
    broker.execute_order(sell_order(10.0, 200.0))
    assert broker.cash == pytest.approx(2000.0)


def test_sell_partial_position():
    """Buy 10, sell 5 → position = 5."""
    broker = PaperBroker(initial_cash=1000)
    broker.execute_order(buy_order(10.0, 100.0))
    broker.execute_order(sell_order(5.0, 100.0))
    assert broker.position_size == pytest.approx(5.0)


def test_sell_fill_side_is_sell():
    broker = PaperBroker(initial_cash=1000)
    broker.execute_order(buy_order(10.0, 100.0))
    fill = broker.execute_order(sell_order(10.0, 100.0))
    assert fill.side == SELL


def test_sell_fill_quantity_correct():
    broker = PaperBroker(initial_cash=1000)
    broker.execute_order(buy_order(10.0, 100.0))
    fill = broker.execute_order(sell_order(10.0, 100.0))
    assert fill.quantity == pytest.approx(10.0)


def test_sell_fill_price_correct_no_slippage():
    broker = PaperBroker(initial_cash=1000)
    broker.execute_order(buy_order(10.0, 100.0))
    fill = broker.execute_order(sell_order(10.0, 200.0))
    assert fill.price == pytest.approx(200.0)


def test_sell_fill_cash_change_positive():
    broker = PaperBroker(initial_cash=1000)
    broker.execute_order(buy_order(10.0, 100.0))
    fill = broker.execute_order(sell_order(10.0, 200.0))
    assert fill.cash_change == pytest.approx(2000.0)


def test_sell_fill_position_change_negative():
    broker = PaperBroker(initial_cash=1000)
    broker.execute_order(buy_order(10.0, 100.0))
    fill = broker.execute_order(sell_order(10.0, 200.0))
    assert fill.position_change == pytest.approx(-10.0)


# ===========================================================================
# Part 4 — Slippage applied
# ===========================================================================

def test_buy_slippage_increases_execution_price():
    """1% slippage on BUY at 100 → execution price 101."""
    broker = PaperBroker(initial_cash=2000, slippage_pct=0.01)
    fill = broker.execute_order(buy_order(10.0, 100.0))
    assert fill.price == pytest.approx(101.0)


def test_buy_slippage_deducts_more_cash():
    """1% slippage: cost = 101 * 10 = 1010."""
    broker = PaperBroker(initial_cash=2000, slippage_pct=0.01)
    broker.execute_order(buy_order(10.0, 100.0))
    assert broker.cash == pytest.approx(2000.0 - 1010.0)


def test_sell_slippage_decreases_execution_price():
    """1% slippage on SELL at 200 → execution price 198."""
    broker = PaperBroker(initial_cash=2000, slippage_pct=0.01)
    broker.execute_order(buy_order(10.0, 100.0))   # cost = 1010
    fill = broker.execute_order(sell_order(10.0, 200.0))
    assert fill.price == pytest.approx(198.0)


def test_sell_slippage_adds_less_cash():
    """1% slippage: proceeds = 198 * 10 = 1980."""
    broker = PaperBroker(initial_cash=2000, slippage_pct=0.01)
    broker.execute_order(buy_order(10.0, 100.0))   # cash: 2000 - 1010 = 990
    broker.execute_order(sell_order(10.0, 200.0))  # cash: 990 + 1980 = 2970
    assert broker.cash == pytest.approx(990.0 + 1980.0)


# ===========================================================================
# Part 5 — Cannot overbuy
# ===========================================================================

def test_overbuy_raises_value_error():
    broker = PaperBroker(initial_cash=500)
    with pytest.raises(ValueError):
        broker.execute_order(buy_order(10.0, 100.0))  # costs 1000 > 500


def test_overbuy_does_not_change_state():
    broker = PaperBroker(initial_cash=500)
    try:
        broker.execute_order(buy_order(10.0, 100.0))
    except ValueError:
        pass
    assert broker.cash == pytest.approx(500.0)
    assert broker.position_size == pytest.approx(0.0)


# ===========================================================================
# Part 6 — Cannot oversell
# ===========================================================================

def test_oversell_raises_value_error():
    broker = PaperBroker(initial_cash=1000)
    broker.execute_order(buy_order(5.0, 100.0))
    with pytest.raises(ValueError):
        broker.execute_order(sell_order(10.0, 100.0))  # only 5 shares held


def test_oversell_from_flat_raises_value_error():
    broker = PaperBroker(initial_cash=1000)
    with pytest.raises(ValueError):
        broker.execute_order(sell_order(1.0, 100.0))


def test_oversell_does_not_change_state():
    broker = PaperBroker(initial_cash=1000)
    broker.execute_order(buy_order(5.0, 100.0))
    cash_before = broker.cash
    pos_before = broker.position_size
    try:
        broker.execute_order(sell_order(10.0, 100.0))
    except ValueError:
        pass
    assert broker.cash == pytest.approx(cash_before)
    assert broker.position_size == pytest.approx(pos_before)


# ===========================================================================
# Part 7 — Multiple sequential trades
# ===========================================================================

def test_multiple_buys_accumulate_position():
    broker = PaperBroker(initial_cash=3000)
    broker.execute_order(buy_order(10.0, 100.0))  # cost 1000
    broker.execute_order(buy_order(10.0, 100.0))  # cost 1000
    assert broker.position_size == pytest.approx(20.0)
    assert broker.cash == pytest.approx(1000.0)


def test_buy_then_sell_then_buy_final_state():
    """
    Start: cash=1000
    BUY 10 @ 100  → cash=0,    pos=10
    SELL 10 @ 200 → cash=2000, pos=0
    BUY 5 @ 200   → cash=1000, pos=5
    """
    broker = PaperBroker(initial_cash=1000)
    broker.execute_order(buy_order(10.0, 100.0))
    broker.execute_order(sell_order(10.0, 200.0))
    broker.execute_order(buy_order(5.0, 200.0))
    assert broker.cash == pytest.approx(1000.0)
    assert broker.position_size == pytest.approx(5.0)


def test_final_cash_correct_after_round_trip():
    """Buy 10 @ 100, sell 10 @ 150 → cash = 1500."""
    broker = PaperBroker(initial_cash=1000)
    broker.execute_order(buy_order(10.0, 100.0))
    broker.execute_order(sell_order(10.0, 150.0))
    assert broker.cash == pytest.approx(1500.0)


# ===========================================================================
# Part 8 — Deterministic behavior
# ===========================================================================

def test_deterministic_same_orders_same_result():
    orders = [
        buy_order(10.0, 100.0),
        sell_order(5.0, 120.0),
        buy_order(3.0, 110.0),
    ]

    broker1 = PaperBroker(initial_cash=2000)
    for o in orders:
        broker1.execute_order(o)

    broker2 = PaperBroker(initial_cash=2000)
    for o in orders:
        broker2.execute_order(o)

    assert broker1.cash == pytest.approx(broker2.cash)
    assert broker1.position_size == pytest.approx(broker2.position_size)


# ===========================================================================
# Part 9 — Fill is a Fill instance
# ===========================================================================

def test_execute_order_returns_fill_instance():
    broker = PaperBroker(initial_cash=1000)
    result = broker.execute_order(buy_order(10.0, 100.0))
    from execution.order import Fill
    assert isinstance(result, Fill)
