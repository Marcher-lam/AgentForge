"""Genome Protocol — unified interface for all genome encodings."""

from __future__ import annotations

from typing import Protocol, runtime_checkable, Any
from numpy.random import Generator


@runtime_checkable
class Genome(Protocol):
    """Protocol for all genome types."""

    fitness: float | None

    def crossover(self, other: Any, rng: Generator) -> tuple[Any, Any]: ...
    def mutate(self, rate: float, rng: Generator) -> Any: ...
    def clone(self) -> Any: ...
