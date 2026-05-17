"""Replay buffer for off-policy algorithms (DQN)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class Transition:
    """A single environment transition."""

    state: np.ndarray
    action: int
    reward: float
    next_state: np.ndarray
    done: bool


class ReplayBuffer:
    """Circular replay buffer with pre-allocated NumPy arrays."""

    def __init__(self, capacity: int = 10000, obs_dim: int = 4) -> None:
        self.capacity = capacity
        self.obs_dim = obs_dim
        self.pos = 0
        self.size = 0

        # Pre-allocate arrays for performance
        self.states = np.zeros((capacity, obs_dim), dtype=np.float64)
        self.actions = np.zeros(capacity, dtype=np.int64)
        self.rewards = np.zeros(capacity, dtype=np.float64)
        self.next_states = np.zeros((capacity, obs_dim), dtype=np.float64)
        self.dones = np.zeros(capacity, dtype=np.bool_)

    def push(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: bool,
    ) -> None:
        """Add a transition to the buffer."""
        idx = self.pos % self.capacity
        self.states[idx] = state
        self.actions[idx] = action
        self.rewards[idx] = reward
        self.next_states[idx] = next_state
        self.dones[idx] = done
        self.pos += 1
        self.size = min(self.pos, self.capacity)

    def sample(self, batch_size: int) -> Transition:
        """Sample a random batch of transitions."""
        indices = np.random.randint(0, self.size, size=batch_size)
        return Transition(
            state=self.states[indices],
            action=self.actions[indices],
            reward=self.rewards[indices],
            next_state=self.next_states[indices],
            done=self.dones[indices],
        )

    def __len__(self) -> int:
        return self.size
