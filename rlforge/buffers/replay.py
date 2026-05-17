"""Thread-safe ReplayBuffer."""

from __future__ import annotations

import random
import threading
from typing import Any

import numpy as np

from rlforge.types.transition import Transition


class ReplayBuffer:
    def __init__(self, capacity: int = 100_000) -> None:
        self._capacity = capacity
        self._buffer: list[Transition] = []
        self._lock = threading.Lock()

    def push(self, transition: Transition) -> None:
        with self._lock:
            if len(self._buffer) >= self._capacity:
                self._buffer.pop(0)
            self._buffer.append(transition)

    def sample(self, batch_size: int) -> list[Transition]:
        with self._lock:
            return random.sample(self._buffer, min(batch_size, len(self._buffer)))

    def __len__(self) -> int:
        return len(self._buffer)


class PrioritizedReplayBuffer:
    def __init__(self, capacity: int = 100_000, alpha: float = 0.6, beta: float = 0.4) -> None:
        self._capacity = capacity
        self._alpha = alpha
        self._beta = beta
        self._buffer: list[Transition] = []
        self._priorities: list[float] = []
        self._lock = threading.Lock()

    def push(self, transition: Transition, priority: float = 1.0) -> None:
        with self._lock:
            if len(self._buffer) >= self._capacity:
                self._buffer.pop(0)
                self._priorities.pop(0)
            self._buffer.append(transition)
            self._priorities.append(priority ** self._alpha)

    def sample(self, batch_size: int) -> tuple[list[Transition], list[float], list[int]]:
        with self._lock:
            total = sum(self._priorities)
            probs = [p / total for p in self._priorities]
            indices = random.choices(range(len(self._buffer)), weights=probs, k=min(batch_size, len(self._buffer)))
            samples = [self._buffer[i] for i in indices]
            weights = [(len(self._buffer) * probs[i]) ** (-self._beta) for i in indices]
            max_w = max(weights) if weights else 1.0
            weights = [w / max_w for w in weights]
            return samples, weights, indices

    def update_priorities(self, indices: list[int], priorities: list[float]) -> None:
        with self._lock:
            for idx, p in zip(indices, priorities):
                if idx < len(self._priorities):
                    self._priorities[idx] = (p + 1e-6) ** self._alpha

    def __len__(self) -> int:
        return len(self._buffer)
