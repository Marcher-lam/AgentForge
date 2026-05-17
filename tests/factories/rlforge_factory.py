"""RL-engine test data factories.

Builders: PPOConfig, DQNConfig, StepInfo, EpisodeInfo, UpdateInfo,
          Transition, GymWrapperEnv.
Scenarios: valid defaults, edge cases, boundary values, training configs.
"""
from __future__ import annotations

from typing import Any

import numpy as np

from rlforge.algorithms.ppo.trainer import PPOConfig
from rlforge.algorithms.dqn.trainer import DQNConfig
from rlforge.training.callbacks import StepInfo, EpisodeInfo, UpdateInfo
from rlforge.types.transition import Transition
from rlforge.envs.base import EnvBase, GymWrapper


# ---------------------------------------------------------------------------
# PPOConfig
# ---------------------------------------------------------------------------
class PPOConfigFactory:
    """Build PPOConfig instances for tests."""

    def __init__(self):
        self._learning_rate: float = 3e-4
        self._n_steps: int = 2048
        self._batch_size: int = 64
        self._epochs: int = 10
        self._gamma: float = 0.99
        self._gae_lambda: float = 0.95
        self._clip_range: float = 0.2
        self._entropy_coef: float = 0.01
        self._hidden_layers: list[int] = [256, 256]

    def with_lr(self, lr: float) -> PPOConfigFactory:
        self._learning_rate = lr
        return self

    def with_n_steps(self, n: int) -> PPOConfigFactory:
        self._n_steps = n
        return self

    def with_batch_size(self, bs: int) -> PPOConfigFactory:
        self._batch_size = bs
        return self

    def with_epochs(self, e: int) -> PPOConfigFactory:
        self._epochs = e
        return self

    def with_gamma(self, g: float) -> PPOConfigFactory:
        self._gamma = g
        return self

    def with_hidden_layers(self, layers: list[int]) -> PPOConfigFactory:
        self._hidden_layers = layers
        return self

    def build(self) -> PPOConfig:
        return PPOConfig(
            learning_rate=self._learning_rate,
            n_steps=self._n_steps,
            batch_size=self._batch_size,
            epochs=self._epochs,
            gamma=self._gamma,
            gae_lambda=self._gae_lambda,
            clip_range=self._clip_range,
            entropy_coef=self._entropy_coef,
            hidden_layers=self._hidden_layers,
        )

    @classmethod
    def create(cls, **kwargs) -> PPOConfig:
        f = cls()
        mapping = {
            "learning_rate": f.with_lr, "n_steps": f.with_n_steps,
            "batch_size": f.with_batch_size, "epochs": f.with_epochs,
            "gamma": f.with_gamma, "hidden_layers": f.with_hidden_layers,
        }
        for k, v in kwargs.items():
            if k in mapping:
                mapping[k](v)
        return f.build()

    @classmethod
    def fast(cls) -> PPOConfig:
        """Small config for fast test runs."""
        return cls().with_n_steps(64).with_batch_size(16).with_epochs(2).with_hidden_layers([32]).build()

    @classmethod
    def large(cls) -> PPOConfig:
        """Large config for stress tests."""
        return cls().with_n_steps(4096).with_batch_size(256).with_hidden_layers([512, 512, 512]).build()


