"""BinaryGenome — bitstring encoding."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.random import Generator


@dataclass
class BinaryGenome:
    """Bitstring genome with single-point crossover and bit-flip mutation."""
    genes: np.ndarray  # bool array
    fitness: float | None = None

    def crossover(self, other: BinaryGenome, rng: Generator) -> tuple[BinaryGenome, BinaryGenome]:
        """Single-point crossover returning two offspring."""
        point = rng.integers(1, len(self.genes))
        child1 = np.concatenate([self.genes[:point], other.genes[point:]])
        child2 = np.concatenate([other.genes[:point], self.genes[point:]])
        return BinaryGenome(genes=child1), BinaryGenome(genes=child2)

    def mutate(self, rate: float, rng: Generator) -> BinaryGenome:
        """Flip each bit independently with the given rate."""
        genes = self.genes.copy()
        flip = rng.random(len(genes)) < rate
        genes[flip] = ~genes[flip]
        return BinaryGenome(genes=genes)

    def clone(self) -> BinaryGenome:
        """Return an independent copy of this genome."""
        return BinaryGenome(genes=self.genes.copy(), fitness=self.fitness)

    @classmethod
    def random(cls, length: int, rng: Generator | None = None) -> BinaryGenome:
        """Create a random binary genome of the given length."""
        rng = rng or np.random.default_rng()
        return cls(genes=rng.random(length) < 0.5)
