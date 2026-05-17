"""Fitness function protocols and implementations."""

from __future__ import annotations

import asyncio
from typing import Protocol, runtime_checkable, Any, Callable

import numpy as np
from numpy.random import Generator


@runtime_checkable
class FitnessFunction(Protocol):
    """Protocol for fitness evaluation strategies."""
    def evaluate(self, population: list[Any]) -> list[float]: ...


class SimpleFitness:
    """Evaluate each individual with a single objective function."""
    def __init__(self, fn: Callable[[Any], float]) -> None:
        self._fn = fn

    def evaluate(self, population: list[Any]) -> list[float]:
        """Apply the fitness function to every individual in the population."""
        return [self._fn(ind) for ind in population]


class WeightedMultiObjective:
    """Combine multiple objectives with configurable weights (auto-normalized to sum to 1.0)."""
    def __init__(self, objectives: list[Callable[[Any], float]], weights: list[float] | None = None) -> None:
        self._objectives = objectives
        raw_weights = weights or [1.0] * len(objectives)
        total = sum(abs(w) for w in raw_weights)
        self._weights = [w / total for w in raw_weights] if total > 0 else raw_weights

    def evaluate(self, population: list[Any]) -> list[float]:
        """Compute weighted sum of all objectives for each individual."""
        scores = []
        for ind in population:
            total = sum(w * fn(ind) for w, fn in zip(self._weights, self._objectives))
            scores.append(total)
        return scores


class BoundaryClip:
    """Clamp gene values to their declared bounds."""
    def enforce(self, genome: Any) -> Any:
        """Clip all gene values to their bounds in-place."""
        if hasattr(genome, "genes") and hasattr(genome, "bounds") and isinstance(genome.genes, np.ndarray):
            for i, (lo, hi) in enumerate(genome.bounds):
                genome.genes[i] = np.clip(genome.genes[i], lo, hi)
        return genome


class PenaltyFunction:
    """Apply a penalty proportional to constraint violation."""
    def __init__(self, constraint_fn: Callable[[Any], float], penalty_factor: float = 100.0) -> None:
        self._constraint_fn = constraint_fn
        self._penalty_factor = penalty_factor

    def apply(self, genome: Any) -> float:
        """Return the penalty value for the given genome."""
        violation = self._constraint_fn(genome)
        return -self._penalty_factor * violation


class RepairOperator:
    """Wrap a custom repair function for constraint satisfaction."""
    def __init__(self, repair_fn: Callable[[Any], Any]) -> None:
        self._repair_fn = repair_fn

    def repair(self, genome: Any) -> Any:
        """Apply the repair function to return a feasible genome."""
        return self._repair_fn(genome)


class AsyncFitnessWrapper:
    """Wrap a synchronous fitness function for use in async contexts.

    The synchronous ``evaluate`` is offloaded to the default executor via
    ``asyncio.get_event_loop().run_in_executor`` so it does not block the
    event loop.
    """
    def __init__(self, fn: Callable[[list[Any]], list[float]]) -> None:
        self._fn = fn

    async def evaluate(self, population: list[Any]) -> list[float]:
        """Evaluate population in a thread pool to avoid blocking the event loop."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._fn, population)


class BatchFitness:
    """Evaluate all individuals at once via a vectorized batch function.

    Unlike ``SimpleFitness`` which calls ``fn(ind)`` per individual,
    ``BatchFitness`` calls ``fn(population)`` once and expects a list of
    float scores in the same order.
    """
    def __init__(self, batch_fn: Callable[[list[Any]], list[float]]) -> None:
        self._fn = batch_fn

    def evaluate(self, population: list[Any]) -> list[float]:
        """Evaluate the entire population in a single batch call."""
        return self._fn(population)
