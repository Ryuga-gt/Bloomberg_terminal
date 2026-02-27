"""
execution.execution_gateway
============================

Candle-by-candle forward execution gateway for paper/live trading simulation.

This is NOT a backtester.  It processes one candle at a time via
``on_candle()``, maintaining live state (cash, position, equity, trade
history, equity curve).

Usage
-----
    gateway = ExecutionGateway(MyStrategyClass, initial_cash=5000)
    for candle in live_feed:
        gateway.on_candle(candle)
    state = gateway.get_state()

Execution model
---------------
* All-in: a BUY uses all available cash to purchase shares at the
  candle's close price.
* A SELL closes the entire position at the close price.
* No shorting.
* Redundant signals are silently ignored:
    - BUY when already LONG → ignored
    - SELL when already FLAT → ignored

Signal interface
----------------
The strategy class must expose::

    generate_signal(candle: dict) -> str   # "BUY" | "SELL" | "HOLD"

Validation
----------
* ``initial_cash`` must be > 0 → ``ValueError``
* ``candle`` must contain the key ``"close"`` → ``KeyError``
* Input candles are never mutated.
"""


class ExecutionGateway:
    """
    Forward execution gateway.

    Parameters
    ----------
    strategy_class : type
        Strategy class (not instance).  Must expose
        ``generate_signal(candle: dict) -> str``.
    initial_cash : float, optional
        Starting cash balance.  Must be > 0.  Default 1000.

    Raises
    ------
    ValueError
        If ``initial_cash`` is not > 0.
    """

    def __init__(self, strategy_class: type, initial_cash: float = 1000) -> None:
        if initial_cash <= 0:
            raise ValueError(
                f"initial_cash must be > 0, got {initial_cash!r}"
            )

        self._strategy = strategy_class()
        self._initial_cash = float(initial_cash)

        # Mutable state
        self._cash: float = float(initial_cash)
        self._position_size: float = 0.0   # shares held
        self._current_price: float = 0.0
        self._state: str = "FLAT"          # "FLAT" | "LONG"

        self._equity_curve: list = []
        self._trade_history: list = []

    # ------------------------------------------------------------------
    @property
    def _equity(self) -> float:
        """Current mark-to-market equity."""
        return self._cash + self._position_size * self._current_price

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

        if signal == "BUY" and self._state == "FLAT":
            # All-in purchase
            shares = self._cash / price
            self._position_size = shares
            self._cash = 0.0
            self._state = "LONG"
            self._trade_history.append({
                "type": "BUY",
                "price": price,
                "shares": shares,
                "cash_after": self._cash,
            })

        elif signal == "SELL" and self._state == "LONG":
            # Close full position
            proceeds = self._position_size * price
            self._cash = proceeds
            self._position_size = 0.0
            self._state = "FLAT"
            self._trade_history.append({
                "type": "SELL",
                "price": price,
                "shares": 0.0,   # no shares held after sell
                "cash_after": self._cash,
            })

        # HOLD or redundant signal → no action

        # Always update equity curve
        self._equity_curve.append(self._equity)

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
        return {
            "cash":          self._cash,
            "position_size": self._position_size,
            "equity":        self._equity,
            "equity_curve":  list(self._equity_curve),
            "trade_history": [dict(t) for t in self._trade_history],
            "state":         self._state,
        }
