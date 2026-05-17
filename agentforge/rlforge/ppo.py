"""PPO algorithm — Proximal Policy Optimization with Actor-Critic (NumPy only)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np

from agentforge.rlforge.environment import Environment, StepResult
from agentforge.rlforge.trainer import StepMetric


@dataclass
class PPOConfig:
    obs_dim: int = 4
    act_dim: int = 2
    hidden: int = 32
    lr: float = 0.001
    gamma: float = 0.99
    gae_lambda: float = 0.95
    clip_eps: float = 0.2
    entropy_coef: float = 0.01
    value_coef: float = 0.5
    rollout_length: int = 128
    ppo_epochs: int = 4
    batch_size: int = 32
    total_steps: int = 200
    seed: int = 42


class ActorCritic:
    """Shared-backbone actor-critic network: obs -> (probs, value)."""

    def __init__(
        self,
        obs_dim: int = 4,
        act_dim: int = 2,
        hidden: int = 32,
        lr: float = 0.001,
        seed: int | None = None,
    ) -> None:
        self.obs_dim = obs_dim
        self.act_dim = act_dim
        self.lr = lr
        self.rng = np.random.default_rng(seed)

        # Shared backbone
        scale1 = np.sqrt(2.0 / (obs_dim + hidden))
        self.w1 = self.rng.standard_normal((obs_dim, hidden)) * scale1
        self.b1 = np.zeros(hidden)

        # Policy head
        scale_pol = np.sqrt(2.0 / (hidden + act_dim))
        self.w_pol = self.rng.standard_normal((hidden, act_dim)) * scale_pol
        self.b_pol = np.zeros(act_dim)

        # Value head
        scale_val = np.sqrt(2.0 / (hidden + 1))
        self.w_val = self.rng.standard_normal((hidden, 1)) * scale_val
        self.b_val = np.zeros(1)

        # Adam optimizer state
        self._m: dict[str, np.ndarray] = {}
        self._v: dict[str, np.ndarray] = {}
        self._t = 0

    def forward(self, obs: np.ndarray) -> tuple[np.ndarray, float]:
        """Forward pass: obs -> (probs, value)."""
        h = obs @ self.w1 + self.b1
        h_act = np.maximum(0, h)

        # Policy head (softmax)
        logits = h_act @ self.w_pol + self.b_pol
        logits_stable = logits - np.max(logits)
        exp_l = np.exp(logits_stable)
        probs = exp_l / np.sum(exp_l)

        # Value head
        value = float((h_act @ self.w_val + self.b_val)[0])

        return probs, value

    def forward_batch(self, obs_batch: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Forward pass for a batch: (B, obs_dim) -> (probs (B, act_dim), values (B,))."""
        h = obs_batch @ self.w1 + self.b1  # (B, hidden)
        h_act = np.maximum(0, h)

        # Policy head
        logits = h_act @ self.w_pol + self.b_pol  # (B, act_dim)
        logits_stable = logits - np.max(logits, axis=1, keepdims=True)
        exp_l = np.exp(logits_stable)
        probs = exp_l / np.sum(exp_l, axis=1, keepdims=True)

        # Value head
        values = (h_act @ self.w_val + self.b_val).squeeze(-1)  # (B,)

        return probs, values

    def evaluate(
        self,
        obs_batch: np.ndarray,
        actions: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray, float]:
        """Evaluate actions for a batch. Returns (log_probs, values, entropy)."""
        probs, values = self.forward_batch(obs_batch)

        # Log probabilities of taken actions
        log_probs = np.log(probs[np.arange(len(actions)), actions] + 1e-8)

        # Entropy of the policy
        entropy = float(-np.sum(probs * np.log(probs + 1e-8)) / len(actions))

        return log_probs, values, entropy

    def select_action(self, obs: np.ndarray) -> tuple[int, float, float]:
        """Select action and return (action, log_prob, value)."""
        probs, value = self.forward(obs)
        action = int(self.rng.choice(self.act_dim, p=probs))
        log_prob = float(np.log(probs[action] + 1e-8))
        return action, log_prob, value

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
        return {
            "w1": self.w1.copy(), "b1": self.b1.copy(),
            "w_pol": self.w_pol.copy(), "b_pol": self.b_pol.copy(),
            "w_val": self.w_val.copy(), "b_val": self.b_val.copy(),
        }

    def set_weights(self, weights: dict[str, np.ndarray]) -> None:
        for key in ["w1", "b1", "w_pol", "b_pol", "w_val", "b_val"]:
            setattr(self, key, weights[key].copy())


