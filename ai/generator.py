"""
ai/generator.py — Deterministic mock strategy generator.

StrategyGenerator.generate(prompt: str) -> type

Returns a class whose instances satisfy:
    instance.generate(candles: list[dict]) -> list[str]

The mapping from prompt to strategy is keyword-based and fully deterministic.
No external API calls are made.

Strategy catalogue
------------------
Prompts containing 'momentum' or 'trend'  → MomentumStrategy
Prompts containing 'mean reversion'        → MeanReversionStrategy
Prompts containing 'conservative'          → ConservativeStrategy
Prompts containing 'aggressive'            → AggressiveStrategy
All other prompts                          → AlwaysLongStrategy (default)
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Concrete strategy classes
# ---------------------------------------------------------------------------

class AlwaysLongStrategy:
    """Buy on the first candle, hold to the end."""

    def generate(self, candles: list[dict]) -> list[str]:
        if not candles:
            return []
        return ["BUY"] + ["HOLD"] * (len(candles) - 1)


class MomentumStrategy:
    """
    Buy when the close is higher than the previous close; sell when it falls;
    hold otherwise.  First candle is always HOLD (no prior reference).
    """

    def generate(self, candles: list[dict]) -> list[str]:
        if not candles:
            return []
        signals = ["HOLD"]
        for i in range(1, len(candles)):
            prev_close = candles[i - 1]["close"]
            curr_close = candles[i]["close"]
            if curr_close > prev_close:
                signals.append("BUY")
            elif curr_close < prev_close:
                signals.append("SELL")
            else:
                signals.append("HOLD")
        return signals


class MeanReversionStrategy:
    """
    Computes a simple moving average over all preceding candles.
    Buy when price is below average (cheap), sell when above (expensive).
    First candle is HOLD.
    """

    def generate(self, candles: list[dict]) -> list[str]:
        if not candles:
            return []
        signals = ["HOLD"]
        for i in range(1, len(candles)):
            closes = [c["close"] for c in candles[:i]]
            avg = sum(closes) / len(closes)
            curr_close = candles[i]["close"]
            if curr_close < avg:
                signals.append("BUY")
            elif curr_close > avg:
                signals.append("SELL")
            else:
                signals.append("HOLD")
        return signals


class ConservativeStrategy:
    """
    Buy once at the start, sell at the midpoint, stay flat for the remainder.
    Low activity, limited exposure.
    """

    def generate(self, candles: list[dict]) -> list[str]:
        n = len(candles)
        if n == 0:
            return []
        if n == 1:
            return ["HOLD"]
        mid = n // 2
        signals = ["BUY"]
        for i in range(1, n):
            if i == mid:
                signals.append("SELL")
            else:
                signals.append("HOLD")
        return signals


class AggressiveStrategy:
    """
    Alternates BUY / SELL on every candle to maximise trade frequency.
    First candle is always BUY.
    """

    def generate(self, candles: list[dict]) -> list[str]:
        signals = []
        for i in range(len(candles)):
            signals.append("BUY" if i % 2 == 0 else "SELL")
        return signals


# ---------------------------------------------------------------------------
# Strategy registry — ordered so more-specific keywords take priority
# ---------------------------------------------------------------------------

_REGISTRY: list[tuple[tuple[str, ...], type]] = [
    (("mean reversion",),                          MeanReversionStrategy),
    (("momentum", "trend"),                        MomentumStrategy),
    (("conservative",),                            ConservativeStrategy),
    (("aggressive",),                              AggressiveStrategy),
]

_DEFAULT_STRATEGY: type = AlwaysLongStrategy


# ---------------------------------------------------------------------------
# StrategyGenerator
# ---------------------------------------------------------------------------

class StrategyGenerator:
    """
    Deterministic mock generator that maps a natural-language prompt to a
    concrete strategy class based on keyword matching.

    Usage::

        gen = StrategyGenerator()
        StrategyClass = gen.generate("aggressive momentum strategy")
        signals = StrategyClass().generate(candles)
    """

    def generate(self, prompt: str) -> type:
        """
        Map *prompt* to a strategy class.

        Parameters
        ----------
        prompt:
            A natural-language description of the desired strategy.

        Returns
        -------
        type
            A class (not an instance) whose ``generate(candles)`` method
            returns ``list[str]`` of signals (``"BUY"``, ``"SELL"``,
            ``"HOLD"``), one per candle.
        """
        lower = prompt.lower()
        for keywords, strategy_class in _REGISTRY:
            if any(kw in lower for kw in keywords):
                return strategy_class
        return _DEFAULT_STRATEGY
