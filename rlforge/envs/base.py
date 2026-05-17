"""EnvBase ABC and Gymnasium wrapper."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import gymnasium
import numpy as np

from rlforge.types.transition import Transition


class EnvBase(ABC):
    @abstractmethod
    def reset(self) -> np.ndarray: ...

    @abstractmethod
    def step(self, action: int | np.ndarray) -> tuple[np.ndarray, float, bool, bool, dict]: ...

    def close(self) -> None:
        pass

    @property
    @abstractmethod
    def observation_space(self) -> Any: ...

    @property
    @abstractmethod
    def action_space(self) -> Any: ...


class GymWrapper(EnvBase):
    def __init__(self, env_id: str, seed: int | None = None, render: bool = False) -> None:
        self._env = gymnasium.make(env_id, render_mode="human" if render else None)
        if seed is not None:
            self._env.reset(seed=seed)
            self._seed = seed
        else:
            self._seed = None

    def reset(self) -> np.ndarray:
        obs, _ = self._env.reset()
        return np.asarray(obs, dtype=np.float32)

    def step(self, action: int | np.ndarray) -> tuple[np.ndarray, float, bool, bool, dict]:
        obs, reward, terminated, truncated, info = self._env.step(action)
        return np.asarray(obs, dtype=np.float32), float(reward), bool(terminated), bool(truncated), info

    def close(self) -> None:
        self._env.close()

    @property
    def observation_space(self) -> Any:
        return self._env.observation_space

    @property
    def action_space(self) -> Any:
        return self._env.action_space
