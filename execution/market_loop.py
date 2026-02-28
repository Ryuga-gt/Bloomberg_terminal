"""
execution.market_loop
=====================

Simple event-driven market loop that feeds candles one-by-one into an
:class:`ExecutionGateway`.

Usage
-----
    from execution.paper_broker import PaperBroker
    from execution.execution_gateway import ExecutionGateway
    from execution.market_loop import MarketLoop

    broker  = PaperBroker(initial_cash=1000)
    gateway = ExecutionGateway(MyStrategy, broker)
    loop    = MarketLoop(gateway)
    result  = loop.run(candles)

The loop is:

* **Deterministic** — same candles always produce the same result.
* **Non-mutating** — input candles are never modified.
* **Synchronous** — no async, no threading.
"""

from execution.execution_gateway import ExecutionGateway


class MarketLoop:
    """
    Event-driven loop that drives an :class:`ExecutionGateway` through a
    sequence of candles.

    Parameters
    ----------
    gateway : ExecutionGateway
        A fully configured gateway (with broker and optional risk manager).
    """

    def __init__(self, gateway: ExecutionGateway) -> None:
        self._gateway = gateway

    # ------------------------------------------------------------------

    def run(self, candles: list) -> dict:
        """
        Feed every candle in *candles* to the gateway in order.

        Parameters
        ----------
        candles : list[dict]
            Chronological sequence of OHLCV candles.  Each must contain
            at least ``"close"``.  Not mutated.

        Returns
        -------
        dict
            The final gateway state as returned by
            :meth:`ExecutionGateway.get_state`.
        """
        for candle in candles:
            self._gateway.on_candle(candle)

        return self._gateway.get_state()
