"""RL trainer — delegates to REINFORCE / PPO / DQN based on algorithm config."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np

from agentforge.rlforge.environment import Environment, StepResult
from agentforge.rlforge.policy import PolicyNetwork


@dataclass
class TrainingConfig:
    algorithm: str = "PPO"      # PPO / REINFORCE / DQN / A2C
    total_steps: int = 200
    gamma: float = 0.99         # discount factor
    gae_lambda: float = 0.95    # GAE lambda
    clip_eps: float = 0.2       # PPO clip range
    entropy_coef: float = 0.01
    value_coef: float = 0.5
    seed: int = 42
    obs_dim: int = 4
    act_dim: int = 2
    hidden: int = 32
    lr: float = 0.001


@dataclass
class StepMetric:
    step: int
    reward: float
    loss: float
    episode_reward: float = 0.0
    value_estimate: float = 0.0


class RLTrainer:
    """Synchronous RL trainer — delegates to algorithm-specific trainer."""

    def __init__(self, config: TrainingConfig | None = None) -> None:
        self.config = config or TrainingConfig()
        self.rng = np.random.default_rng(self.config.seed)
        self.env = Environment(
            obs_dim=self.config.obs_dim,
            act_dim=self.config.act_dim,
            seed=self.config.seed,
        )
        self.policy = PolicyNetwork(
            obs_dim=self.config.obs_dim,
            act_dim=self.config.act_dim,
            hidden=self.config.hidden,
            lr=self.config.lr,
            seed=self.config.seed,
        )
        # Simple value baseline (linear)
        self.value_w = np.zeros(self.config.obs_dim)
        self.value_lr = self.config.lr

    def _compute_returns(self, rewards: list[float], values: list[float], dones: list[bool]) -> list[float]:
        """Compute GAE advantages and returns."""
        advantages = []
        gae = 0.0
        next_value = 0.0

        for t in reversed(range(len(rewards))):
            if dones[t]:
                next_value = 0.0
                gae = 0.0

            delta = rewards[t] + self.config.gamma * next_value - values[t]
            gae = delta + self.config.gamma * self.config.gae_lambda * gae
            advantages.insert(0, gae)
            next_value = values[t]

        returns = [a + v for a, v in zip(advantages, values)]
        return advantages, returns

    def _estimate_value(self, obs: np.ndarray) -> float:
        return float(obs @ self.value_w)

    def _update_value(self, obs: np.ndarray, target: float) -> None:
        pred = self._estimate_value(obs)
        error = pred - target
        self.value_w -= self.value_lr * error * obs

    def _train_reinforce(self, callback: Callable[[StepMetric], None] | None = None) -> list[StepMetric]:
        """REINFORCE (simple policy gradient) training loop."""
        metrics: list[StepMetric] = []
        obs = self.env.reset()
        episode_reward = 0.0
        episode_rewards: list[float] = []
        episode_values: list[float] = []
        episode_obs: list[np.ndarray] = []
        episode_actions: list[int] = []
        episode_dones: list[bool] = []

        for step in range(self.config.total_steps):
            action, cache = self.policy.select_action(obs)
            value = self._estimate_value(obs)

            result: StepResult = self.env.step(action)
            episode_reward += result.reward

            episode_obs.append(obs)
            episode_actions.append(action)
            episode_values.append(value)
            episode_rewards.append(result.reward)
            episode_dones.append(result.done)

            # Compute loss for display
            advantage = result.reward + self.config.gamma * self._estimate_value(result.observation) - value
            grads = self.policy.compute_loss(cache, action, advantage)
            loss = -np.log(cache["probs"][action] + 1e-8) * advantage

            # PPO-style update (simplified: single step)
            self.policy.update(grads)
            self._update_value(obs, result.reward + self.config.gamma * self._estimate_value(result.observation))

            metric = StepMetric(
                step=step + 1,
                reward=result.reward,
                loss=float(loss),
                episode_reward=episode_reward,
                value_estimate=value,
            )
            metrics.append(metric)

            if callback:
                callback(metric)

            obs = result.observation

            if result.done:
                # Episode finished
                episode_rewards.clear()
                episode_values.clear()
                episode_obs.clear()
                episode_actions.clear()
                episode_dones.clear()
                episode_reward = 0.0
                obs = self.env.reset()

        return metrics

    def train(self, callback: Callable[[StepMetric], None] | None = None) -> list[StepMetric]:
        """Run training loop, delegating to the appropriate algorithm trainer."""
        algo = self.config.algorithm.upper()

        if algo == "DQN":
            from agentforge.rlforge.dqn import DQNTrainer, DQNConfig

            dqn_config = DQNConfig(
                obs_dim=self.config.obs_dim,
                act_dim=self.config.act_dim,
                hidden=self.config.hidden,
                lr=self.config.lr,
                gamma=self.config.gamma,
                total_steps=self.config.total_steps,
                seed=self.config.seed,
            )
            trainer = DQNTrainer(dqn_config)
            return trainer.train(callback)

        if algo == "PPO":
            from agentforge.rlforge.ppo import PPOTrainer, PPOConfig

            ppo_config = PPOConfig(
                obs_dim=self.config.obs_dim,
                act_dim=self.config.act_dim,
                hidden=self.config.hidden,
                lr=self.config.lr,
                gamma=self.config.gamma,
                gae_lambda=self.config.gae_lambda,
                clip_eps=self.config.clip_eps,
                entropy_coef=self.config.entropy_coef,
                value_coef=self.config.value_coef,
                total_steps=self.config.total_steps,
                seed=self.config.seed,
            )
            trainer = PPOTrainer(ppo_config)
            return trainer.train(callback)

        # Default: REINFORCE (simple policy gradient)
        return self._train_reinforce(callback)
