"""MLP Network implementation with PyTorch backend."""

from __future__ import annotations

from typing import Any

import numpy as np
import torch
import torch.nn as nn


def get_device() -> str:
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


class MLP(nn.Module):
    def __init__(self, input_dim: int, output_dim: int, hidden: list[int] | None = None) -> None:
        super().__init__()
        hidden = hidden or [256, 256]
        layers: list[nn.Module] = []
        prev = input_dim
        for h in hidden:
            layers.extend([nn.Linear(prev, h), nn.ReLU()])
            prev = h
        layers.append(nn.Linear(prev, output_dim))
        self.net = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)

    def get_numpy_weights(self) -> dict[str, np.ndarray]:
        return {k: v.detach().cpu().numpy() for k, v in self.state_dict().items()}

    def set_numpy_weights(self, weights: dict[str, np.ndarray]) -> None:
        self.load_state_dict({k: torch.from_numpy(v) for k, v in weights.items()})


class DuelingQNetwork(nn.Module):
    def __init__(self, input_dim: int, output_dim: int, hidden: list[int] | None = None) -> None:
        super().__init__()
        hidden = hidden or [256, 256]
        self.feature = MLP(input_dim, hidden[-1], hidden[:-1]).net if len(hidden) > 1 else nn.Identity()
        feat_dim = hidden[-1] if hidden else input_dim
        self.value_head = nn.Linear(feat_dim, 1)
        self.advantage_head = nn.Linear(feat_dim, output_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        feat = self.feature(x)
        value = self.value_head(feat)
        advantage = self.advantage_head(feat)
        return value + advantage - advantage.mean(dim=-1, keepdim=True)


class ActorCriticNetwork(nn.Module):
    def __init__(self, input_dim: int, action_dim: int, hidden: list[int] | None = None, continuous: bool = False) -> None:
        super().__init__()
        hidden = hidden or [256, 256]
        self.backbone = MLP(input_dim, hidden[-1], hidden[:-1]).net if len(hidden) > 1 else nn.Identity()
        feat_dim = hidden[-1] if hidden else input_dim
        self.critic = nn.Linear(feat_dim, 1)
        self.continuous = continuous
        if continuous:
            self.actor_mean = nn.Linear(feat_dim, action_dim)
            self.actor_log_std = nn.Parameter(torch.zeros(action_dim))
        else:
            self.actor = nn.Linear(feat_dim, action_dim)

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        feat = self.backbone(x)
        value = self.critic(feat)
        if self.continuous:
            mean = self.actor_mean(feat)
            std = torch.exp(torch.clamp(self.actor_log_std, -5, 2))
            return mean, std, value
        else:
            logits = self.actor(feat)
            probs = torch.softmax(logits, dim=-1)
            return probs, value

    def get_action(self, x: torch.Tensor, deterministic: bool = False) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        if self.continuous:
            mean, std, value = self.forward(x)
            if deterministic:
                action = mean
                log_prob = torch.zeros(mean.shape[0], device=mean.device)
            else:
                dist = torch.distributions.Normal(mean, std)
                action = dist.sample()
                log_prob = dist.log_prob(action).sum(-1)
            return action, log_prob, value
        else:
            probs, value = self.forward(x)
            dist = torch.distributions.Categorical(probs)
            if deterministic:
                action = probs.argmax(dim=-1)
            else:
                action = dist.sample()
            log_prob = dist.log_prob(action)
            return action, log_prob, value
