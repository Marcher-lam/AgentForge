"""Selection operators."""

from __future__ import annotations

from typing import Any

import numpy as np
from numpy.random import Generator


def roulette_selection(population: list[Any], n: int, rng: Generator) -> list[Any]:
    """Select n individuals via fitness-proportionate (roulette wheel) selection."""
    fitnesses = np.array([ind.fitness for ind in population], dtype=float)
    fitnesses = fitnesses - fitnesses.min() + 1e-10
    probs = fitnesses / fitnesses.sum()
    indices = rng.choice(len(population), size=n, p=probs)
    return [population[i] for i in indices]


def tournament_selection(population: list[Any], n: int, rng: Generator, k: int = 3) -> list[Any]:
    """Select n individuals via tournament selection with k competitors."""
    selected = []
    for _ in range(n):
        candidates = rng.choice(len(population), size=min(k, len(population)), replace=False)
        best = max(candidates, key=lambda i: population[i].fitness if population[i].fitness is not None else float("-inf"))
        selected.append(population[best])
    return selected


def elite_selection(population: list[Any], n: int, rng: Generator) -> list[Any]:
    """Return the top n individuals by fitness."""
    sorted_pop = sorted(population, key=lambda x: x.fitness if x.fitness is not None else float("-inf"), reverse=True)
    return sorted_pop[:n]


def rank_selection(population: list[Any], n: int, rng: Generator) -> list[Any]:
    """Select n individuals via rank-based selection."""
    sorted_pop = sorted(population, key=lambda x: x.fitness if x.fitness is not None else float("-inf"))
    ranks = np.arange(1, len(sorted_pop) + 1, dtype=float)
    probs = ranks / ranks.sum()
    indices = rng.choice(len(sorted_pop), size=n, p=probs)
    return [sorted_pop[i] for i in indices]
