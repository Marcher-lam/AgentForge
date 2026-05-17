"""Termination criteria — combined OR semantics."""

from __future__ import annotations

from typing import Any


class TerminationCriteria:
    """Combined termination criteria with OR semantics."""
    def __init__(
        self,
        max_generations: int | None = None,
        fitness_threshold: float | None = None,
        convergence_generations: int | None = None,
        convergence_threshold: float = 1e-6,
        diversity_threshold: float | None = None,
        diversity_generations: int = 5,
    ) -> None:
        self.max_generations = max_generations
        self.fitness_threshold = fitness_threshold
        self.convergence_generations = convergence_generations
        self.convergence_threshold = convergence_threshold
        self.diversity_threshold = diversity_threshold
        self.diversity_generations = diversity_generations
        self._stagnation_count = 0
        self._prev_best: float | None = None
        self._low_diversity_count = 0

    def should_terminate(self, generation: int, best_fitness: float | None, diversity: float | None = None) -> tuple[bool, str]:
        """Check whether any termination criterion has been met."""
        if self.max_generations is not None and generation >= self.max_generations:
            return True, "MAX_GENERATIONS"
        if self.fitness_threshold is not None and best_fitness is not None and best_fitness >= self.fitness_threshold:
            return True, "FITNESS_THRESHOLD"
        if self._check_convergence(best_fitness):
            return True, "CONVERGENCE"
        if self._check_diversity(diversity):
            return True, "LOW_DIVERSITY"
        return False, ""

    def _check_convergence(self, best_fitness: float | None) -> bool:
        if self.convergence_generations is None or best_fitness is None:
            if best_fitness is not None:
                self._prev_best = best_fitness
            return False
        if self._prev_best is not None and abs(best_fitness - self._prev_best) < self.convergence_threshold:
            self._stagnation_count += 1
        else:
            self._stagnation_count = 0
        self._prev_best = best_fitness
        return self._stagnation_count >= self.convergence_generations

    def _check_diversity(self, diversity: float | None) -> bool:
        """Return True if diversity has been below threshold for N consecutive generations."""
        if self.diversity_threshold is None or diversity is None:
            if diversity is not None:
                pass  # track but don't terminate
            return False
        if diversity < self.diversity_threshold:
            self._low_diversity_count += 1
        else:
            self._low_diversity_count = 0
        return self._low_diversity_count >= self.diversity_generations
