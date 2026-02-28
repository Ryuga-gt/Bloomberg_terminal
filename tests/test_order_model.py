"""
Tests for execution.order — Order and Fill models.

Contract
--------
Order(side, quantity, price, timestamp=None)
    id          : str  (uuid4, unique per instance)
    side        : str
    quantity    : float
    price       : float
    timestamp   : any (optional)
    Immutable after creation → AttributeError on reassignment.

Fill(order_id, side, quantity, price, cash_change, position_change)
    All fields stored as given.
    Immutable after creation → AttributeError on reassignment.

Constants: BUY = "BUY", SELL = "SELL"
"""

import pytest

from execution.order import Order, Fill, BUY, SELL


# ===========================================================================
# Part 1 — Constants
# ===========================================================================

def test_buy_constant_value():
    assert BUY == "BUY"


def test_sell_constant_value():
    assert SELL == "SELL"


# ===========================================================================
# Part 2 — Order: field storage
# ===========================================================================

def test_order_side_stored():
    o = Order(side=BUY, quantity=10.0, price=100.0)
    assert o.side == BUY


def test_order_quantity_stored():
    o = Order(side=BUY, quantity=10.0, price=100.0)
    assert o.quantity == pytest.approx(10.0)


def test_order_price_stored():
    o = Order(side=BUY, quantity=10.0, price=100.0)
    assert o.price == pytest.approx(100.0)


def test_order_timestamp_default_none():
    o = Order(side=BUY, quantity=10.0, price=100.0)
    assert o.timestamp is None


def test_order_timestamp_stored():
    o = Order(side=SELL, quantity=5.0, price=200.0, timestamp="2024-01-01T00:00:00Z")
    assert o.timestamp == "2024-01-01T00:00:00Z"


def test_order_quantity_stored_as_float():
    o = Order(side=BUY, quantity=10, price=100)
    assert isinstance(o.quantity, float)


def test_order_price_stored_as_float():
    o = Order(side=BUY, quantity=10, price=100)
    assert isinstance(o.price, float)


def test_order_sell_side_stored():
    o = Order(side=SELL, quantity=3.0, price=50.0)
    assert o.side == SELL


# ===========================================================================
# Part 3 — Order: id uniqueness
# ===========================================================================

def test_order_has_id():
    o = Order(side=BUY, quantity=1.0, price=10.0)
    assert o.id is not None


def test_order_id_is_string():
    o = Order(side=BUY, quantity=1.0, price=10.0)
    assert isinstance(o.id, str)


def test_order_id_is_unique_per_instance():
    o1 = Order(side=BUY, quantity=1.0, price=10.0)
    o2 = Order(side=BUY, quantity=1.0, price=10.0)
    assert o1.id != o2.id


def test_order_id_unique_across_many_instances():
    ids = {Order(side=BUY, quantity=1.0, price=10.0).id for _ in range(100)}
    assert len(ids) == 100


# ===========================================================================
# Part 4 — Order: immutability
# ===========================================================================

def test_order_id_immutable():
    o = Order(side=BUY, quantity=1.0, price=10.0)
    with pytest.raises(AttributeError):
        o.id = "new-id"


def test_order_side_immutable():
    o = Order(side=BUY, quantity=1.0, price=10.0)
    with pytest.raises(AttributeError):
        o.side = SELL


def test_order_quantity_immutable():
    o = Order(side=BUY, quantity=1.0, price=10.0)
    with pytest.raises(AttributeError):
        o.quantity = 999.0


def test_order_price_immutable():
    o = Order(side=BUY, quantity=1.0, price=10.0)
    with pytest.raises(AttributeError):
        o.price = 999.0


def test_order_timestamp_immutable():
    o = Order(side=BUY, quantity=1.0, price=10.0)
    with pytest.raises(AttributeError):
        o.timestamp = "2024-01-01"


def test_order_new_attribute_immutable():
    o = Order(side=BUY, quantity=1.0, price=10.0)
    with pytest.raises(AttributeError):
        o.extra = "value"


