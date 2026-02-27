"""
execution.portfolio_engine
==========================

Multi-strategy portfolio engine.

Manages multiple strategies simultaneously, allocates capital per strategy
using a separate :class:`PaperBroker` for each, and aggregates portfolio
equity across all sub-strategies.

Usage
-----
    from execution.portfolio_engine import PortfolioEngine
    from execution.risk_manager import RiskManager

    engine = PortfolioEngine(
        strategies=[StrategyA, StrategyB],
        initial_capital=10_000,
        allocation="equal",
    )
    result = engine.run(candles)

Design
------
* Each strategy gets its own :class:`PaperBroker` and
  :class:`ExecutionGateway` — no shared state between strategies.
* Capital is split equally across strategies (``allocation="equal"``).
* The aggregated equity curve is the element-wise sum of all individual
  equity curves.
* Deterministic: same candles always produce the same result.
* Input candles are never mutated.

Validation
----------
* ``strategies`` must not be empty → ``ValueError``
* ``initial_capital`` must be > 0 → ``ValueError``
* ``allocation`` must be ``"equal"`` → ``ValueError`` for any other value
"""

from execution.paper_broker import PaperBroker
from execution.execution_gateway import ExecutionGateway


class PortfolioEngine:
    """
    Multi-strategy portfolio engine with equal capital allocation.

    Parameters
    ----------
    strategies : list[type]
        Non-empty list of strategy classes (not instances).  Each must
        expose ``generate_signal(candle: dict) -> str``.
    initial_capital : float
        Total capital to distribute across all strategies.  Must be > 0.
    allocation : str, optional
        Capital allocation scheme.  Only ``"equal"`` is supported.
        Default ``"equal"``.
    risk_manager : RiskManager or None, optional
        If provided, the same :class:`RiskManager` instance is passed to
        every :class:`ExecutionGateway`.  Default ``None``.

    Raises
    ------
    ValueError
        If ``strategies`` is empty, ``initial_capital`` <= 0, or
        ``allocation`` is not ``"equal"``.
    """

    def __init__(
        self,
        strategies: list,
        initial_capital: float,
        allocation: str = "equal",
        risk_manager=None,
    ) -> None:
        if not strategies:
            raise ValueError("strategies must not be empty")
        if initial_capital <= 0:
            raise ValueError(
                f"initial_capital must be > 0, got {initial_capital!r}"
            )
        if allocation != "equal":
            raise ValueError(
                f"allocation must be 'equal', got {allocation!r}"
            )

        self._strategies = list(strategies)
        self._initial_capital = float(initial_capital)
        self._allocation = allocation
        self._risk_manager = risk_manager

        # Build one broker + gateway per strategy
        capital_per = self._initial_capital / len(self._strategies)
        self._brokers: list = []
        self._gateways: list = []

        for strategy_class in self._strategies:
            broker = PaperBroker(initial_cash=capital_per)
            gateway = ExecutionGateway(
                strategy_class,
                broker,
                risk_manager=risk_manager,
            )
            self._brokers.append(broker)
            self._gateways.append(gateway)

        # Aggregated equity curve (built during run())
        self._portfolio_equity_curve: list = []
        self._last_price: float = 0.0

    # ------------------------------------------------------------------

    def run(self, candles: list) -> dict:
        """
        Feed every candle to all gateways and return the aggregated result.

        Parameters
        ----------
        candles : list[dict]
            Chronological OHLCV candles.  Each must contain ``"close"``.
            Not mutated.

        Returns
        -------
        dict with keys:
            portfolio_equity        : float
            portfolio_equity_curve  : list[float]
            strategies              : dict[str, dict]
                Per-strategy state:
                    cash, position_size, equity, trade_history
        """
        # Reset aggregated curve for idempotent re-runs
        self._portfolio_equity_curve = []

        for candle in candles:
            price = float(candle["close"])
            self._last_price = price

            # Feed candle to every gateway
            for gateway in self._gateways:
                gateway.on_candle(candle)

            # Aggregate equity at this step
            step_equity = sum(
                broker.cash + broker.position_size * price
                for broker in self._brokers
            )
            self._portfolio_equity_curve.append(step_equity)

        # Build final state
        portfolio_equity = sum(
            broker.cash + broker.position_size * self._last_price
            for broker in self._brokers
        )

        strategies_state = {}
        for strategy_class, broker, gateway in zip(
            self._strategies, self._brokers, self._gateways
        ):
            gw_state = gateway.get_state()
            strategies_state[strategy_class.__name__] = {
                "cash":          gw_state["cash"],
                "position_size": gw_state["position_size"],
                "equity":        gw_state["equity"],
                "trade_history": gw_state["trade_history"],
            }

        return {
            "portfolio_equity":       portfolio_equity,
            "portfolio_equity_curve": list(self._portfolio_equity_curve),
            "strategies":             strategies_state,
        }
