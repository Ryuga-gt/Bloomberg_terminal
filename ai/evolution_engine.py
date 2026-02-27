"""
ai.evolution_engine
====================

Genetic algorithm for evolving trading strategy genomes.

Algorithm
---------
1. Initialize a random population of genomes.
2. For each generation:
   a. Evaluate fitness of every genome.
   b. Select parents via tournament selection.
   c. Apply crossover to produce offspring.
   d. Apply mutation to offspring.
   e. Apply elitism: carry the best N genomes unchanged.
3. Return the best genome found.

Usage
-----
    engine = EvolutionEngine(
        candles=candles,
        population_size=20,
        generations=10,
        mutation_rate=0.3,
        crossover_rate=0.7,
        seed=42,
    )
    result = engine.run()
    best_genome = result["best_genome"]
"""

import random
import copy

from ai.strategy_genome import (
    GENOME_BOUNDS,
    GENOME_TYPES,
    validate_genome,
    genome_to_strategy_class,
)
from ai.mutation_engine import MutationEngine
from ai.crossover_engine import CrossoverEngine
from ai.fitness_evaluator import FitnessEvaluator


class EvolutionEngine:
    """
    Genetic algorithm for strategy genome evolution.

    Parameters
    ----------
    candles : list[dict]
        Historical OHLCV candles used for fitness evaluation.
    population_size : int, optional
        Number of genomes per generation.  Default 20.
    generations : int, optional
        Number of evolutionary generations.  Default 10.
    mutation_rate : float, optional
        Per-parameter mutation probability.  Default 0.3.
    crossover_rate : float, optional
        Probability of crossover vs. cloning.  Default 0.7.
    elitism : int, optional
        Number of top genomes carried unchanged to next generation.
        Default 2.
    tournament_size : int, optional
        Number of candidates in each tournament selection.  Default 3.
    fitness_mode : str, optional
        ``"fast"`` or ``"full"``.  Default ``"fast"``.
    initial_cash : float, optional
        Starting cash for fitness evaluation.  Default 1000.
    seed : int or None, optional
        Random seed for deterministic evolution.  Default ``None``.

    Raises
    ------
    ValueError
        If ``population_size`` < 2 or ``generations`` < 1.
    """

    def __init__(
        self,
        candles: list,
        population_size: int = 20,
        generations: int = 10,
        mutation_rate: float = 0.3,
        crossover_rate: float = 0.7,
        elitism: int = 2,
        tournament_size: int = 3,
        fitness_mode: str = "fast",
        initial_cash: float = 1000,
        seed=None,
    ) -> None:
        if population_size < 2:
            raise ValueError(f"population_size must be >= 2, got {population_size!r}")
        if generations < 1:
            raise ValueError(f"generations must be >= 1, got {generations!r}")

        self._candles        = candles
        self._pop_size       = population_size
        self._generations    = generations
        self._crossover_rate = crossover_rate
        self._elitism        = min(elitism, population_size)
        self._tournament_size = min(tournament_size, population_size)

        self._rng      = random.Random(seed)
        self._mutator  = MutationEngine(mutation_rate=mutation_rate, seed=seed)
        self._crossover = CrossoverEngine(seed=seed)
        self._evaluator = FitnessEvaluator(
            candles=candles,
            initial_cash=initial_cash,
            mode=fitness_mode,
        )

    # ------------------------------------------------------------------

    def run(self) -> dict:
        """
        Run the genetic algorithm.

        Returns
        -------
        dict with keys:
            best_genome     : dict
            best_fitness    : float
            generation_bests: list[float]  (best fitness per generation)
            history         : list[dict]   (all evaluated genomes + scores)
        """
        population = self._init_population()
        generation_bests = []
        history = []

        for gen in range(self._generations):
            # Evaluate fitness
            scored = []
            for genome in population:
                score = self._evaluator.evaluate(genome)
                scored.append((score, genome))
                history.append({"generation": gen, "genome": copy.deepcopy(genome),
                                 "fitness": score})

            # Sort descending by fitness
            scored.sort(key=lambda x: x[0], reverse=True)
            generation_bests.append(scored[0][0])

            # Build next generation
            next_pop = []

            # Elitism: carry top N unchanged
            for i in range(self._elitism):
                next_pop.append(copy.deepcopy(scored[i][1]))

            # Fill rest via selection + crossover + mutation
            while len(next_pop) < self._pop_size:
                parent_a = self._tournament_select(scored)
                if self._rng.random() < self._crossover_rate:
                    parent_b = self._tournament_select(scored)
                    # Only crossover same-type genomes
                    if parent_a["type"] == parent_b["type"]:
                        child = self._crossover.crossover(parent_a, parent_b)
                    else:
                        child = copy.deepcopy(parent_a)
                else:
                    child = copy.deepcopy(parent_a)

                child = self._mutator.mutate(child)
                next_pop.append(child)

            population = next_pop

        # Final evaluation
        final_scored = [
            (self._evaluator.evaluate(g), g) for g in population
        ]
        final_scored.sort(key=lambda x: x[0], reverse=True)
        best_fitness, best_genome = final_scored[0]

        return {
            "best_genome":      best_genome,
            "best_fitness":     best_fitness,
            "generation_bests": generation_bests,
            "history":          history,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _init_population(self) -> list:
        """Generate a random initial population."""
        population = []
        for _ in range(self._pop_size):
            gtype = self._rng.choice(GENOME_TYPES)
            genome = {"type": gtype}
            bounds = GENOME_BOUNDS[gtype]
            for param, (lo, hi) in bounds.items():
                genome[param] = self._rng.randint(lo, hi)

            # Enforce moving_average constraint
            if gtype == "moving_average":
                s_lo, s_hi = bounds["short"]
                l_lo, l_hi = bounds["long"]
                short = self._rng.randint(s_lo, s_hi)
                long_ = self._rng.randint(max(short + 1, l_lo), l_hi)
                genome["short"] = short
                genome["long"]  = long_

            population.append(genome)
        return population

    def _tournament_select(self, scored: list) -> dict:
        """Tournament selection: pick best from a random subset."""
        candidates = self._rng.sample(scored, min(self._tournament_size, len(scored)))
        best = max(candidates, key=lambda x: x[0])
        return copy.deepcopy(best[1])
