"""
Tests for execution.strategy_registry.StrategyRegistry

Contract
--------
StrategyRegistry()

    register(name: str, strategy_class: type) -> None
        Raises ValueError on duplicate name.

    unregister(name: str) -> None
        Raises KeyError on unknown name.

    get(name: str) -> type
        Raises KeyError on unknown name.

    list_strategies() -> list[str]
        Returns names in insertion order.

Rules
-----
* No global state — each instance is independent.
* Stored classes are never mutated.
* Insertion order is preserved.
"""

import pytest

from execution.strategy_registry import StrategyRegistry


# ---------------------------------------------------------------------------
# Dummy strategy classes used as fixtures
# ---------------------------------------------------------------------------

class StrategyAlpha:
    def generate_signal(self, candle):
        return "HOLD"


class StrategyBeta:
    def generate_signal(self, candle):
        return "BUY"


class StrategyGamma:
    def generate_signal(self, candle):
        return "SELL"


# ===========================================================================
# Part 1 — register + get
# ===========================================================================

def test_register_and_get_returns_correct_class():
    registry = StrategyRegistry()
    registry.register("alpha", StrategyAlpha)
    assert registry.get("alpha") is StrategyAlpha


def test_register_and_get_multiple_strategies():
    registry = StrategyRegistry()
    registry.register("alpha", StrategyAlpha)
    registry.register("beta", StrategyBeta)
    assert registry.get("alpha") is StrategyAlpha
    assert registry.get("beta") is StrategyBeta


def test_get_returns_class_not_instance():
    registry = StrategyRegistry()
    registry.register("alpha", StrategyAlpha)
    result = registry.get("alpha")
    assert result is StrategyAlpha
    assert isinstance(result, type)


# ===========================================================================
# Part 2 — duplicate registration raises ValueError
# ===========================================================================

def test_duplicate_registration_raises_value_error():
    registry = StrategyRegistry()
    registry.register("alpha", StrategyAlpha)
    with pytest.raises(ValueError):
        registry.register("alpha", StrategyBeta)


def test_duplicate_registration_error_message_contains_name():
    registry = StrategyRegistry()
    registry.register("my_strategy", StrategyAlpha)
    with pytest.raises(ValueError, match="my_strategy"):
        registry.register("my_strategy", StrategyAlpha)


def test_duplicate_registration_does_not_overwrite_original():
    registry = StrategyRegistry()
    registry.register("alpha", StrategyAlpha)
    try:
        registry.register("alpha", StrategyBeta)
    except ValueError:
        pass
    # Original must still be intact
    assert registry.get("alpha") is StrategyAlpha


# ===========================================================================
# Part 3 — unregister
# ===========================================================================

def test_unregister_removes_strategy():
    registry = StrategyRegistry()
    registry.register("alpha", StrategyAlpha)
    registry.unregister("alpha")
    assert "alpha" not in registry.list_strategies()


def test_unregister_allows_reregistration():
    registry = StrategyRegistry()
    registry.register("alpha", StrategyAlpha)
    registry.unregister("alpha")
    registry.register("alpha", StrategyBeta)
    assert registry.get("alpha") is StrategyBeta


def test_unregister_unknown_raises_key_error():
    registry = StrategyRegistry()
    with pytest.raises(KeyError):
        registry.unregister("nonexistent")


def test_unregister_does_not_affect_other_strategies():
    registry = StrategyRegistry()
    registry.register("alpha", StrategyAlpha)
    registry.register("beta", StrategyBeta)
    registry.unregister("alpha")
    assert registry.get("beta") is StrategyBeta


# ===========================================================================
# Part 4 — get unknown raises KeyError
# ===========================================================================

def test_get_unknown_raises_key_error():
    registry = StrategyRegistry()
    with pytest.raises(KeyError):
        registry.get("nonexistent")


def test_get_after_unregister_raises_key_error():
    registry = StrategyRegistry()
    registry.register("alpha", StrategyAlpha)
    registry.unregister("alpha")
    with pytest.raises(KeyError):
        registry.get("alpha")


# ===========================================================================
# Part 5 — list_strategies preserves insertion order
# ===========================================================================

def test_list_strategies_empty_registry():
    registry = StrategyRegistry()
    assert registry.list_strategies() == []


def test_list_strategies_single_entry():
    registry = StrategyRegistry()
    registry.register("alpha", StrategyAlpha)
    assert registry.list_strategies() == ["alpha"]


def test_list_strategies_preserves_insertion_order():
    registry = StrategyRegistry()
    registry.register("gamma", StrategyGamma)
    registry.register("alpha", StrategyAlpha)
    registry.register("beta", StrategyBeta)
    assert registry.list_strategies() == ["gamma", "alpha", "beta"]


def test_list_strategies_after_unregister_preserves_remaining_order():
    registry = StrategyRegistry()
    registry.register("alpha", StrategyAlpha)
    registry.register("beta", StrategyBeta)
    registry.register("gamma", StrategyGamma)
    registry.unregister("beta")
    assert registry.list_strategies() == ["alpha", "gamma"]


def test_list_strategies_returns_new_list_each_call():
    """Mutating the returned list must not affect the registry."""
    registry = StrategyRegistry()
    registry.register("alpha", StrategyAlpha)
    names = registry.list_strategies()
    names.append("injected")
    assert registry.list_strategies() == ["alpha"]


# ===========================================================================
# Part 6 — No global state (instances are independent)
# ===========================================================================

def test_two_registries_are_independent():
    r1 = StrategyRegistry()
    r2 = StrategyRegistry()
    r1.register("alpha", StrategyAlpha)
    assert "alpha" not in r2.list_strategies()


def test_unregister_in_one_registry_does_not_affect_another():
    r1 = StrategyRegistry()
    r2 = StrategyRegistry()
    r1.register("alpha", StrategyAlpha)
    r2.register("alpha", StrategyAlpha)
    r1.unregister("alpha")
    assert r2.get("alpha") is StrategyAlpha


# ===========================================================================
# Part 7 — Stored classes are not mutated
# ===========================================================================

def test_registered_class_is_identical_object():
    registry = StrategyRegistry()
    registry.register("alpha", StrategyAlpha)
    retrieved = registry.get("alpha")
    # Must be the exact same object, not a copy
    assert retrieved is StrategyAlpha


def test_registered_class_is_still_instantiable():
    registry = StrategyRegistry()
    registry.register("alpha", StrategyAlpha)
    cls = registry.get("alpha")
    instance = cls()
    assert instance.generate_signal({}) == "HOLD"
