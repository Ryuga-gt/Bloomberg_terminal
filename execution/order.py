"""
execution.order
===============

Immutable order and fill data models for the broker-driven execution layer.

Constants
---------
BUY  = "BUY"
SELL = "SELL"

Classes
-------
Order  — represents an instruction to buy or sell a quantity at a price.
Fill   — represents the result of executing an Order.

Both classes are immutable after construction: attribute reassignment raises
``AttributeError``.
"""

import uuid

# ---------------------------------------------------------------------------
# Side constants
# ---------------------------------------------------------------------------
BUY  = "BUY"
SELL = "SELL"


# ---------------------------------------------------------------------------
# Order
# ---------------------------------------------------------------------------

class Order:
    """
    An instruction to buy or sell *quantity* shares at *price*.

    Parameters
    ----------
    side : str
        ``"BUY"`` or ``"SELL"``.
    quantity : float
        Number of shares.  Must be > 0.
    price : float
        Limit / reference price per share.  Must be > 0.
    timestamp : str or None, optional
        ISO-8601 timestamp string or any label.  Default ``None``.

    Attributes
    ----------
    id : str
        UUID4 string, unique per instance.
    side, quantity, price, timestamp : as above.

    Notes
    -----
    Instances are immutable — attribute reassignment raises ``AttributeError``.
    """

    __slots__ = ("_id", "_side", "_quantity", "_price", "_timestamp")

    def __init__(
        self,
        side: str,
        quantity: float,
        price: float,
        timestamp=None,
    ) -> None:
        object.__setattr__(self, "_id",        str(uuid.uuid4()))
        object.__setattr__(self, "_side",      side)
        object.__setattr__(self, "_quantity",  float(quantity))
        object.__setattr__(self, "_price",     float(price))
        object.__setattr__(self, "_timestamp", timestamp)

    # ------------------------------------------------------------------
    # Read-only properties
    # ------------------------------------------------------------------

    @property
    def id(self) -> str:
        return self._id

    @property
    def side(self) -> str:
        return self._side

    @property
    def quantity(self) -> float:
        return self._quantity

    @property
    def price(self) -> float:
        return self._price

    @property
    def timestamp(self):
        return self._timestamp

    # ------------------------------------------------------------------
    # Immutability guard
    # ------------------------------------------------------------------

    def __setattr__(self, name, value):
        raise AttributeError(
            f"Order is immutable — cannot set attribute '{name}'"
        )

    def __repr__(self) -> str:
        return (
            f"Order(id={self._id!r}, side={self._side!r}, "
            f"quantity={self._quantity}, price={self._price}, "
            f"timestamp={self._timestamp!r})"
        )


# ---------------------------------------------------------------------------
# Fill
# ---------------------------------------------------------------------------

class Fill:
    """
    The result of executing an :class:`Order`.

    Parameters
    ----------
    order_id : str
        The ``id`` of the originating :class:`Order`.
    side : str
        ``"BUY"`` or ``"SELL"``.
    quantity : float
        Shares actually transacted.
    price : float
        Execution price per share (may differ from order price due to
        slippage).
    cash_change : float
        Change in cash balance (negative for BUY, positive for SELL).
    position_change : float
        Change in share position (positive for BUY, negative for SELL).

    Notes
    -----
    Instances are immutable — attribute reassignment raises ``AttributeError``.
    """

    __slots__ = (
        "_order_id",
        "_side",
        "_quantity",
        "_price",
        "_cash_change",
        "_position_change",
    )

    def __init__(
        self,
        order_id: str,
        side: str,
        quantity: float,
        price: float,
        cash_change: float,
        position_change: float,
    ) -> None:
        object.__setattr__(self, "_order_id",        order_id)
        object.__setattr__(self, "_side",            side)
        object.__setattr__(self, "_quantity",        float(quantity))
        object.__setattr__(self, "_price",           float(price))
        object.__setattr__(self, "_cash_change",     float(cash_change))
        object.__setattr__(self, "_position_change", float(position_change))

    # ------------------------------------------------------------------
    # Read-only properties
    # ------------------------------------------------------------------

    @property
    def order_id(self) -> str:
        return self._order_id

    @property
    def side(self) -> str:
        return self._side

    @property
    def quantity(self) -> float:
        return self._quantity

    @property
    def price(self) -> float:
        return self._price

    @property
    def cash_change(self) -> float:
        return self._cash_change

    @property
    def position_change(self) -> float:
        return self._position_change

    # ------------------------------------------------------------------
    # Immutability guard
    # ------------------------------------------------------------------

    def __setattr__(self, name, value):
        raise AttributeError(
            f"Fill is immutable — cannot set attribute '{name}'"
        )

    def __repr__(self) -> str:
        return (
            f"Fill(order_id={self._order_id!r}, side={self._side!r}, "
            f"quantity={self._quantity}, price={self._price}, "
            f"cash_change={self._cash_change}, "
            f"position_change={self._position_change})"
        )
