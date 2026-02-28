"""
RED tests for ai.generator.StrategyGenerator contract.

Contract:
  - Class StrategyGenerator
  - Method generate(prompt: str) -> type
  - Returned type must implement:
        generate(self, candles: list[dict]) -> list[str]
"""

from ai.generator import StrategyGenerator

# ---------------------------------------------------------------------------
# Minimal candle fixtures
# ---------------------------------------------------------------------------
CANDLES = [
    {"timestamp": "2024-01-01", "open": 99.0,  "high": 101.0, "low": 98.0,  "close": 100.0, "volume": 1_000_000},
    {"timestamp": "2024-01-02", "open": 100.5, "high": 111.0, "low": 100.0, "close": 110.0, "volume": 1_200_000},
    {"timestamp": "2024-01-03", "open": 105.0, "high": 111.0, "low": 104.5, "close": 115.0, "volume": 1_300_000},
]


# ---------------------------------------------------------------------------
# StrategyGenerator instantiation
# ---------------------------------------------------------------------------

def test_strategy_generator_is_instantiable():
    gen = StrategyGenerator()
    assert gen is not None


# ---------------------------------------------------------------------------
# generate() returns a type (class), not an instance
# ---------------------------------------------------------------------------

def test_generate_returns_a_type():
    gen = StrategyGenerator()
    result = gen.generate("buy when price rises")
    assert isinstance(result, type), (
        f"generate() must return a class (type), got {type(result)}"
    )


# ---------------------------------------------------------------------------
# The returned class must be instantiable with no arguments
# ---------------------------------------------------------------------------

def test_generate_returned_class_is_instantiable():
    gen = StrategyGenerator()
    StrategyClass = gen.generate("simple momentum strategy")
    instance = StrategyClass()
    assert instance is not None


# ---------------------------------------------------------------------------
# The returned class instance must have a generate() method
# ---------------------------------------------------------------------------

def test_generated_class_has_generate_method():
    gen = StrategyGenerator()
    StrategyClass = gen.generate("any prompt")
    instance = StrategyClass()
    assert hasattr(instance, "generate"), (
        "Returned class instance must have a generate() method"
    )
    assert callable(instance.generate), (
        "generate attribute must be callable"
    )


# ---------------------------------------------------------------------------
# The generate() method on the returned instance must accept candles
# ---------------------------------------------------------------------------

def test_generated_class_generate_accepts_candles():
    gen = StrategyGenerator()
    StrategyClass = gen.generate("buy low sell high")
    instance = StrategyClass()
    # Must not raise
    result = instance.generate(CANDLES)
    assert result is not None


# ---------------------------------------------------------------------------
# The generate() method must return a list of strings
# ---------------------------------------------------------------------------

def test_generated_class_generate_returns_list_of_strings():
    gen = StrategyGenerator()
    StrategyClass = gen.generate("always buy strategy")
    instance = StrategyClass()
    signals = instance.generate(CANDLES)
    assert isinstance(signals, list), (
        f"generate() must return a list, got {type(signals)}"
    )
    for s in signals:
        assert isinstance(s, str), (
            f"Every signal must be a str, got {type(s)}"
        )


# ---------------------------------------------------------------------------
# Each signal must be one of the valid values: BUY, SELL, HOLD
# ---------------------------------------------------------------------------

def test_generated_class_generate_returns_valid_signals():
    valid = {"BUY", "SELL", "HOLD"}
    gen = StrategyGenerator()
    StrategyClass = gen.generate("trend following")
    instance = StrategyClass()
    signals = instance.generate(CANDLES)
    for s in signals:
        assert s in valid, (
            f"Signal '{s}' is not valid; must be one of {valid}"
        )


# ---------------------------------------------------------------------------
# Signal list length must match candles length
# ---------------------------------------------------------------------------

def test_generated_class_generate_returns_one_signal_per_candle():
    gen = StrategyGenerator()
    StrategyClass = gen.generate("any strategy")
    instance = StrategyClass()
    signals = instance.generate(CANDLES)
    assert len(signals) == len(CANDLES), (
        f"Expected {len(CANDLES)} signals, got {len(signals)}"
    )


# ---------------------------------------------------------------------------
# Different prompts may return different (or same) classes, but each
# returned class must independently satisfy the contract
# ---------------------------------------------------------------------------

def test_generate_called_with_different_prompts_both_satisfy_contract():
    gen = StrategyGenerator()
    ClassA = gen.generate("aggressive momentum")
    ClassB = gen.generate("conservative mean reversion")

    for StrategyClass in (ClassA, ClassB):
        instance = StrategyClass()
        signals = instance.generate(CANDLES)
        assert isinstance(signals, list)
        assert len(signals) == len(CANDLES)
        for s in signals:
            assert s in {"BUY", "SELL", "HOLD"}


# ---------------------------------------------------------------------------
# Returned class must be deterministic — same prompt → same signals
# ---------------------------------------------------------------------------

def test_generate_is_deterministic_for_same_prompt():
    gen = StrategyGenerator()
    StrategyClass1 = gen.generate("deterministic prompt")
    StrategyClass2 = gen.generate("deterministic prompt")

    signals1 = StrategyClass1().generate(CANDLES)
    signals2 = StrategyClass2().generate(CANDLES)

    assert signals1 == signals2, (
        "Same prompt must produce the same signals (deterministic)"
    )
