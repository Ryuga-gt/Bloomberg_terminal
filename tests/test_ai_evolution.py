"""
Tests for the AI evolution engine modules:
  ai.strategy_genome
  ai.mutation_engine
  ai.crossover_engine
  ai.fitness_evaluator
  ai.evolution_engine
"""

import copy
import pytest

from ai.strategy_genome import (
    validate_genome,
    genome_to_strategy_class,
    GENOME_TYPES,
    GENOME_BOUNDS,
)
from ai.mutation_engine import MutationEngine
from ai.crossover_engine import CrossoverEngine
from ai.fitness_evaluator import FitnessEvaluator
from ai.evolution_engine import EvolutionEngine


# ---------------------------------------------------------------------------
# Candle factory
# ---------------------------------------------------------------------------

def make_candles(n: int = 30, start: float = 100.0, step: float = 1.0) -> list:
    candles = []
    price = start
    for i in range(n):
        candles.append({
            "timestamp": f"2024-01-{i+1:02d}",
            "open":   price,
            "high":   price + 1,
            "low":    price - 1,
            "close":  price,
            "volume": 1_000_000,
        })
        price += step
    return candles


CANDLES = make_candles(50)


# ===========================================================================
# Part 1 — strategy_genome
# ===========================================================================

def test_validate_genome_valid_ma():
    validate_genome({"type": "moving_average", "short": 5, "long": 20})


def test_validate_genome_valid_rsi():
    validate_genome({"type": "rsi", "period": 14, "overbought": 70, "oversold": 30})


def test_validate_genome_valid_breakout():
    validate_genome({"type": "breakout", "window": 20})


def test_validate_genome_missing_type_raises():
    with pytest.raises(ValueError):
        validate_genome({"short": 5, "long": 20})


def test_validate_genome_unknown_type_raises():
    with pytest.raises(ValueError):
        validate_genome({"type": "unknown", "short": 5, "long": 20})


def test_validate_genome_out_of_bounds_raises():
    with pytest.raises(ValueError):
        validate_genome({"type": "moving_average", "short": 1, "long": 20})


def test_genome_to_strategy_class_ma():
    cls = genome_to_strategy_class({"type": "moving_average", "short": 5, "long": 20})
    assert isinstance(cls, type)


def test_genome_to_strategy_class_rsi():
    cls = genome_to_strategy_class({"type": "rsi", "period": 14, "overbought": 70, "oversold": 30})
    assert isinstance(cls, type)


def test_genome_to_strategy_class_breakout():
    cls = genome_to_strategy_class({"type": "breakout", "window": 20})
    assert isinstance(cls, type)


def test_strategy_class_instantiable():
    cls = genome_to_strategy_class({"type": "moving_average", "short": 5, "long": 20})
    instance = cls()
    assert instance is not None


def test_strategy_class_generate_signal_returns_string():
    cls = genome_to_strategy_class({"type": "moving_average", "short": 5, "long": 20})
    instance = cls()
    candle = {"close": 100.0}
    signal = instance.generate_signal(candle)
    assert signal in ("BUY", "SELL", "HOLD")


def test_strategy_class_generate_signal_valid_for_all_candles():
    cls = genome_to_strategy_class({"type": "moving_average", "short": 5, "long": 20})
    instance = cls()
    for candle in CANDLES:
        signal = instance.generate_signal(candle)
        assert signal in ("BUY", "SELL", "HOLD")


# ===========================================================================
# Part 2 — MutationEngine
# ===========================================================================

def test_mutation_engine_invalid_rate_raises():
    with pytest.raises(ValueError):
        MutationEngine(mutation_rate=1.5)


def test_mutation_engine_returns_valid_genome():
    engine = MutationEngine(mutation_rate=1.0, seed=42)
    genome = {"type": "moving_average", "short": 5, "long": 20}
    mutated = engine.mutate(genome)
    validate_genome(mutated)


def test_mutation_engine_does_not_mutate_input():
    engine = MutationEngine(mutation_rate=1.0, seed=42)
    genome = {"type": "moving_average", "short": 5, "long": 20}
    original = copy.deepcopy(genome)
    engine.mutate(genome)
    assert genome == original


def test_mutation_engine_deterministic():
    engine1 = MutationEngine(mutation_rate=0.5, seed=42)
    engine2 = MutationEngine(mutation_rate=0.5, seed=42)
    genome = {"type": "moving_average", "short": 5, "long": 20}
    m1 = engine1.mutate(genome)
    m2 = engine2.mutate(genome)
    assert m1 == m2


def test_mutation_engine_zero_rate_no_change():
    engine = MutationEngine(mutation_rate=0.0, seed=42)
    genome = {"type": "moving_average", "short": 5, "long": 20}
    mutated = engine.mutate(genome)
    assert mutated["short"] == 5
    assert mutated["long"] == 20


