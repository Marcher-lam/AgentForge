"""Mutation operators."""

from __future__ import annotations

from typing import Any

import numpy as np
from numpy.random import Generator


def gaussian_mutation(genome: Any, rate: float, rng: Generator, sigma: float = 1.0) -> Any:
    """Apply Gaussian noise to each gene with the given probability."""
    if hasattr(genome, "genes") and isinstance(genome.genes, np.ndarray):
        mutant = genome.clone()
        mask = rng.random(len(mutant.genes)) < rate
        mutant.genes[mask] += rng.normal(0, sigma, size=mask.sum())
        if hasattr(mutant, "bounds") and mutant.bounds:
            for i, (lo, hi) in enumerate(mutant.bounds):
                mutant.genes[i] = np.clip(mutant.genes[i], lo, hi)
        return mutant
    return genome.mutate(rate, rng)


def uniform_mutation(genome: Any, rate: float, rng: Generator) -> Any:
    """Replace selected genes with uniform random values within bounds."""
    if hasattr(genome, "genes") and isinstance(genome.genes, np.ndarray) and hasattr(genome, "bounds"):
        mutant = genome.clone()
        mask = rng.random(len(mutant.genes)) < rate
        for i in np.where(mask)[0]:
            lo, hi = mutant.bounds[i] if i < len(mutant.bounds) else (-10, 10)
            mutant.genes[i] = rng.uniform(lo, hi)
        return mutant
    return genome.mutate(rate, rng)


def bitflip_mutation(genome: Any, rate: float, rng: Generator) -> Any:
    """Flip random bits in a binary genome at the given rate."""
    if hasattr(genome, "genes") and isinstance(genome.genes, np.ndarray) and genome.genes.dtype == bool:
        mutant = genome.clone()
        flip = rng.random(len(mutant.genes)) < rate
        mutant.genes[flip] = ~mutant.genes[flip]
        return mutant
    return genome.mutate(rate, rng)


def polynomial_mutation(genome: Any, rate: float, rng: Generator, eta: float = 20.0) -> Any:
    """Apply polynomial mutation with distribution index eta."""
    if hasattr(genome, "genes") and isinstance(genome.genes, np.ndarray) and hasattr(genome, "bounds"):
        mutant = genome.clone()
        for i in range(len(mutant.genes)):
            if rng.random() < rate:
                lo, hi = mutant.bounds[i] if i < len(mutant.bounds) else (-10, 10)
                u = rng.random()
                delta = (2 * u) ** (1.0 / (eta + 1)) - 1 if u < 0.5 else 1 - (2 * (1 - u)) ** (1.0 / (eta + 1))
                mutant.genes[i] = np.clip(mutant.genes[i] + delta * (hi - lo), lo, hi)
        return mutant
    return genome.mutate(rate, rng)
