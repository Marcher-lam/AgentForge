"""DQN Trainer with Double DQN, Dueling, and configurable target update."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import torch
import torch.nn as nn

from rlforge.buffers.replay import ReplayBuffer
from rlforge.envs.base import EnvBase
from rlforge.networks.mlp import DuelingQNetwork, MLP, get_device
from rlforge.training.callbacks import CallbackList, EpisodeInfo, StepInfo
from rlforge.training.mixin import TrainerMixin


@dataclass
class DQNConfig:
    learning_rate: float = 1e-3
    buffer_size: int = 100_000
    batch_size: int = 64
    gamma: float = 0.99
    target_update_freq: int = 1000
    target_update_type: str = "hard"
    tau: float = 0.005
    epsilon_start: float = 1.0
    epsilon_end: float = 0.01
    epsilon_decay_steps: int = 50_000
    dueling: bool = True
    hidden_layers: list[int] = field(default_factory=lambda: [256, 256])


class DQNTrainer(TrainerMixin):
    def __init__(self, env: EnvBase, config: DQNConfig | None = None, seed: int | None = None) -> None:
        self.env = env
        self.config = config or DQNConfig()
        self._callbacks = CallbackList()
        self.setup_seed(seed)
        self._device = get_device()

        obs_dim = env.observation_space.shape[0]
        act_dim = env.action_space.n

        if self.config.dueling:
            self.q_net = DuelingQNetwork(obs_dim, act_dim, self.config.hidden_layers).to(self._device)
            self.target_net = DuelingQNetwork(obs_dim, act_dim, self.config.hidden_layers).to(self._device)
        else:
            self.q_net = MLP(obs_dim, act_dim, self.config.hidden_layers).to(self._device)
            self.target_net = MLP(obs_dim, act_dim, self.config.hidden_layers).to(self._device)

        self.target_net.load_state_dict(self.q_net.state_dict())
        self.target_net.eval()

        self.optimizer = torch.optim.Adam(self.q_net.parameters(), lr=self.config.learning_rate)
        self.buffer = ReplayBuffer(capacity=self.config.buffer_size)
        self._total_steps = 0
        self._episodes = 0

    @property
    def epsilon(self) -> float:
        cfg = self.config
        if self._total_steps >= cfg.epsilon_decay_steps:
            return cfg.epsilon_end
        progress = self._total_steps / cfg.epsilon_decay_steps
        return cfg.epsilon_start + (cfg.epsilon_end - cfg.epsilon_start) * progress

    def _select_action(self, obs: np.ndarray) -> int:
        if np.random.random() < self.epsilon:
            return self.env.action_space.sample()
        with torch.no_grad():
            obs_t = torch.FloatTensor(obs).unsqueeze(0).to(self._device)
            return int(self.q_net(obs_t).argmax(dim=-1).item())

    def _update(self) -> float | None:
        if len(self.buffer) < self.config.batch_size:
            return None
        batch = self.buffer.sample(self.config.batch_size)
        obs = torch.FloatTensor(np.array([t.obs for t in batch])).to(self._device)
        actions = torch.LongTensor([t.action for t in batch]).to(self._device)
        rewards = torch.FloatTensor([t.reward for t in batch]).to(self._device)
        next_obs = torch.FloatTensor(np.array([t.next_obs for t in batch])).to(self._device)
        dones = torch.FloatTensor([float(t.terminated) for t in batch]).to(self._device)

        q_values = self.q_net(obs).gather(1, actions.unsqueeze(1)).squeeze(1)
        with torch.no_grad():
            next_q = self.target_net(next_obs)
            next_actions = self.q_net(next_obs).argmax(dim=1)
            target_q = next_q.gather(1, next_actions.unsqueeze(1)).squeeze(1)
            target = rewards + self.config.gamma * target_q * (1 - dones)

        loss = nn.functional.mse_loss(q_values, target)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        return loss.item()

    def _update_target(self) -> None:
        if self.config.target_update_type == "hard":
            if self._total_steps % self.config.target_update_freq == 0:
                self.target_net.load_state_dict(self.q_net.state_dict())
        else:
            tau = self.config.tau
            for target_p, online_p in zip(self.target_net.parameters(), self.q_net.parameters()):
                target_p.data.copy_(tau * online_p.data + (1 - tau) * target_p.data)

    def train(self, max_steps: int = 500_000) -> dict[str, Any]:
        obs = self.env.reset()
        episode_reward = 0.0
        episode_len = 0

        for step in range(max_steps):
            self._total_steps += 1
            action = self._select_action(obs)
            next_obs, reward, terminated, truncated, info = self.env.step(action)

            from rlforge.types.transition import Transition
            self.buffer.push(Transition(
                obs=obs, action=action, reward=reward, next_obs=next_obs,
                terminated=terminated, truncated=truncated, info=info,
            ))

            loss = self._update()
            self._update_target()

            episode_reward += reward
            episode_len += 1
            obs = next_obs

            self._callbacks.on_step_end(StepInfo(step=self._total_steps, reward=reward, loss=loss, epsilon=self.epsilon))

            if terminated or truncated:
                self._episodes += 1
                self._callbacks.on_episode_end(EpisodeInfo(
                    episode=self._episodes, total_reward=episode_reward, length=episode_len,
                ))
                obs = self.env.reset()
                episode_reward = 0.0
                episode_len = 0

        return {"total_steps": self._total_steps, "episodes": self._episodes}
