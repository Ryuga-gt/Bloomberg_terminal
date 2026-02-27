"""
ai.strategy_genome
==================

Strategy genome representation and strategy class factory.

A genome is a dict describing a trading strategy's parameters:

    moving_average:
        {"type": "moving_average", "short": int, "long": int}

    rsi:
        {"type": "rsi", "period": int, "overbought": int, "oversold": int}

    breakout:
        {"type": "breakout", "window": int}

The :func:`genome_to_strategy_class` factory converts a genome dict into
a concrete strategy class compatible with the existing execution layer
(``generate_signal(candle) -> str``).

All strategy classes generated here use only the candle history passed
to them via a stateful ``generate_signal`` call.  They maintain internal
state (price history) between calls.
"""

# ---------------------------------------------------------------------------
# Parameter bounds
# ---------------------------------------------------------------------------

GENOME_BOUNDS = {
    "moving_average": {
        "short": (2, 50),
        "long":  (10, 200),
    },
    "rsi": {
        "period":     (5, 30),
        "overbought": (60, 90),
        "oversold":   (10, 40),
    },
    "breakout": {
        "window": (5, 60),
    },
}

GENOME_TYPES = list(GENOME_BOUNDS.keys())


# ---------------------------------------------------------------------------
# Genome validation
# ---------------------------------------------------------------------------

def validate_genome(genome: dict) -> None:
    """
    Raise ``ValueError`` if *genome* is invalid.

    Parameters
    ----------
    genome : dict

    Raises
    ------
    ValueError
    """
    if "type" not in genome:
        raise ValueError("genome must have a 'type' key")
    gtype = genome["type"]
    if gtype not in GENOME_BOUNDS:
        raise ValueError(
            f"Unknown genome type {gtype!r}. "
            f"Must be one of {GENOME_TYPES}."
        )
    bounds = GENOME_BOUNDS[gtype]
    for param, (lo, hi) in bounds.items():
        if param not in genome:
            raise ValueError(f"genome missing required parameter '{param}'")
        v = genome[param]
        if not (lo <= v <= hi):
            raise ValueError(
                f"genome['{param}'] = {v} out of bounds [{lo}, {hi}]"
            )


# ---------------------------------------------------------------------------
# Strategy class factory
# ---------------------------------------------------------------------------

def genome_to_strategy_class(genome: dict) -> type:
    """
    Convert a genome dict into a concrete strategy class.

    The returned class exposes ``generate_signal(candle: dict) -> str``
    and maintains internal price history.

    Parameters
    ----------
    genome : dict
        A valid genome dict.

    Returns
    -------
    type
        A strategy class (not instance).
    """
    validate_genome(genome)
    gtype = genome["type"]

    if gtype == "moving_average":
        return _make_ma_strategy(genome["short"], genome["long"])
    elif gtype == "rsi":
        return _make_rsi_strategy(
            genome["period"], genome["overbought"], genome["oversold"]
        )
    elif gtype == "breakout":
        return _make_breakout_strategy(genome["window"])
    else:
        raise ValueError(f"Unknown genome type {gtype!r}")


# ---------------------------------------------------------------------------
# Strategy class builders
# ---------------------------------------------------------------------------

def _make_ma_strategy(short: int, long_: int) -> type:
    """Moving average crossover strategy."""

    class MovingAverageStrategy:
        _short = short
        _long  = long_

        def __init__(self):
            self._prices = []
            self._position = "FLAT"

        def generate_signal(self, candle: dict) -> str:
            self._prices.append(float(candle["close"]))
            n = len(self._prices)

            if n < self._long:
                return "HOLD"

            short_ma = sum(self._prices[-self._short:]) / self._short
            long_ma  = sum(self._prices[-self._long:])  / self._long

            if short_ma > long_ma and self._position == "FLAT":
                self._position = "LONG"
                return "BUY"
            elif short_ma < long_ma and self._position == "LONG":
                self._position = "FLAT"
                return "SELL"
            return "HOLD"

    MovingAverageStrategy.__name__ = f"MA_{short}_{long_}"
    MovingAverageStrategy.__qualname__ = MovingAverageStrategy.__name__
    return MovingAverageStrategy


def _make_rsi_strategy(period: int, overbought: int, oversold: int) -> type:
    """RSI-based mean-reversion strategy."""

    class RSIStrategy:
        _period     = period
        _overbought = overbought
        _oversold   = oversold

        def __init__(self):
            self._prices   = []
            self._position = "FLAT"

        def _rsi(self) -> float:
            prices = self._prices[-(self._period + 1):]
            if len(prices) < self._period + 1:
                return 50.0
            gains  = [max(prices[i] - prices[i-1], 0) for i in range(1, len(prices))]
            losses = [max(prices[i-1] - prices[i], 0) for i in range(1, len(prices))]
            avg_gain = sum(gains)  / len(gains)
            avg_loss = sum(losses) / len(losses)
            if avg_loss == 0:
                return 100.0
            rs = avg_gain / avg_loss
            return 100.0 - (100.0 / (1.0 + rs))

        def generate_signal(self, candle: dict) -> str:
            self._prices.append(float(candle["close"]))
            rsi = self._rsi()

            if rsi < self._oversold and self._position == "FLAT":
                self._position = "LONG"
                return "BUY"
            elif rsi > self._overbought and self._position == "LONG":
                self._position = "FLAT"
                return "SELL"
            return "HOLD"

    RSIStrategy.__name__ = f"RSI_{period}_{overbought}_{oversold}"
    RSIStrategy.__qualname__ = RSIStrategy.__name__
    return RSIStrategy


def _make_breakout_strategy(window: int) -> type:
    """Breakout strategy: BUY when price exceeds rolling high."""

    class BreakoutStrategy:
        _window = window

        def __init__(self):
            self._prices   = []
            self._position = "FLAT"

        def generate_signal(self, candle: dict) -> str:
            price = float(candle["close"])
            self._prices.append(price)
            n = len(self._prices)

            if n <= self._window:
                return "HOLD"

            rolling_high = max(self._prices[-(self._window + 1):-1])
            rolling_low  = min(self._prices[-(self._window + 1):-1])

            if price > rolling_high and self._position == "FLAT":
                self._position = "LONG"
                return "BUY"
            elif price < rolling_low and self._position == "LONG":
                self._position = "FLAT"
                return "SELL"
            return "HOLD"

    BreakoutStrategy.__name__ = f"Breakout_{window}"
    BreakoutStrategy.__qualname__ = BreakoutStrategy.__name__
    return BreakoutStrategy
