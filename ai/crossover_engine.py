"""
ai.crossover_engine
====================

Genome crossover engine for the evolutionary strategy optimizer.

Crossover combines parameters from two parent genomes to produce a child
genome.  Both parents must have the same ``type``.

Usage
-----
    engine = CrossoverEngine(seed=42)
    child = engine.crossover(parent_a, parent_b)
"""

import random
import copy

from ai.strategy_genome import GENOME_BOUNDS, validate_genome


class CrossoverEngine:
    """
    Combine two parent genomes to produce a child genome.

    Parameters
    ----------
    seed : int or None, optional
        Random seed for deterministic crossover.  Default ``None``.
    """

    def __init__(self, seed=None) -> None:
        self._rng = random.Random(seed)

    # ------------------------------------------------------------------

    def crossover(self, parent_a: dict, parent_b: dict) -> dict:
        """
        Produce a child genome by uniform crossover of *parent_a* and
        *parent_b*.

        For each parameter, the child inherits the value from either
        parent with equal probability (50/50).

        Parameters
        ----------
        parent_a : dict
            First parent genome.  Not mutated.
        parent_b : dict
            Second parent genome.  Not mutated.  Must have the same
            ``type`` as *parent_a*.

        Returns
        -------
        dict
            Child genome.

        Raises
        ------
        ValueError
            If the parents have different ``type`` values.
        """
        validate_genome(parent_a)
        validate_genome(parent_b)

        if parent_a["type"] != parent_b["type"]:
            raise ValueError(
                f"Cannot crossover genomes of different types: "
                f"{parent_a['type']!r} vs {parent_b['type']!r}"
            )

        gtype = parent_a["type"]
        child = {"type": gtype}
        bounds = GENOME_BOUNDS[gtype]

        for param in bounds:
            # Uniform crossover: pick from either parent with 50% probability
            if self._rng.random() < 0.5:
                child[param] = parent_a[param]
            else:
                child[param] = parent_b[param]

        # Enforce moving_average constraint: short < long
        if gtype == "moving_average":
            if child["short"] >= child["long"]:
                # Use parent_a's values as fallback
                child["short"] = parent_a["short"]
                child["long"]  = parent_a["long"]

        return child