# ===========================================================================
# Part 5 — Fill: field storage
# ===========================================================================

def test_fill_order_id_stored():
    f = Fill(order_id="abc-123", side=BUY, quantity=10.0,
             price=100.0, cash_change=-1000.0, position_change=10.0)
    assert f.order_id == "abc-123"


def test_fill_side_stored():
    f = Fill(order_id="abc-123", side=BUY, quantity=10.0,
             price=100.0, cash_change=-1000.0, position_change=10.0)
    assert f.side == BUY


def test_fill_quantity_stored():
    f = Fill(order_id="abc-123", side=BUY, quantity=10.0,
             price=100.0, cash_change=-1000.0, position_change=10.0)
    assert f.quantity == pytest.approx(10.0)


def test_fill_price_stored():
    f = Fill(order_id="abc-123", side=BUY, quantity=10.0,
             price=100.0, cash_change=-1000.0, position_change=10.0)
    assert f.price == pytest.approx(100.0)


def test_fill_cash_change_stored():
    f = Fill(order_id="abc-123", side=BUY, quantity=10.0,
             price=100.0, cash_change=-1000.0, position_change=10.0)
    assert f.cash_change == pytest.approx(-1000.0)


def test_fill_position_change_stored():
    f = Fill(order_id="abc-123", side=BUY, quantity=10.0,
             price=100.0, cash_change=-1000.0, position_change=10.0)
    assert f.position_change == pytest.approx(10.0)


def test_fill_sell_side_stored():
    f = Fill(order_id="xyz", side=SELL, quantity=5.0,
             price=200.0, cash_change=1000.0, position_change=-5.0)
    assert f.side == SELL
    assert f.cash_change == pytest.approx(1000.0)
    assert f.position_change == pytest.approx(-5.0)


def test_fill_quantity_stored_as_float():
    f = Fill(order_id="x", side=BUY, quantity=5, price=10,
             cash_change=-50, position_change=5)
    assert isinstance(f.quantity, float)


def test_fill_price_stored_as_float():
    f = Fill(order_id="x", side=BUY, quantity=5, price=10,
             cash_change=-50, position_change=5)
    assert isinstance(f.price, float)


# ===========================================================================
# Part 6 — Fill: immutability
# ===========================================================================

def test_fill_order_id_immutable():
    f = Fill(order_id="abc", side=BUY, quantity=1.0,
             price=10.0, cash_change=-10.0, position_change=1.0)
    with pytest.raises(AttributeError):
        f.order_id = "new"


def test_fill_side_immutable():
    f = Fill(order_id="abc", side=BUY, quantity=1.0,
             price=10.0, cash_change=-10.0, position_change=1.0)
    with pytest.raises(AttributeError):
        f.side = SELL


def test_fill_quantity_immutable():
    f = Fill(order_id="abc", side=BUY, quantity=1.0,
             price=10.0, cash_change=-10.0, position_change=1.0)
    with pytest.raises(AttributeError):
        f.quantity = 999.0


def test_fill_price_immutable():
    f = Fill(order_id="abc", side=BUY, quantity=1.0,
             price=10.0, cash_change=-10.0, position_change=1.0)
    with pytest.raises(AttributeError):
        f.price = 999.0


def test_fill_cash_change_immutable():
    f = Fill(order_id="abc", side=BUY, quantity=1.0,
             price=10.0, cash_change=-10.0, position_change=1.0)
    with pytest.raises(AttributeError):
        f.cash_change = 0.0


def test_fill_position_change_immutable():
    f = Fill(order_id="abc", side=BUY, quantity=1.0,
             price=10.0, cash_change=-10.0, position_change=1.0)
    with pytest.raises(AttributeError):
        f.position_change = 0.0


# ===========================================================================
# Part 7 — Fill links back to Order
# ===========================================================================

def test_fill_order_id_matches_order():
    o = Order(side=BUY, quantity=10.0, price=100.0)
    f = Fill(order_id=o.id, side=BUY, quantity=10.0,
             price=100.0, cash_change=-1000.0, position_change=10.0)
    assert f.order_id == o.id