# ---------------------------------------------------------------------------
# DQNConfig
# ---------------------------------------------------------------------------
class DQNConfigFactory:
    """Build DQNConfig instances for tests."""

    def __init__(self):
        self._learning_rate: float = 1e-3
        self._buffer_size: int = 100000
        self._batch_size: int = 64
        self._gamma: float = 0.99
        self._target_update_freq: int = 1000
        self._target_update_type: str = "hard"
        self._tau: float = 0.005
        self._epsilon_start: float = 1.0
        self._epsilon_end: float = 0.01
        self._epsilon_decay_steps: int = 50000
        self._dueling: bool = True
        self._hidden_layers: list[int] = [256, 256]

    def with_lr(self, lr: float) -> DQNConfigFactory:
        self._learning_rate = lr
        return self

    def with_buffer_size(self, bs: int) -> DQNConfigFactory:
        self._buffer_size = bs
        return self

    def with_epsilon(self, start: float, end: float, decay: int) -> DQNConfigFactory:
        self._epsilon_start = start
        self._epsilon_end = end
        self._epsilon_decay_steps = decay
        return self

    def with_dueling(self, d: bool) -> DQNConfigFactory:
        self._dueling = d
        return self

    def with_hidden_layers(self, layers: list[int]) -> DQNConfigFactory:
        self._hidden_layers = layers
        return self

    def build(self) -> DQNConfig:
        return DQNConfig(
            learning_rate=self._learning_rate,
            buffer_size=self._buffer_size,
            batch_size=self._batch_size,
            gamma=self._gamma,
            target_update_freq=self._target_update_freq,
            target_update_type=self._target_update_type,
            tau=self._tau,
            epsilon_start=self._epsilon_start,
            epsilon_end=self._epsilon_end,
            epsilon_decay_steps=self._epsilon_decay_steps,
            dueling=self._dueling,
            hidden_layers=self._hidden_layers,
        )

    @classmethod
    def create(cls, **kwargs) -> DQNConfig:
        f = cls()
        mapping = {
            "learning_rate": f.with_lr, "buffer_size": f.with_buffer_size,
            "dueling": f.with_dueling, "hidden_layers": f.with_hidden_layers,
        }
        for k, v in kwargs.items():
            if k in mapping:
                mapping[k](v)
            elif k == "epsilon":
                f.with_epsilon(*v) if isinstance(v, (list, tuple)) else None
        return f.build()

    @classmethod
    def fast(cls) -> DQNConfig:
        """Small config for fast test runs."""
        return (cls()
            .with_buffer_size(1000)
            .with_epsilon(1.0, 0.01, 500)
            .with_hidden_layers([32])
            .build())

    @classmethod
    def no_dueling(cls) -> DQNConfig:
        return cls().with_dueling(False).build()


# ---------------------------------------------------------------------------
# Callback Data
# ---------------------------------------------------------------------------
class StepInfoFactory:
    """Build StepInfo instances for tests."""

    @classmethod
    def create(cls, step: int = 0, reward: float = 1.0, loss: float | None = 0.5,
               epsilon: float | None = None, entropy: float | None = None) -> StepInfo:
        return StepInfo(step=step, reward=reward, loss=loss, epsilon=epsilon, entropy=entropy)

    @classmethod
    def ppo_step(cls, step: int = 100) -> StepInfo:
        return StepInfo(step=step, reward=1.0, loss=0.3, epsilon=None, entropy=1.8)

    @classmethod
    def dqn_step(cls, step: int = 100, epsilon: float = 0.5) -> StepInfo:
        return StepInfo(step=step, reward=1.0, loss=0.4, epsilon=epsilon, entropy=None)

    @classmethod
    def zero_reward(cls, step: int = 0) -> StepInfo:
        return StepInfo(step=step, reward=0.0, loss=None, epsilon=None, entropy=None)

    @classmethod
    def negative_reward(cls, step: int = 50) -> StepInfo:
        return StepInfo(step=step, reward=-1.0, loss=0.8, epsilon=0.3, entropy=0.5)


class EpisodeInfoFactory:
    """Build EpisodeInfo instances for tests."""

    @classmethod
    def create(cls, episode: int = 1, total_reward: float = 100.0, length: int = 100) -> EpisodeInfo:
        return EpisodeInfo(episode=episode, total_reward=total_reward, length=length)

    @classmethod
    def short_episode(cls) -> EpisodeInfo:
        return EpisodeInfo(episode=1, total_reward=10.0, length=10)

    @classmethod
    def long_episode(cls) -> EpisodeInfo:
        return EpisodeInfo(episode=1, total_reward=500.0, length=500)

    @classmethod
    def failed_episode(cls) -> EpisodeInfo:
        return EpisodeInfo(episode=1, total_reward=0.0, length=5)


