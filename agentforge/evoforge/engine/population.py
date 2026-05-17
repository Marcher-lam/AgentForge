"""Population management."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from numpy.random import Generator


@dataclass
class Individual:
    """A single individual with genome, fitness, and lineage tracking."""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    genome: Any = None
    generation: int = 0
    parents: list[uuid.UUID] = field(default_factory=list)
    fitness: float | None = None


class Population:
    """Collection of individuals with sorting and statistics."""
    def __init__(self, individuals: list[Individual] | None = None) -> None:
        self.individuals: list[Individual] = individuals or []

    @classmethod
    def random(cls, genome_factory: Any, size: int = 100, rng: Generator | None = None) -> Population:
        """Create a population of random individuals using the given factory."""
        rng = rng or np.random.default_rng()
        individuals = [Individual(genome=genome_factory(rng), generation=0) for _ in range(size)]
        return cls(individuals)

    def sort_by_fitness(self, reverse: bool = True) -> None:
        """Sort individuals by fitness in-place."""
        self.individuals.sort(
            key=lambda x: x.fitness if x.fitness is not None else float("-inf"),
            reverse=reverse,
        )

    def best(self) -> Individual | None:
        """Return the individual with the highest fitness, or None if empty."""
        if not self.individuals:
            return None
        return max(
            self.individuals,
            key=lambda x: x.fitness if x.fitness is not None else float("-inf"),
        )

    def stats(self) -> dict[str, float]:
        """Return summary statistics (best, mean, worst, std, diversity)."""
        fitnesses = [ind.fitness for ind in self.individuals if ind.fitness is not None]
        if not fitnesses:
            return {"best": 0.0, "mean": 0.0, "worst": 0.0, "std": 0.0, "diversity": 0.0}
        arr = np.array(fitnesses)
        return {
            "best": float(arr.max()),
            "mean": float(arr.mean()),
            "worst": float(arr.min()),
            "std": float(arr.std()),
            "diversity": float(arr.std()),
        }

    def __len__(self) -> int:
        return len(self.individuals)
