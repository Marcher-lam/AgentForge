"""Preset test scenarios for rl-engine factories.

Valid defaults, edge cases, and boundary values for comprehensive testing.
"""
from __future__ import annotations

import numpy as np

from tests.factories.rlforge_factory import (
    PPOConfigFactory,
    DQNConfigFactory,
    StepInfoFactory,
    EpisodeInfoFactory,
    UpdateInfoFactory,
    TransitionFactory,
    EnvFactory,
)


class ConfigScenarios:
    """Preset training config scenarios."""

    @classmethod
    def ppo_default(cls) -> dict:
        return {"name": "ppo_default", "data": PPOConfigFactory.create()}

    @classmethod
    def ppo_fast(cls) -> dict:
        return {"name": "ppo_fast", "data": PPOConfigFactory.fast()}

    @classmethod
    def ppo_large(cls) -> dict:
        return {"name": "ppo_large", "data": PPOConfigFactory.large()}

    @classmethod
    def ppo_high_lr(cls) -> dict:
        return {"name": "ppo_high_lr", "data": PPOConfigFactory.create(learning_rate=0.01)}

    @classmethod
    def ppo_low_gamma(cls) -> dict:
        return {"name": "ppo_low_gamma", "data": PPOConfigFactory.create(gamma=0.5)}

    @classmethod
    def dqn_default(cls) -> dict:
        return {"name": "dqn_default", "data": DQNConfigFactory.create()}

    @classmethod
    def dqn_fast(cls) -> dict:
        return {"name": "dqn_fast", "data": DQNConfigFactory.fast()}

    @classmethod
    def dqn_no_dueling(cls) -> dict:
        return {"name": "dqn_no_dueling", "data": DQNConfigFactory.no_dueling()}

    @classmethod
    def all_scenarios(cls) -> list[dict]:
        return [
            cls.ppo_default(), cls.ppo_fast(), cls.ppo_large(),
            cls.ppo_high_lr(), cls.ppo_low_gamma(),
            cls.dqn_default(), cls.dqn_fast(), cls.dqn_no_dueling(),
        ]


class TransitionScenarios:
    """Preset transition scenarios."""

    @classmethod
    def normal(cls) -> dict:
        return {"name": "normal", "data": TransitionFactory.create()}

    @classmethod
    def terminal(cls) -> dict:
        return {"name": "terminal", "data": TransitionFactory.terminal()}

    @classmethod
    def truncated(cls) -> dict:
        return {"name": "truncated", "data": TransitionFactory.create(truncated=True)}

    @classmethod
    def zero_reward(cls) -> dict:
        return {"name": "zero_reward", "data": TransitionFactory.create(reward=0.0)}

    @classmethod
    def negative_reward(cls) -> dict:
        return {"name": "negative_reward", "data": TransitionFactory.create(reward=-1.0)}

    @classmethod
    def high_dim(cls) -> dict:
        return {"name": "high_dim_64", "data": TransitionFactory.create(obs_dim=64)}

    @classmethod
    def continuous_action(cls) -> dict:
        return {"name": "continuous_action", "data": TransitionFactory.create(continuous=True)}

    @classmethod
    def batch_100(cls) -> dict:
        return {"name": "batch_100", "data": TransitionFactory.create_batch(100)}

    @classmethod
    def all_scenarios(cls) -> list[dict]:
        return [
            cls.normal(), cls.terminal(), cls.truncated(),
            cls.zero_reward(), cls.negative_reward(), cls.high_dim(),
            cls.continuous_action(), cls.batch_100(),
        ]


class CallbackScenarios:
    """Preset callback data scenarios."""

    @classmethod
    def ppo_step(cls) -> dict:
        return {"name": "ppo_step", "data": StepInfoFactory.ppo_step()}

    @classmethod
    def dqn_step(cls) -> dict:
        return {"name": "dqn_step", "data": StepInfoFactory.dqn_step()}

    @classmethod
    def step_zero_reward(cls) -> dict:
        return {"name": "step_zero_reward", "data": StepInfoFactory.zero_reward()}

    @classmethod
    def step_negative(cls) -> dict:
        return {"name": "step_negative", "data": StepInfoFactory.negative_reward()}

    @classmethod
    def episode_short(cls) -> dict:
        return {"name": "episode_short", "data": EpisodeInfoFactory.short_episode()}

    @classmethod
    def episode_long(cls) -> dict:
        return {"name": "episode_long", "data": EpisodeInfoFactory.long_episode()}

    @classmethod
    def episode_failed(cls) -> dict:
        return {"name": "episode_failed", "data": EpisodeInfoFactory.failed_episode()}

    @classmethod
    def ppo_update(cls) -> dict:
        return {"name": "ppo_update", "data": UpdateInfoFactory.ppo_update()}

    @classmethod
    def dqn_update(cls) -> dict:
        return {"name": "dqn_update", "data": UpdateInfoFactory.dqn_update()}

    @classmethod
    def all_scenarios(cls) -> list[dict]:
        return [
            cls.ppo_step(), cls.dqn_step(), cls.step_zero_reward(), cls.step_negative(),
            cls.episode_short(), cls.episode_long(), cls.episode_failed(),
            cls.ppo_update(), cls.dqn_update(),
        ]
