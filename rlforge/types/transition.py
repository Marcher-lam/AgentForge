"""Core types: Transition, Episode, Network Protocol."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable, Any

import numpy as np


@dataclass(frozen=True, slots=True)
class Transition:
    obs: np.ndarray
    action: int | np.ndarray
    reward: float
    next_obs: np.ndarray
    terminated: bool
    truncated: bool
    info: dict = field(default_factory=dict)


@dataclass
class Episode:
    transitions: list[Transition] = field(default_factory=list)
    total_reward: float = 0.0
    length: int = 0
    seed: int | None = None


@runtime_checkable
class Network(Protocol):
    def forward(self, x: np.ndarray) -> np.ndarray: ...
    def get_weights(self) -> dict[str, np.ndarray]: ...
    def set_weights(self, weights: dict[str, np.ndarray]) -> None: ...
    @property
    def trainable(self) -> bool: ...
