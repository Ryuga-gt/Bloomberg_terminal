"""
ai/feedback_loop.py — Iterative strategy research loop.

StrategyResearchLoop.run(
    prompt: str,
    candles: list[dict],
    iterations: int,
) -> dict

Algorithm
---------
For each iteration *i* in range(iterations):
  1. Generate a strategy class from the current prompt.
  2. Evaluate the strategy against the candles.
  3. Store (prompt, strategy_class, metrics) in the history.
  4. Apply a simple heuristic to adjust the prompt for the next iteration:
       - If fitness improved  → reinforce the prompt by appending
         "optimise for returns"
       - If fitness regressed → switch to a complementary style by
         appending "conservative mean reversion"
       - If fitness is equal  → nudge with "trend momentum"

Return a dict containing:
    best_strategy_class — the strategy class with the highest fitness_score
    best_metrics        — the metrics dict for that strategy
    best_prompt         — the prompt that produced the best strategy
    history             — list of dicts, one per iteration:
                            {iteration, prompt, strategy_class, metrics}
"""

from __future__ import annotations

from ai.generator import StrategyGenerator
from ai.evaluator import StrategyEvaluator


class StrategyResearchLoop:
    """
    Runs an iterative generate → evaluate → adjust loop to search for a
    high-fitness trading strategy.

    Usage::

        loop = StrategyResearchLoop()
        result = loop.run(
            prompt="momentum strategy",
            candles=candles,
            iterations=5,
        )
        best_class   = result["best_strategy_class"]
        best_metrics = result["best_metrics"]
    """

    def __init__(self) -> None:
        self._generator = StrategyGenerator()
        self._evaluator = StrategyEvaluator()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(
        self,
        prompt: str,
        candles: list[dict],
        iterations: int,
    ) -> dict:
        """
        Execute the research loop.

        Parameters
        ----------
        prompt:
            Initial natural-language strategy description.
        candles:
            Market data to back-test against.  Never mutated.
        iterations:
            Number of generate-evaluate-adjust cycles to perform.
            Must be >= 1.

        Returns
        -------
        dict with keys:
            ``best_strategy_class``, ``best_metrics``, ``best_prompt``,
            ``history``.
        """
        if iterations < 1:
            raise ValueError(f"iterations must be >= 1, got {iterations}")

        history: list[dict] = []
        current_prompt: str = prompt

        best_fitness: float = float("-inf")
        best_strategy_class: type | None = None
        best_metrics: dict | None = None
        best_prompt: str = current_prompt

        prev_fitness: float = float("-inf")

        for i in range(iterations):
            # 1. Generate
            strategy_class = self._generator.generate(current_prompt)

            # 2. Evaluate
            metrics = self._evaluator.evaluate(strategy_class, candles)
            fitness: float = metrics["fitness_score"]

            # 3. Store
            history.append(
                {
                    "iteration": i,
                    "prompt": current_prompt,
                    "strategy_class": strategy_class,
                    "metrics": metrics,
                }
            )

            # Track the best result seen so far
            if fitness > best_fitness:
                best_fitness = fitness
                best_strategy_class = strategy_class
                best_metrics = metrics
                best_prompt = current_prompt

            # 4. Adjust prompt heuristic (only if there will be a next iteration)
            if i < iterations - 1:
                current_prompt = self._adjust_prompt(
                    current_prompt, fitness, prev_fitness
                )

            prev_fitness = fitness

        return {
            "best_strategy_class": best_strategy_class,
            "best_metrics": best_metrics,
            "best_prompt": best_prompt,
            "history": history,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _adjust_prompt(
        prompt: str,
        current_fitness: float,
        prev_fitness: float,
    ) -> str:
        """
        Apply a simple heuristic to evolve *prompt* for the next iteration.

        - Improved fitness  → reinforce with "optimise for returns"
        - Worse fitness     → switch direction with "conservative mean reversion"
        - Equal fitness     → nudge with "trend momentum"
        """
        if current_fitness > prev_fitness:
            suffix = "optimise for returns"
        elif current_fitness < prev_fitness:
            suffix = "conservative mean reversion"
        else:
            suffix = "trend momentum"

        return f"{prompt} {suffix}"
