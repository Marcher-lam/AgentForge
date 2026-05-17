"""Callback system and statistics collector."""

from __future__ import annotations

from typing import Any, Callable
from dataclasses import dataclass, field


@dataclass
class GenerationStats:
    generation: int
    best_fitness: float
    mean_fitness: float
    std_fitness: float
    diversity: float
    best_individual_id: str
    timestamp: str = ""


class Callback:
    """Base class for evolution callbacks with no-op defaults."""
    def on_generation_end(self, stats: GenerationStats, population: Any) -> None:
        """Called after each generation's evaluation and statistics collection."""
        pass

    def on_evaluation(self, population: Any, fitnesses: list[float]) -> None:
        """Called after fitness evaluation of the population."""
        pass

    def on_termination(self, reason: str, stats: GenerationStats) -> None:
        """Called when the evolution terminates."""
        pass


class StatsCollector(Callback):
    """Collects GenerationStats into a history list."""
    def __init__(self) -> None:
        self.history: list[GenerationStats] = []

    def on_generation_end(self, stats: GenerationStats, population: Any) -> None:
        """Append generation stats to history."""
        self.history.append(stats)


class CompositeCallback(Callback):
    """Dispatches callbacks to multiple listeners."""
    def __init__(self, callbacks: list[Callback] | None = None) -> None:
        self._callbacks = callbacks or []

    def add(self, cb: Callback) -> None:
        """Register an additional callback listener."""
        self._callbacks.append(cb)

    def on_generation_end(self, stats: GenerationStats, population: Any) -> None:
        for cb in self._callbacks:
            cb.on_generation_end(stats, population)

    def on_evaluation(self, population: Any, fitnesses: list[float]) -> None:
        for cb in self._callbacks:
            cb.on_evaluation(population, fitnesses)

    def on_termination(self, reason: str, stats: GenerationStats) -> None:
        for cb in self._callbacks:
            cb.on_termination(reason, stats)
