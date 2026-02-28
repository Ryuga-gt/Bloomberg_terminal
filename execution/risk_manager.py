"""
execution.risk_manager
======================

Position-size risk manager.

The :class:`RiskManager` caps the quantity of a BUY :class:`Order` so that
the resulting position value does not exceed ``equity * max_position_pct``.

SELL orders are passed through unchanged (closing a position is always
permitted).

Formula
-------
    max_value    = equity * max_position_pct
    max_quantity = max_value / order.price
    adjusted_qty = min(order.quantity, max_quantity)

If ``adjusted_qty`` equals ``order.quantity`` the original order is returned
unchanged.  Otherwise a new :class:`Order` is returned with the capped
quantity (same side, price, and timestamp; new ``id``).

Validation
----------
* ``max_position_pct`` must satisfy ``0 < pct <= 1`` → ``ValueError``.
* ``equity`` passed to :meth:`adjust_order` must be >= 0 → ``ValueError``.
"""

from execution.order import Order, BUY


class RiskManager:
    """
    Caps BUY order quantity to ``equity * max_position_pct / price``.

    Parameters
    ----------
    max_position_pct : float
        Maximum fraction of equity that may be allocated to a single
        position.  Must satisfy ``0 < max_position_pct <= 1``.

    Raises
    ------
    ValueError
        If ``max_position_pct`` is not in ``(0, 1]``.
    """

    def __init__(self, max_position_pct: float) -> None:
        if not (0 < max_position_pct <= 1):
            raise ValueError(
                f"max_position_pct must be in (0, 1], got {max_position_pct!r}"
            )
        self._max_position_pct = float(max_position_pct)

    # ------------------------------------------------------------------

    @property
    def max_position_pct(self) -> float:
        return self._max_position_pct

    # ------------------------------------------------------------------

    def adjust_order(self, order: Order, equity: float) -> Order:
        """
        Return *order* (possibly with a reduced quantity) that respects
        the position-size limit.

        Parameters
        ----------
        order : Order
            The order to evaluate.
        equity : float
            Current portfolio equity (cash + position mark-to-market).
            Must be >= 0.

        Returns
        -------
        Order
            The original order if no adjustment is needed, otherwise a
            new :class:`Order` with a capped quantity.

        Raises
        ------
        ValueError
            If ``equity`` < 0.
        """
        if equity < 0:
            raise ValueError(
                f"equity must be >= 0, got {equity!r}"
            )

        # SELL orders are not capped
        if order.side != BUY:
            return order

        max_value = equity * self._max_position_pct
        max_quantity = max_value / order.price if order.price > 0 else 0.0
        adjusted_qty = min(order.quantity, max_quantity)

        if adjusted_qty >= order.quantity:
            # No adjustment needed
            return order

        # Return a new Order with the capped quantity
        return Order(
            side=order.side,
            quantity=adjusted_qty,
            price=order.price,
            timestamp=order.timestamp,
        )
