"""PPO Trainer with Actor-Critic, GAE, and PPO-Clip."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import torch
import torch.nn as nn

from rlforge.buffers.rollout import RolloutBuffer
from rlforge.envs.base import EnvBase
from rlforge.networks.mlp import ActorCriticNetwork, get_device
from rlforge.training.callbacks import CallbackList, EpisodeInfo, StepInfo, UpdateInfo
from rlforge.training.mixin import TrainerMixin


@dataclass
class PPOConfig:
    learning_rate: float = 3e-4
    n_steps: int = 2048
    batch_size: int = 64
    epochs: int = 10
    gamma: float = 0.99
    gae_lambda: float = 0.95
    clip_range: float = 0.2
    entropy_coef: float = 0.01
    hidden_layers: list[int] = field(default_factory=lambda: [256, 256])


class PPOTrainer(TrainerMixin):
    def __init__(self, env: EnvBase, config: PPOConfig | None = None, seed: int | None = None, continuous: bool = False) -> None:
        self.env = env
        self.config = config or PPOConfig()
        self.continuous = continuous
        self._callbacks = CallbackList()
        self.setup_seed(seed)
        self._device = get_device()

        obs_dim = env.observation_space.shape[0]
        if continuous:
            act_dim = env.action_space.shape[0]
        else:
            act_dim = env.action_space.n

        self.model = ActorCriticNetwork(obs_dim, act_dim, self.config.hidden_layers, continuous=continuous).to(self._device)
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=self.config.learning_rate)
        self.buffer = RolloutBuffer()
        self._total_steps = 0
        self._episodes = 0
        self._updates = 0

    def _select_action(self, obs: np.ndarray) -> tuple[np.ndarray | int, float, float]:
        with torch.no_grad():
            obs_t = torch.FloatTensor(obs).unsqueeze(0).to(self._device)
            action, log_prob, value = self.model.get_action(obs_t)
        return action.squeeze().cpu().numpy(), log_prob.item(), value.item()

    def _collect_rollout(self) -> None:
        self.buffer.clear()
        obs = self.env.reset()

        for _ in range(self.config.n_steps):
            action, log_prob, value = self._select_action(obs)
            if not self.continuous:
                action_env = int(action)
            else:
                action_env = action

            next_obs, reward, terminated, truncated, info = self.env.step(action_env)
            done = terminated or truncated

            self.buffer.push(obs, action, reward, value, log_prob, float(terminated))
            self._total_steps += 1

            obs = next_obs
            if done:
                self._episodes += 1
                self._callbacks.on_step_end(StepInfo(step=self._total_steps, reward=reward))
                obs = self.env.reset()

    def _update(self) -> dict[str, float]:
        advantages, returns = self.buffer.compute_gae(self.config.gamma, self.config.gae_lambda)
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

        obs_arr = np.array(self.buffer.obs, dtype=np.float32)
        actions_arr = np.array(self.buffer.actions)
        old_log_probs = np.array(self.buffer.log_probs, dtype=np.float32)

        total_policy_loss = 0.0
        total_value_loss = 0.0
        total_entropy = 0.0

        for _ in range(self.config.epochs):
            indices = np.arange(len(obs_arr))
            np.random.shuffle(indices)

            for start in range(0, len(obs_arr), self.config.batch_size):
                idx = indices[start:start + self.config.batch_size]

                obs_t = torch.FloatTensor(obs_arr[idx]).to(self._device)
                actions_t = torch.FloatTensor(actions_arr[idx]).to(self._device) if self.continuous else torch.LongTensor(actions_arr[idx]).to(self._device)
                old_lp = torch.FloatTensor(old_log_probs[idx]).to(self._device)
                adv_t = torch.FloatTensor(advantages[idx]).to(self._device)
                ret_t = torch.FloatTensor(returns[idx]).to(self._device)

                if self.continuous:
                    mean, std, values = self.model(obs_t)
                    dist = torch.distributions.Normal(mean, std)
                    log_probs = dist.log_prob(actions_t).sum(-1)
                    entropy = dist.entropy().sum(-1).mean()
                else:
                    probs, values = self.model(obs_t)
                    dist = torch.distributions.Categorical(probs)
                    log_probs = dist.log_prob(actions_t)
                    entropy = dist.entropy().mean()

                ratio = torch.exp(log_probs - old_lp)
                surr1 = ratio * adv_t
                surr2 = torch.clamp(ratio, 1 - self.config.clip_range, 1 + self.config.clip_range) * adv_t
                policy_loss = -torch.min(surr1, surr2).mean()

                value_loss = nn.functional.mse_loss(values.squeeze(), ret_t)

                loss = policy_loss + 0.5 * value_loss - self.config.entropy_coef * entropy

                self.optimizer.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(self.model.parameters(), 0.5)
                self.optimizer.step()

                total_policy_loss += policy_loss.item()
                total_value_loss += value_loss.item()
                total_entropy += entropy.item()

        n_updates = self.config.epochs * max(1, len(obs_arr) // self.config.batch_size)
        self._updates += 1
        return {
            "policy_loss": total_policy_loss / n_updates,
            "value_loss": total_value_loss / n_updates,
            "entropy": total_entropy / n_updates,
        }

    def train(self, max_steps: int = 200_000) -> dict[str, Any]:
        while self._total_steps < max_steps:
            self._collect_rollout()
            loss_dict = self._update()
            self._callbacks.on_update_end(UpdateInfo(update=self._updates, loss_dict=loss_dict))
        return {"total_steps": self._total_steps, "episodes": self._episodes, "updates": self._updates}
