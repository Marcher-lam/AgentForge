"""DQN algorithm — Q-learning with replay buffer and target network (NumPy only)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np

from agentforge.rlforge.buffer import ReplayBuffer
from agentforge.rlforge.environment import Environment, StepResult
from agentforge.rlforge.trainer import StepMetric


@dataclass
class DQNConfig:
    obs_dim: int = 4
    act_dim: int = 2
    hidden: int = 64
    lr: float = 0.001
    gamma: float = 0.99
    epsilon_start: float = 1.0
    epsilon_end: float = 0.01
    epsilon_decay: int = 50000
    buffer_size: int = 10000
    batch_size: int = 64
    target_update_freq: int = 1000
    total_steps: int = 200
    seed: int = 42


class DQNNetwork:
    """Q-value network: obs -> Q-values for all actions. NumPy MLP."""

    def __init__(self, obs_dim: int, act_dim: int, hidden: int = 64, lr: float = 0.001, seed: int | None = None) -> None:
        self.obs_dim = obs_dim
        self.act_dim = act_dim
        self.lr = lr
        self.rng = np.random.default_rng(seed)

        # Xavier initialization
        scale1 = np.sqrt(2.0 / (obs_dim + hidden))
        scale2 = np.sqrt(2.0 / (hidden + act_dim))

        self.w1 = self.rng.standard_normal((obs_dim, hidden)) * scale1
        self.b1 = np.zeros(hidden)
        self.w2 = self.rng.standard_normal((hidden, act_dim)) * scale2
        self.b2 = np.zeros(act_dim)

        # Adam optimizer state
        self._m: dict[str, np.ndarray] = {}
        self._v: dict[str, np.ndarray] = {}
        self._t = 0

    def forward(self, obs: np.ndarray) -> np.ndarray:
        """Forward pass: obs -> Q-values (raw, no softmax)."""
        h = obs @ self.w1 + self.b1
        h_act = np.maximum(0, h)  # ReLU
        q_values = h_act @ self.w2 + self.b2
        return q_values

    def forward_with_cache(self, obs: np.ndarray) -> tuple[np.ndarray, dict[str, np.ndarray]]:
        """Forward pass returning cache for backprop."""
        h = obs @ self.w1 + self.b1
        h_act = np.maximum(0, h)
        q_values = h_act @ self.w2 + self.b2
        cache = {"obs": obs, "h": h, "h_act": h_act, "q_values": q_values}
        return q_values, cache

    def select_action(self, obs: np.ndarray, epsilon: float = 0.0) -> int:
        """Epsilon-greedy action selection."""
        if np.random.random() < epsilon:
            return int(np.random.randint(self.act_dim))
        q_values = self.forward(obs)
        return int(np.argmax(q_values))

    def update(self, grads: dict[str, np.ndarray]) -> None:
        """Adam optimizer update."""
        self._t += 1
        beta1, beta2, eps = 0.9, 0.999, 1e-8

        for name, grad in grads.items():
            if name not in self._m:
                self._m[name] = np.zeros_like(grad)
                self._v[name] = np.zeros_like(grad)

            self._m[name] = beta1 * self._m[name] + (1 - beta1) * grad
            self._v[name] = beta2 * self._v[name] + (1 - beta2) * grad ** 2

            m_hat = self._m[name] / (1 - beta1 ** self._t)
            v_hat = self._v[name] / (1 - beta2 ** self._t)

            param = getattr(self, name)
            setattr(self, name, param - self.lr * m_hat / (np.sqrt(v_hat) + eps))

    def get_weights(self) -> dict[str, np.ndarray]:
        return {"w1": self.w1.copy(), "b1": self.b1.copy(), "w2": self.w2.copy(), "b2": self.b2.copy()}

    def set_weights(self, weights: dict[str, np.ndarray]) -> None:
        self.w1 = weights["w1"].copy()
        self.b1 = weights["b1"].copy()
        self.w2 = weights["w2"].copy()
        self.b2 = weights["b2"].copy()


def _compute_dqn_grad(
    network: DQNNetwork,
    obs_batch: np.ndarray,
    actions: np.ndarray,
    td_targets: np.ndarray,
) -> dict[str, np.ndarray]:
    """Compute gradients for Q-network from a batch using MSE loss.

    MSE loss = 0.5 * mean((Q(s,a) - target)^2)
    dloss/dQ = (Q(s,a) - target) for selected actions, 0 otherwise.
    """
    batch_size = obs_batch.shape[0]

    # Forward pass with caching
    h = obs_batch @ network.w1 + network.b1  # (B, hidden)
    h_act = np.maximum(0, h)  # (B, hidden)
    q_values = h_act @ network.w2 + network.b2  # (B, act_dim)

    # Gradient of MSE loss w.r.t. q_values
    dq = np.zeros_like(q_values)  # (B, act_dim)
    for i in range(batch_size):
        dq[i, actions[i]] = q_values[i, actions[i]] - td_targets[i]
    dq /= batch_size

    # Backprop
    dw2 = h_act.T @ dq  # (hidden, act_dim)
    db2 = dq.sum(axis=0)  # (act_dim,)

    dh_act = dq @ network.w2.T  # (B, hidden)
    dh = dh_act * (h > 0).astype(float)  # ReLU derivative

    dw1 = obs_batch.T @ dh  # (obs_dim, hidden)
    db1 = dh.sum(axis=0)  # (hidden,)

    return {"w1": dw1, "b1": db1, "w2": dw2, "b2": db2}


class DQNTrainer:
    """DQN trainer with replay buffer and target network."""

    def __init__(self, config: DQNConfig | None = None) -> None:
        self.config = config or DQNConfig()
        self.rng = np.random.default_rng(self.config.seed)

        self.env = Environment(
            obs_dim=self.config.obs_dim,
            act_dim=self.config.act_dim,
            seed=self.config.seed,
        )

        self.q_network = DQNNetwork(
            obs_dim=self.config.obs_dim,
            act_dim=self.config.act_dim,
            hidden=self.config.hidden,
            lr=self.config.lr,
            seed=self.config.seed,
        )

        # Target network (starts as copy of q_network)
        self.target_network = DQNNetwork(
            obs_dim=self.config.obs_dim,
            act_dim=self.config.act_dim,
            hidden=self.config.hidden,
            lr=self.config.lr,
            seed=self.config.seed + 1,
        )
        self.target_network.set_weights(self.q_network.get_weights())

        self.buffer = ReplayBuffer(
            capacity=self.config.buffer_size,
            obs_dim=self.config.obs_dim,
        )

        self.total_steps_done = 0

    def _get_epsilon(self) -> float:
        """Linear epsilon decay."""
        if self.total_steps_done >= self.config.epsilon_decay:
            return self.config.epsilon_end
        ratio = self.total_steps_done / self.config.epsilon_decay
        return self.config.epsilon_start + (self.config.epsilon_end - self.config.epsilon_start) * ratio

    def train(self, callback: Callable[[StepMetric], None] | None = None) -> list[StepMetric]:
        """Run DQN training loop."""
        metrics: list[StepMetric] = []
        obs = self.env.reset()
        episode_reward = 0.0

        for step in range(self.config.total_steps):
            epsilon = self._get_epsilon()
            action = self.q_network.select_action(obs, epsilon)

            result: StepResult = self.env.step(action)
            self.buffer.push(obs, action, result.reward, result.observation, result.done)
            episode_reward += result.reward

            loss = 0.0
            value_estimate = 0.0

            # Learn from replay buffer if enough data
            if len(self.buffer) >= self.config.batch_size:
                batch = self.buffer.sample(self.config.batch_size)

                # Compute TD targets using target network
                next_q = self.target_network.forward(batch.next_state)
                max_next_q = np.max(next_q, axis=1)
                td_targets = batch.reward + self.config.gamma * max_next_q * (1.0 - batch.done.astype(float))

                # Compute loss for display
                current_q = self.q_network.forward(batch.state)
                loss = float(np.mean((current_q[np.arange(len(batch.action)), batch.action] - td_targets) ** 2))

                # Compute and apply gradients
                grads = _compute_dqn_grad(self.q_network, batch.state, batch.action, td_targets)
                self.q_network.update(grads)

                value_estimate = float(np.mean(current_q[np.arange(len(batch.action)), batch.action]))

            # Update target network
            self.total_steps_done += 1
            if self.total_steps_done % self.config.target_update_freq == 0:
                self.target_network.set_weights(self.q_network.get_weights())

            metric = StepMetric(
                step=step + 1,
                reward=result.reward,
                loss=loss,
                episode_reward=episode_reward,
                value_estimate=value_estimate,
            )
            metrics.append(metric)

            if callback:
                callback(metric)

            obs = result.observation

            if result.done:
                episode_reward = 0.0
                obs = self.env.reset()

        return metrics

    def save(self, path: str) -> None:
        """Save trainer state to file."""
        from agentforge.rlforge.checkpoint import save_checkpoint

        save_checkpoint(self, path)

    def load(self, path: str) -> None:
        """Load trainer state from file."""
        from agentforge.rlforge.checkpoint import load_checkpoint

        state = load_checkpoint(path)
        self.q_network.set_weights(state["network"])
        self.target_network.set_weights(state.get("target_network", state["network"]))
        self.total_steps_done = state.get("total_steps", 0)