def _compute_ppo_grad(
    network: ActorCritic,
    obs_batch: np.ndarray,
    actions: np.ndarray,
    old_log_probs: np.ndarray,
    advantages: np.ndarray,
    returns: np.ndarray,
    clip_eps: float,
    entropy_coef: float,
    value_coef: float,
) -> dict[str, np.ndarray]:
    """Compute PPO gradients for a mini-batch.

    Total loss = policy_loss + value_coef * value_loss - entropy_coef * entropy
    """
    batch_size = obs_batch.shape[0]

    # Forward pass
    h = obs_batch @ network.w1 + network.b1  # (B, hidden)
    h_act = np.maximum(0, h)

    # Policy head
    logits = h_act @ network.w_pol + network.b_pol  # (B, act_dim)
    logits_stable = logits - np.max(logits, axis=1, keepdims=True)
    exp_l = np.exp(logits_stable)
    probs = exp_l / np.sum(exp_l, axis=1, keepdims=True)  # (B, act_dim)
    log_probs = np.log(probs[np.arange(batch_size), actions] + 1e-8)  # (B,)

    # Ratio
    ratio = np.exp(log_probs - old_log_probs)

    # Clipped surrogate objective
    surr1 = ratio * advantages
    surr2 = np.clip(ratio, 1.0 - clip_eps, 1.0 + clip_eps) * advantages
    policy_loss = -np.mean(np.minimum(surr1, surr2))

    # Value loss
    values = (h_act @ network.w_val + network.b_val).squeeze(-1)  # (B,)
    value_loss = np.mean((values - returns) ** 2)

    # Entropy
    entropy = -np.sum(probs * np.log(probs + 1e-8)) / batch_size

    # Total loss scalar (for grad scaling)
    total_loss = policy_loss + value_coef * value_loss - entropy_coef * entropy

    # --- Backprop ---
    # Gradient of total_loss w.r.t. all parameters
    # d_policy_loss/d_logits (for selected actions)
    d_surr1 = advantages
    d_surr2 = advantages * np.clip(ratio, 1.0 - clip_eps, 1.0 + clip_eps)
    # Use the one that gives the minimum (more negative gradient = stronger update)
    use_clipped = surr2 < surr1
    d_ratio = np.where(use_clipped, np.zeros_like(advantages), advantages)

    # d(log_prob) -> d(logits) for cross-entropy style
    d_log_probs = d_ratio  # d(ratio * adv) / d(log_prob) = ratio * adv -> but ratio = exp(logp - old), d_ratio/d_logp = ratio
    d_log_probs = ratio * d_ratio  # chain rule through exp

    # d_log_probs -> d_logits (softmax + log gradient)
    # d(log(p_j))/d(logits_k) = delta_{kj} - p_k
    d_logits = np.zeros_like(probs)
    for i in range(batch_size):
        d_logits[i] = -probs[i] * d_log_probs[i]
        d_logits[i, actions[i]] += d_log_probs[i]  # +1 for the delta term
    d_logits /= batch_size

    # Add entropy gradient: d(-entropy)/d_logits = (log(probs) + 1) * probs
    entropy_grad = probs * (np.log(probs + 1e-8) + 1.0) / batch_size
    d_logits -= entropy_coef * entropy_grad

    # Value loss gradient
    value_errors = 2.0 * (values - returns) / batch_size  # (B,)
    d_w_val_input = value_errors.reshape(-1, 1)  # (B, 1)

    # Combine gradients through shared backbone
    # Policy head grads
    dw_pol = h_act.T @ d_logits  # (hidden, act_dim)
    db_pol = d_logits.sum(axis=0)  # (act_dim,)

    # Value head grads
    dw_val = (h_act * d_w_val_input).sum(axis=0).reshape(-1, 1)  # (hidden, 1)
    db_val = np.array([value_errors.sum()])  # (1,)

    # Backprop to shared backbone
    dh_act_pol = d_logits @ network.w_pol.T  # (B, hidden)
    dh_act_val = d_w_val_input @ network.w_val.T  # (B, hidden)

    dh_act = dh_act_pol + value_coef * dh_act_val
    dh = dh_act * (h > 0).astype(float)  # ReLU derivative

    dw1 = obs_batch.T @ dh  # (obs_dim, hidden)
    db1 = dh.sum(axis=0)  # (hidden,)

    return {
        "w1": dw1, "b1": db1,
        "w_pol": dw_pol, "b_pol": db_pol,
        "w_val": dw_val, "b_val": db_val,
    }


