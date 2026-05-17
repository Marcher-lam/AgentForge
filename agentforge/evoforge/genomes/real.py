"""RealGenome — float vector with bounds."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
from numpy.random import Generator


@dataclass
class RealGenome:
    """Float-vector genome with bounded uniform crossover and Gaussian mutation."""
    genes: np.ndarray
    bounds: list[tuple[float, float]] = field(default_factory=list)
    fitness: float | None = None

    def __post_init__(self) -> None:
        if not self.bounds:
            self.bounds = [(-10.0, 10.0)] * len(self.genes)

    def crossover(self, other: RealGenome, rng: Generator) -> tuple[RealGenome, RealGenome]:
        """Uniform crossover — each gene selected from either parent at 50%."""
        mask = rng.random(len(self.genes)) < 0.5
        child1 = np.where(mask, self.genes, other.genes)
        child2 = np.where(mask, other.genes, self.genes)
        return (
            RealGenome(genes=child1.copy(), bounds=list(self.bounds)),
            RealGenome(genes=child2.copy(), bounds=list(self.bounds)),
        )

    def mutate(self, rate: float, rng: Generator) -> RealGenome:
        """Add Gaussian noise to selected genes, clipped to bounds."""
        genes = self.genes.copy()
        mask = rng.random(len(genes)) < rate
        noise = rng.normal(0, 1, size=len(genes))
        genes[mask] += noise[mask]
        for i, (lo, hi) in enumerate(self.bounds):
            genes[i] = np.clip(genes[i], lo, hi)
        return RealGenome(genes=genes, bounds=list(self.bounds))

    def clone(self) -> RealGenome:
        """Return an independent copy of this genome."""
        return RealGenome(genes=self.genes.copy(), bounds=list(self.bounds), fitness=self.fitness)

    @classmethod
    def random(cls, length: int, bounds: list[tuple[float, float]] | None = None, rng: Generator | None = None) -> RealGenome:
        """Create a random real-valued genome within the given bounds."""
        rng = rng or np.random.default_rng()
        bounds = bounds or [(-10.0, 10.0)] * length
        genes = np.array([rng.uniform(lo, hi) for lo, hi in bounds])
        return cls(genes=genes, bounds=bounds)
