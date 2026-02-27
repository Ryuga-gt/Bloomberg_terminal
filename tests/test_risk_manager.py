"""
Tests for execution.risk_manager.RiskManager

Contract
--------
RiskManager(max_position_pct: float)
    0 < max_position_pct <= 1  → ValueError otherwise

    adjust_order(order: Order, equity: float) -> Order
        BUY:  caps quantity so position_value <= equity * max_position_pct
              max_quantity = equity * max_position_pct / order.price
              adjusted_qty = min(order.quantity, max_quantity)
              Returns original order if no adjustment needed.
              Returns new Order (new id) if quantity is capped.
        SELL: passes through unchanged.
        equity < 0 → ValueError.

Formula:
    max_value    = equity * max_position_pct
    max_quantity = max_value / order.price
    adjusted_qty = min(order.quantity, max_quantity)
"""

import pytest

from execution.order import Order, BUY, SELL
from execution.risk_manager import RiskManager


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def buy_order(quantity: float, price: float) -> Order:
    return Order(side=BUY, quantity=quantity, price=price)


def sell_order(quantity: float, price: float) -> Order:
    return Order(side=SELL, quantity=quantity, price=price)


# ===========================================================================
# Part 1 — Validation: max_position_pct
# ===========================================================================

def test_pct_zero_raises():
    with pytest.raises(ValueError):
        RiskManager(max_position_pct=0.0)


def test_pct_negative_raises():
    with pytest.raises(ValueError):
        RiskManager(max_position_pct=-0.5)


def test_pct_greater_than_one_raises():
    with pytest.raises(ValueError):
        RiskManager(max_position_pct=1.1)


def test_pct_one_is_valid():
    rm = RiskManager(max_position_pct=1.0)
    assert rm.max_position_pct == pytest.approx(1.0)


def test_pct_small_positive_is_valid():
    rm = RiskManager(max_position_pct=0.01)
    assert rm.max_position_pct == pytest.approx(0.01)


# ===========================================================================
# Part 2 — Validation: equity in adjust_order
# ===========================================================================

def test_negative_equity_raises():
    rm = RiskManager(max_position_pct=0.5)
    with pytest.raises(ValueError):
        rm.adjust_order(buy_order(10.0, 100.0), equity=-1.0)


def test_zero_equity_returns_zero_quantity_order():
    """equity=0 → max_quantity=0 → adjusted_qty=0."""
    rm = RiskManager(max_position_pct=0.5)
    result = rm.adjust_order(buy_order(10.0, 100.0), equity=0.0)
    assert result.quantity == pytest.approx(0.0)


# ===========================================================================
# Part 3 — BUY: quantity capped correctly
# ===========================================================================

def test_buy_quantity_capped_when_exceeds_limit():
    """
    equity=1000, pct=0.5 → max_value=500, max_qty=500/100=5
    order qty=10 → capped to 5
    """
    rm = RiskManager(max_position_pct=0.5)
    result = rm.adjust_order(buy_order(10.0, 100.0), equity=1000.0)
    assert result.quantity == pytest.approx(5.0)


def test_buy_quantity_not_capped_when_within_limit():
    """
    equity=2000, pct=0.5 → max_value=1000, max_qty=10
    order qty=10 → no adjustment
    """
    rm = RiskManager(max_position_pct=0.5)
    result = rm.adjust_order(buy_order(10.0, 100.0), equity=2000.0)
    assert result.quantity == pytest.approx(10.0)


def test_buy_no_adjustment_returns_original_order():
    """When no adjustment is needed, the exact same Order object is returned."""
    rm = RiskManager(max_position_pct=1.0)
    order = buy_order(10.0, 100.0)
    result = rm.adjust_order(order, equity=2000.0)
    assert result is order


def test_buy_adjusted_order_is_new_object():
    """When adjustment is needed, a new Order is returned (different id)."""
    rm = RiskManager(max_position_pct=0.5)
    order = buy_order(10.0, 100.0)
    result = rm.adjust_order(order, equity=1000.0)
    assert result is not order
    assert result.id != order.id


def test_buy_adjusted_order_preserves_side():
    rm = RiskManager(max_position_pct=0.5)
    result = rm.adjust_order(buy_order(10.0, 100.0), equity=1000.0)
    assert result.side == BUY


def test_buy_adjusted_order_preserves_price():
    rm = RiskManager(max_position_pct=0.5)
    result = rm.adjust_order(buy_order(10.0, 100.0), equity=1000.0)
    assert result.price == pytest.approx(100.0)


def test_buy_adjusted_order_preserves_timestamp():
    rm = RiskManager(max_position_pct=0.5)
    order = Order(side=BUY, quantity=10.0, price=100.0, timestamp="2024-01-01")
    result = rm.adjust_order(order, equity=1000.0)
    assert result.timestamp == "2024-01-01"


# ===========================================================================
# Part 4 — SELL: passes through unchanged
# ===========================================================================

def test_sell_order_returned_unchanged():
    rm = RiskManager(max_position_pct=0.1)
    order = sell_order(100.0, 50.0)
    result = rm.adjust_order(order, equity=100.0)
    assert result is order


def test_sell_order_quantity_not_modified():
    rm = RiskManager(max_position_pct=0.1)
    order = sell_order(100.0, 50.0)
    result = rm.adjust_order(order, equity=100.0)
    assert result.quantity == pytest.approx(100.0)


# ===========================================================================
# Part 5 — Edge cases
# ===========================================================================

def test_pct_one_allows_full_equity():
    """pct=1.0: max_qty = equity / price = 1000/100 = 10 → no cap for qty=10."""
    rm = RiskManager(max_position_pct=1.0)
    result = rm.adjust_order(buy_order(10.0, 100.0), equity=1000.0)
    assert result.quantity == pytest.approx(10.0)


def test_pct_one_caps_when_order_exceeds_equity():
    """pct=1.0: max_qty=10, order qty=20 → capped to 10."""
    rm = RiskManager(max_position_pct=1.0)
    result = rm.adjust_order(buy_order(20.0, 100.0), equity=1000.0)
    assert result.quantity == pytest.approx(10.0)


def test_small_pct_caps_aggressively():
    """pct=0.01: max_value=10, max_qty=0.1 for price=100."""
    rm = RiskManager(max_position_pct=0.01)
    result = rm.adjust_order(buy_order(10.0, 100.0), equity=1000.0)
    assert result.quantity == pytest.approx(0.1)


def test_exact_limit_no_adjustment():
    """
    equity=1000, pct=0.5 → max_qty=5
    order qty=5 → exactly at limit → no adjustment
    """
    rm = RiskManager(max_position_pct=0.5)
    order = buy_order(5.0, 100.0)
    result = rm.adjust_order(order, equity=1000.0)
    assert result is order


def test_max_position_pct_stored():
    rm = RiskManager(max_position_pct=0.25)
    assert rm.max_position_pct == pytest.approx(0.25)


# ===========================================================================
# Part 6 — Determinism
# ===========================================================================

def test_deterministic_same_inputs_same_result():
    rm = RiskManager(max_position_pct=0.5)
    order = buy_order(10.0, 100.0)
    r1 = rm.adjust_order(order, equity=1000.0)
    r2 = rm.adjust_order(order, equity=1000.0)
    assert r1.quantity == pytest.approx(r2.quantity)
    assert r1.side == r2.side
    assert r1.price == pytest.approx(r2.price)
