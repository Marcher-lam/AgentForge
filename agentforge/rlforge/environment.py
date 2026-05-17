"""Environment abstraction for RL training."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class StepResult:
    observation: np.ndarray
    reward: float
    done: bool
    info: dict[str, Any] = field(default_factory=dict)


class Environment:
    """Base environment interface — Gym-like step/reset API."""

    def __init__(self, obs_dim: int = 4, act_dim: int = 2, seed: int | None = None) -> None:
        self.obs_dim = obs_dim
        self.act_dim = act_dim
        self.rng = np.random.default_rng(seed)
        self._step_count = 0
        self._max_steps = 200
        self._state: np.ndarray | None = None

    def reset(self) -> np.ndarray:
        self._step_count = 0
        self._state = self.rng.standard_normal(self.obs_dim) * 0.1
        return self._state.copy()

    def step(self, action: int | np.ndarray) -> StepResult:
        if self._state is None:
            raise RuntimeError("Call reset() before step()")

        self._step_count += 1

        # Simple cartpole-like dynamics:
        # state = [position, velocity, angle, angular_velocity]
        # action: 0 = push left, 1 = push right
        force = 1.0 if (action == 1 if isinstance(action, (int, np.integer)) else action[0] > 0) else -1.0
        dt = 0.05
        gravity = 9.8
        mass = 1.0

        s = self._state.copy()
        s[0] += s[1] * dt                           # position
        s[1] += (force + mass * gravity * np.sin(s[2]) * 0.5) * dt  # velocity
        s[2] += s[3] * dt                            # angle
        s[3] += (force * 0.5 - gravity * np.sin(s[2]) * 0.5) * dt   # angular velocity

        # Small noise
        s += self.rng.standard_normal(self.obs_dim) * 0.01

        self._state = s

        # Reward: keep angle small and position centered
        reward = 1.0
        done = False
        if abs(s[2]) > 0.5:  # angle too large
            reward = -1.0
            done = True
        if abs(s[0]) > 2.4:  # position out of bounds
            reward = -1.0
            done = True
        if self._step_count >= self._max_steps:
            done = True
            reward = 10.0  # bonus for surviving

        return StepResult(
            observation=s.copy(),
            reward=reward,
            done=done,
            info={"step": self._step_count},
        )