class PPOTrainer:
    """PPO trainer with Actor-Critic, GAE, and clipped surrogate objective."""

    def __init__(self, config: PPOConfig | None = None) -> None:
        self.config = config or PPOConfig()
        self.rng = np.random.default_rng(self.config.seed)

        self.env = Environment(
            obs_dim=self.config.obs_dim,
            act_dim=self.config.act_dim,
            seed=self.config.seed,
        )

        self.model = ActorCritic(
            obs_dim=self.config.obs_dim,
            act_dim=self.config.act_dim,
            hidden=self.config.hidden,
            lr=self.config.lr,
            seed=self.config.seed,
        )

        self.total_steps_done = 0

    def _compute_gae(
        self,
        rewards: list[float],
        values: list[float],
        dones: list[bool],
        last_value: float,
    ) -> tuple[list[float], list[float]]:
        """Compute GAE advantages and returns."""
        advantages = []
        gae = 0.0
        next_value = last_value

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

    def train(self, callback: Callable[[StepMetric], None] | None = None) -> list[StepMetric]:
        """Run PPO training loop."""
        metrics: list[StepMetric] = []
        obs = self.env.reset()
        episode_reward = 0.0
        total_step = 0

        while total_step < self.config.total_steps:
            # --- Collect rollout ---
            rollout_obs = []
            rollout_actions = []
            rollout_log_probs = []
            rollout_rewards = []
            rollout_values = []
            rollout_dones = []

            steps_this_rollout = min(self.config.rollout_length, self.config.total_steps - total_step)

            for _ in range(steps_this_rollout):
                action, log_prob, value = self.model.select_action(obs)
                result: StepResult = self.env.step(action)
                episode_reward += result.reward

                rollout_obs.append(obs.copy())
                rollout_actions.append(action)
                rollout_log_probs.append(log_prob)
                rollout_rewards.append(result.reward)
                rollout_values.append(value)
                rollout_dones.append(result.done)

                obs = result.observation
                total_step += 1

                if result.done:
                    episode_reward = 0.0
                    obs = self.env.reset()

            # Get value of last observation for GAE bootstrap
            if rollout_dones[-1]:
                last_value = 0.0
            else:
                _, last_value = self.model.forward(obs)

            # Compute GAE advantages
            advantages, returns = self._compute_gae(
                rollout_rewards, rollout_values, rollout_dones, last_value
            )

            # Convert to arrays
            obs_arr = np.array(rollout_obs)
            act_arr = np.array(rollout_actions)
            old_log_prob_arr = np.array(rollout_log_probs)
            adv_arr = np.array(advantages)
            ret_arr = np.array(returns)

            # Normalize advantages
            adv_arr = (adv_arr - adv_arr.mean()) / (adv_arr.std() + 1e-8)

            # --- PPO update epochs ---
            for _epoch in range(self.config.ppo_epochs):
                # Mini-batch updates
                indices = np.arange(len(rollout_obs))
                np.random.shuffle(indices)

                for start in range(0, len(indices), self.config.batch_size):
                    end = min(start + self.config.batch_size, len(indices))
                    mb_idx = indices[start:end]

                    grads = _compute_ppo_grad(
                        network=self.model,
                        obs_batch=obs_arr[mb_idx],
                        actions=act_arr[mb_idx],
                        old_log_probs=old_log_prob_arr[mb_idx],
                        advantages=adv_arr[mb_idx],
                        returns=ret_arr[mb_idx],
                        clip_eps=self.config.clip_eps,
                        entropy_coef=self.config.entropy_coef,
                        value_coef=self.config.value_coef,
                    )
                    self.model.update(grads)

            # --- Report metrics ---
            for i in range(steps_this_rollout):
                metric = StepMetric(
                    step=self.total_steps_done + i + 1,
                    reward=rollout_rewards[i],
                    loss=0.0,  # PPO computes loss per mini-batch, not per step
                    episode_reward=0.0,  # tracked per rollout, not per step here
                    value_estimate=rollout_values[i],
                )
                metrics.append(metric)
                if callback:
                    callback(metric)

            self.total_steps_done += steps_this_rollout

        return metrics

    def save(self, path: str) -> None:
        """Save trainer state to file."""
        from agentforge.rlforge.checkpoint import save_checkpoint
        save_checkpoint(self, path)

    def load(self, path: str) -> None:
        """Load trainer state from file."""
        from agentforge.rlforge.checkpoint import load_checkpoint
        state = load_checkpoint(path)
        self.model.set_weights(state["network"])
        self.total_steps_done = state.get("total_steps", 0)
