"""Replacement strategies — generational and steady-state."""

from __future__ import annotations

from typing import Any


def generational_replacement(
    parents: list[Any],
    offspring: list[Any],
    elite_size: int = 0,
) -> list[Any]:
    """Replace the entire parent population with offspring, preserving elites.

    The top ``elite_size`` parents (assumed already sorted best-first) are
    carried forward unchanged.  The remaining slots are filled from offspring.
    """
    if elite_size <= 0:
        return list(offspring[:len(parents)])

    elites = parents[:elite_size]
    n_remaining = len(parents) - elite_size
    return elites + list(offspring[:n_remaining])


def steady_state_replacement(
    parents: list[Any],
    offspring: list[Any],
    n_replace: int = 1,
) -> list[Any]:
    """Replace the worst *n_replace* parents with the best offspring.

    Both *parents* and *offspring* are assumed sorted best-first (highest
    fitness at index 0).  The worst *n_replace* parents are dropped and the
    best *n_replace* offspring take their place.
    """
    n = min(n_replace, len(offspring), len(parents))
    if n <= 0:
        return list(parents)

    # Keep all but the worst n parents, then append best n offspring
    survivors = list(parents[:-n]) if n < len(parents) else []
    return survivors + list(offspring[:n])