class UpdateInfoFactory:
    """Build UpdateInfo instances for tests."""

    @classmethod
    def create(cls, update: int = 1, loss_dict: dict[str, float] | None = None) -> UpdateInfo:
        return UpdateInfo(update=update, loss_dict=loss_dict or {"total_loss": 0.5})

    @classmethod
    def ppo_update(cls, update: int = 1) -> UpdateInfo:
        return UpdateInfo(update=update, loss_dict={
            "policy_loss": 0.12, "value_loss": 0.34, "entropy": 1.85, "clip_fraction": 0.08,
        })

    @classmethod
    def dqn_update(cls, update: int = 1) -> UpdateInfo:
        return UpdateInfo(update=update, loss_dict={"td_loss": 0.45})


# ---------------------------------------------------------------------------
# Transition
# ---------------------------------------------------------------------------
class TransitionFactory:
    """Build Transition instances for tests."""

    def __init__(self):
        self._obs_dim: int = 4
        self._action_discrete: bool = True
        self._reward: float = 1.0
        self._terminated: bool = False
        self._truncated: bool = False
        self._rng: np.random.Generator = np.random.default_rng(42)

    def with_obs_dim(self, dim: int) -> TransitionFactory:
        self._obs_dim = dim
        return self

    def with_continuous_action(self) -> TransitionFactory:
        self._action_discrete = False
        return self

    def with_reward(self, r: float) -> TransitionFactory:
        self._reward = r
        return self

    def with_terminated(self) -> TransitionFactory:
        self._terminated = True
        return self

    def with_truncated(self) -> TransitionFactory:
        self._truncated = True
        return self

    def build(self) -> Transition:
        obs = self._rng.standard_normal(self._obs_dim).astype(np.float32)
        next_obs = self._rng.standard_normal(self._obs_dim).astype(np.float32)
        action = self._rng.integers(0, 2) if self._action_discrete else self._rng.standard_normal(2).astype(np.float32)
        return Transition(
            obs=obs, action=action, reward=self._reward,
            next_obs=next_obs, terminated=self._terminated,
            truncated=self._truncated, info={},
        )

    @classmethod
    def create(cls, **kwargs) -> Transition:
        f = cls()
        if "obs_dim" in kwargs:
            f.with_obs_dim(kwargs["obs_dim"])
        if "continuous" in kwargs and kwargs["continuous"]:
            f.with_continuous_action()
        if "reward" in kwargs:
            f.with_reward(kwargs["reward"])
        if "terminated" in kwargs:
            f.with_terminated()
        if "truncated" in kwargs:
            f.with_truncated()
        return f.build()

    @classmethod
    def create_batch(cls, n: int = 100, obs_dim: int = 4) -> list[Transition]:
        return [TransitionFactory().with_obs_dim(obs_dim).build() for _ in range(n)]

    @classmethod
    def terminal(cls) -> Transition:
        return cls().with_terminated().with_reward(0.0).build()


# ---------------------------------------------------------------------------
# Env (GymWrapper factory)
# ---------------------------------------------------------------------------
class EnvFactory:
    """Create environment instances for tests."""

    @classmethod
    def cartpole(cls) -> GymWrapper:
        return GymWrapper("CartPole-v1")

    @classmethod
    def mountaincar(cls) -> GymWrapper:
        return GymWrapper("MountainCar-v0")

    @classmethod
    def acrobot(cls) -> GymWrapper:
        return GymWrapper("Acrobot-v1")

    @classmethod
    def create(cls, env_id: str = "CartPole-v1") -> GymWrapper:
        return GymWrapper(env_id)
