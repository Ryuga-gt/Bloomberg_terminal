"""
execution.paper_broker
======================

Paper (simulated) broker that implements :class:`BrokerInterface`.

Execution model
---------------
* **BUY**:
    execution_price = order.price * (1 + slippage_pct)
    Deducts ``execution_price * quantity`` from cash.
    Adds ``quantity`` to position.
    Raises ``ValueError`` if cash is insufficient.

* **SELL**:
    execution_price = order.price * (1 - slippage_pct)
    Adds ``execution_price * quantity`` to cash.
    Deducts ``quantity`` from position.
    Raises ``ValueError`` if position is insufficient.

The broker is deterministic: given the same sequence of orders it always
produces the same fills and the same final state.

No threading, no async, no external dependencies.
"""

from execution.broker_interface import BrokerInterface
from execution.order import Order, Fill, BUY, SELL


class PaperBroker(BrokerInterface):
    """
    Simulated paper broker.

    Parameters
    ----------
    initial_cash : float
        Starting cash balance.  Must be > 0.
    slippage_pct : float, optional
        Fractional slippage applied to every execution price.
        0.0 means no slippage.  Default 0.0.

    Raises
    ------
    ValueError
        If ``initial_cash`` <= 0 or ``slippage_pct`` < 0.

    Attributes
    ----------
    cash : float
        Current cash balance.
    position_size : float
        Current share position.
    """

    def __init__(self, initial_cash: float, slippage_pct: float = 0.0) -> None:
        if initial_cash <= 0:
            raise ValueError(
                f"initial_cash must be > 0, got {initial_cash!r}"
            )
        if slippage_pct < 0:
            raise ValueError(
                f"slippage_pct must be >= 0, got {slippage_pct!r}"
            )

        self._cash: float = float(initial_cash)
        self._position_size: float = 0.0
        self._slippage_pct: float = float(slippage_pct)

    # ------------------------------------------------------------------
    # Public read-only accessors
    # ------------------------------------------------------------------

    @property
    def cash(self) -> float:
        return self._cash

    @property
    def position_size(self) -> float:
        return self._position_size

    # ------------------------------------------------------------------
    # BrokerInterface implementation
    # ------------------------------------------------------------------

    def execute_order(self, order: Order) -> Fill:
        """
        Execute *order* and return a :class:`Fill`.

        Parameters
        ----------
        order : Order
            The order to execute.

        Returns
        -------
        Fill

        Raises
        ------
        ValueError
            If a BUY order cannot be afforded, or a SELL order exceeds
            the current position.
        """
        if order.side == BUY:
            return self._execute_buy(order)
        elif order.side == SELL:
            return self._execute_sell(order)
        else:
            raise ValueError(
                f"Unknown order side: {order.side!r}. Expected 'BUY' or 'SELL'."
            )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _execute_buy(self, order: Order) -> Fill:
        execution_price = order.price * (1.0 + self._slippage_pct)
        cost = execution_price * order.quantity

        if cost > self._cash:
            raise ValueError(
                f"Insufficient funds: need {cost:.6f}, have {self._cash:.6f}"
            )

        self._cash -= cost
        self._position_size += order.quantity

        return Fill(
            order_id=order.id,
            side=BUY,
            quantity=order.quantity,
            price=execution_price,
            cash_change=-cost,
            position_change=order.quantity,
        )

    def _execute_sell(self, order: Order) -> Fill:
        if order.quantity > self._position_size:
            raise ValueError(
                f"Insufficient position: need {order.quantity}, "
                f"have {self._position_size}"
            )

        execution_price = order.price * (1.0 - self._slippage_pct)
        proceeds = execution_price * order.quantity

        self._position_size -= order.quantity
        self._cash += proceeds

        return Fill(
            order_id=order.id,
            side=SELL,
            quantity=order.quantity,
            price=execution_price,
            cash_change=proceeds,
            position_change=-order.quantity,
        )
