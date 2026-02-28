"""
ai.mutation_engine
==================

Genome mutation engine for the evolutionary strategy optimizer.

Mutation randomly tweaks one or more parameters of a genome within their
defined bounds.  The mutation is deterministic when a seed is provided.

Usage
-----
    engine = MutationEngine(mutation_rate=0.3, seed=42)
    mutated = engine.mutate(genome)
"""

import random
import copy

from ai.strategy_genome import GENOME_BOUNDS, GENOME_TYPES, validate_genome


class MutationEngine:
    """
    Randomly mutate strategy genome parameters.

    Parameters
    ----------
    mutation_rate : float
        Probability that each parameter is mutated.  Must be in [0, 1].
    seed : int or None, optional
        Random seed for deterministic mutation.  Default ``None``.

    Raises
    ------
    ValueError
        If ``mutation_rate`` is not in [0, 1].
    """

    def __init__(self, mutation_rate: float = 0.3, seed=None) -> None:
        if not (0.0 <= mutation_rate <= 1.0):
            raise ValueError(
                f"mutation_rate must be in [0, 1], got {mutation_rate!r}"
            )
        self._mutation_rate = mutation_rate
        self._rng = random.Random(seed)

    # ------------------------------------------------------------------

    def mutate(self, genome: dict) -> dict:
        """
        Return a mutated copy of *genome*.

        Each integer parameter is independently mutated with probability
        ``mutation_rate``.  Mutation replaces the value with a new random
        integer within the parameter's bounds.

        Parameters
        ----------
        genome : dict
            A valid genome dict.  Not mutated.

        Returns
        -------
        dict
            New genome with (possibly) modified parameters.
        """
        validate_genome(genome)
        mutated = copy.deepcopy(genome)
        gtype = mutated["type"]
        bounds = GENOME_BOUNDS[gtype]

        for param, (lo, hi) in bounds.items():
            if self._rng.random() < self._mutation_rate:
                mutated[param] = self._rng.randint(lo, hi)

        # Enforce moving_average constraint: short < long
        if gtype == "moving_average":
            if mutated["short"] >= mutated["long"]:
                # Swap or clamp
                s_lo, s_hi = GENOME_BOUNDS["moving_average"]["short"]
                l_lo, l_hi = GENOME_BOUNDS["moving_average"]["long"]
                mutated["short"] = self._rng.randint(s_lo, s_hi)
                mutated["long"]  = self._rng.randint(
                    max(mutated["short"] + 1, l_lo), l_hi
                )

        return mutated
