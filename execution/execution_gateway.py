"""
execution.execution_gateway
============================

Candle-by-candle forward execution gateway for paper/live trading simulation.

This is NOT a backtester.  It processes one candle at a time via
``on_candle()``, delegating order execution to a :class:`BrokerInterface`
implementation and optionally enforcing position-size limits via a
:class:`RiskManager`.

Usage
-----
    from execution.paper_broker import PaperBroker
    from execution.risk_manager import RiskManager

    broker = PaperBroker(initial_cash=5000)
    rm     = RiskManager(max_position_pct=0.5)
    gateway = ExecutionGateway(MyStrategyClass, broker, risk_manager=rm)

    for candle in live_feed:
        gateway.on_candle(candle)

    state = gateway.get_state()

Execution model
---------------
* All-in BUY: uses all available broker cash to purchase shares at the
  candle's close price.
* SELL: closes the entire position at the close price.
* No shorting.
* Redundant signals are silently ignored:
    - BUY when already LONG → ignored
    - SELL when already FLAT → ignored
* If a :class:`RiskManager` is provided, the BUY order quantity is capped
  before being sent to the broker.

Signal interface
----------------
The strategy class must expose::

    generate_signal(candle: dict) -> str   # "BUY" | "SELL" | "HOLD"

Validation
----------
* ``candle`` must contain the key ``"close"`` → ``KeyError``
* Input candles are never mutated.
"""

from execution.broker_interface import BrokerInterface
from execution.order import Order, BUY, SELL


class ExecutionGateway:
    """
    Broker-driven forward execution gateway.

    Parameters
    ----------
    strategy_class : type
        Strategy class (not instance).  Must expose
        ``generate_signal(candle: dict) -> str``.
    broker : BrokerInterface
        Broker instance that executes orders and maintains cash/position.
    risk_manager : RiskManager or None, optional
        If provided, BUY order quantities are capped before execution.
        Default ``None`` (no risk management).
    """

    def __init__(
        self,
        strategy_class: type,
        broker: BrokerInterface,
        risk_manager=None,
    ) -> None:
        self._strategy = strategy_class()
        self._broker = broker
        self._risk_manager = risk_manager

        # Gateway-level state (broker owns cash/position)
        self._state: str = "FLAT"          # "FLAT" | "LONG"
        self._current_price: float = 0.0

        self._equity_curve: list = []
        self._trade_history: list = []

    # ------------------------------------------------------------------
    def _equity(self, price: float) -> float:
        """Mark-to-market equity at *price*."""
        return self._broker.cash + self._broker.position_size * price

    # ------------------------------------------------------------------
    def on_candle(self, candle: dict) -> None:
        """
        Process a single candle.

        Parameters
        ----------
        candle : dict
            Must contain at least ``"close"`` (float).  Not mutated.

        Raises
        ------
        KeyError
            If ``candle`` does not contain ``"close"``.
        """
        if "close" not in candle:
            raise KeyError("candle must contain the key 'close'")

        price = float(candle["close"])
        self._current_price = price

        signal = self._strategy.generate_signal(candle)

        if signal == BUY and self._state == "FLAT":
            # All-in: buy as many shares as cash allows
            quantity = self._broker.cash / price
            order = Order(side=BUY, quantity=quantity, price=price)

            # Apply risk manager if present
            if self._risk_manager is not None:
                equity = self._equity(price)
                order = self._risk_manager.adjust_order(order, equity)

            fill = self._broker.execute_order(order)
            self._state = "LONG"
            self._trade_history.append({
                "type":       "BUY",
                "price":      fill.price,
                "shares":     fill.quantity,
                "cash_after": self._broker.cash,
            })

        elif signal == SELL and self._state == "LONG":
            # Close full position
            quantity = self._broker.position_size
            order = Order(side=SELL, quantity=quantity, price=price)
            fill = self._broker.execute_order(order)
            self._state = "FLAT"
            self._trade_history.append({
                "type":       "SELL",
                "price":      fill.price,
                "shares":     fill.quantity,
                "cash_after": self._broker.cash,
            })

        # HOLD or redundant signal → no action

        # Always update equity curve
        self._equity_curve.append(self._equity(price))

    # ------------------------------------------------------------------
    def get_state(self) -> dict:
        """
        Return a snapshot of the current gateway state.

        Returns
        -------
        dict with keys:
            cash          : float
            position_size : float
            equity        : float
            equity_curve  : list[float]
            trade_history : list[dict]
            state         : str  ("FLAT" or "LONG")
        """
        current_equity = self._equity(self._current_price)
        return {
            "cash":          self._broker.cash,
            "position_size": self._broker.position_size,
            "equity":        current_equity,
            "equity_curve":  list(self._equity_curve),
            "trade_history": [dict(t) for t in self._trade_history],
            "state":         self._state,
        }
