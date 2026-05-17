"""Crossover operators."""

from __future__ import annotations

from typing import Any

import numpy as np
from numpy.random import Generator


def single_point_crossover(parent1: Any, parent2: Any, rng: Generator) -> tuple[Any, Any]:
    """Perform single-point crossover between two parents."""
    return parent1.crossover(parent2, rng)


def _is_numeric_genome(individual: Any) -> bool:
    return (
        hasattr(individual, "genes")
        and isinstance(individual.genes, np.ndarray)
        and np.issubdtype(individual.genes.dtype, np.number)
    )


def multi_point_crossover(parent1: Any, parent2: Any, rng: Generator, points: int = 2) -> tuple[Any, Any]:
    """Perform multi-point crossover with alternating segments."""
    if not _is_numeric_genome(parent1):
        return parent1.crossover(parent2, rng)
    length = len(parent1.genes)
    pts = sorted(rng.choice(range(1, length), size=min(points, length - 1), replace=False))
    g1, g2 = parent1.genes.copy(), parent2.genes.copy()
    swap = False
    prev = 0
    for pt in pts:
        if swap:
            g1[prev:pt], g2[prev:pt] = parent2.genes[prev:pt].copy(), parent1.genes[prev:pt].copy()
        swap = not swap
        prev = pt
    if swap:
        g1[prev:], g2[prev:] = parent2.genes[prev:].copy(), parent1.genes[prev:].copy()
    child1 = parent1.__class__(genes=g1, bounds=getattr(parent1, "bounds", []))
    child2 = parent2.__class__(genes=g2, bounds=getattr(parent2, "bounds", []))
    return child1, child2


def uniform_crossover(parent1: Any, parent2: Any, rng: Generator) -> tuple[Any, Any]:
    """Perform uniform crossover — each gene swapped independently at 50%."""
    return parent1.crossover(parent2, rng)


def sbx_crossover(parent1: Any, parent2: Any, rng: Generator, eta: float = 2.0) -> tuple[Any, Any]:
    """Simulated Binary Crossover with distribution index eta."""
    if not _is_numeric_genome(parent1):
        return parent1.crossover(parent2, rng)
    g1 = parent1.genes.copy()
    g2 = parent2.genes.copy()
    for i in range(len(g1)):
        if rng.random() < 0.5:
            if abs(g1[i] - g2[i]) > 1e-10:
                u = rng.random()
                if u <= 0.5:
                    beta = (2 * u) ** (1.0 / (eta + 1))
                else:
                    beta = (1.0 / (2 * (1 - u))) ** (1.0 / (eta + 1))
                c1 = 0.5 * ((1 + beta) * g1[i] + (1 - beta) * g2[i])
                c2 = 0.5 * ((1 - beta) * g1[i] + (1 + beta) * g2[i])
                g1[i], g2[i] = c1, c2
    child1 = parent1.__class__(genes=g1, bounds=getattr(parent1, "bounds", []))
    child2 = parent2.__class__(genes=g2, bounds=getattr(parent2, "bounds", []))
    return child1, child2