def test_mutation_engine_ma_constraint_short_less_than_long():
    engine = MutationEngine(mutation_rate=1.0, seed=42)
    for _ in range(20):
        genome = {"type": "moving_average", "short": 5, "long": 20}
        mutated = engine.mutate(genome)
        assert mutated["short"] < mutated["long"]


# ===========================================================================
# Part 3 — CrossoverEngine
# ===========================================================================

def test_crossover_engine_returns_valid_genome():
    engine = CrossoverEngine(seed=42)
    pa = {"type": "moving_average", "short": 5, "long": 20}
    pb = {"type": "moving_average", "short": 10, "long": 50}
    child = engine.crossover(pa, pb)
    validate_genome(child)


def test_crossover_engine_different_types_raises():
    engine = CrossoverEngine(seed=42)
    pa = {"type": "moving_average", "short": 5, "long": 20}
    pb = {"type": "rsi", "period": 14, "overbought": 70, "oversold": 30}
    with pytest.raises(ValueError):
        engine.crossover(pa, pb)


def test_crossover_engine_does_not_mutate_parents():
    engine = CrossoverEngine(seed=42)
    pa = {"type": "moving_average", "short": 5, "long": 20}
    pb = {"type": "moving_average", "short": 10, "long": 50}
    orig_a = copy.deepcopy(pa)
    orig_b = copy.deepcopy(pb)
    engine.crossover(pa, pb)
    assert pa == orig_a
    assert pb == orig_b


def test_crossover_engine_deterministic():
    engine1 = CrossoverEngine(seed=42)
    engine2 = CrossoverEngine(seed=42)
    pa = {"type": "moving_average", "short": 5, "long": 20}
    pb = {"type": "moving_average", "short": 10, "long": 50}
    c1 = engine1.crossover(pa, pb)
    c2 = engine2.crossover(pa, pb)
    assert c1 == c2


def test_crossover_child_params_from_parents():
    """Child parameters must come from one of the two parents."""
    engine = CrossoverEngine(seed=42)
    pa = {"type": "moving_average", "short": 5, "long": 20}
    pb = {"type": "moving_average", "short": 10, "long": 50}
    child = engine.crossover(pa, pb)
    assert child["short"] in (5, 10)
    assert child["long"] in (20, 50)


# ===========================================================================
# Part 4 — FitnessEvaluator
# ===========================================================================

def test_fitness_evaluator_invalid_mode_raises():
    with pytest.raises(ValueError):
        FitnessEvaluator(CANDLES, mode="unknown")


def test_fitness_evaluator_returns_float():
    evaluator = FitnessEvaluator(CANDLES, mode="fast")
    genome = {"type": "moving_average", "short": 5, "long": 20}
    score = evaluator.evaluate(genome)
    assert isinstance(score, float)


def test_fitness_evaluator_deterministic():
    evaluator = FitnessEvaluator(CANDLES, mode="fast")
    genome = {"type": "moving_average", "short": 5, "long": 20}
    s1 = evaluator.evaluate(genome)
    s2 = evaluator.evaluate(genome)
    assert s1 == pytest.approx(s2)


# ===========================================================================
# Part 5 — EvolutionEngine
# ===========================================================================

def test_evolution_engine_invalid_population_raises():
    with pytest.raises(ValueError):
        EvolutionEngine(CANDLES, population_size=1)


def test_evolution_engine_invalid_generations_raises():
    with pytest.raises(ValueError):
        EvolutionEngine(CANDLES, generations=0)


def test_evolution_engine_run_returns_dict():
    engine = EvolutionEngine(
        CANDLES, population_size=4, generations=2, seed=42
    )
    result = engine.run()
    assert isinstance(result, dict)


def test_evolution_engine_result_has_best_genome():
    engine = EvolutionEngine(
        CANDLES, population_size=4, generations=2, seed=42
    )
    result = engine.run()
    assert "best_genome" in result


def test_evolution_engine_result_has_best_fitness():
    engine = EvolutionEngine(
        CANDLES, population_size=4, generations=2, seed=42
    )
    result = engine.run()
    assert "best_fitness" in result


def test_evolution_engine_result_has_generation_bests():
    engine = EvolutionEngine(
        CANDLES, population_size=4, generations=3, seed=42
    )
    result = engine.run()
    assert len(result["generation_bests"]) == 3


def test_evolution_engine_best_genome_is_valid():
    engine = EvolutionEngine(
        CANDLES, population_size=4, generations=2, seed=42
    )
    result = engine.run()
    validate_genome(result["best_genome"])


def test_evolution_engine_deterministic():
    engine1 = EvolutionEngine(
        CANDLES, population_size=4, generations=2, seed=42
    )
    engine2 = EvolutionEngine(
        CANDLES, population_size=4, generations=2, seed=42
    )
    r1 = engine1.run()
    r2 = engine2.run()
    assert r1["best_genome"] == r2["best_genome"]
    assert r1["best_fitness"] == pytest.approx(r2["best_fitness"])
