"""Policy network — simple 2-layer MLP with softmax output, implemented in NumPy."""

from __future__ import annotations

import numpy as np


class PolicyNetwork:
    """Feed-forward policy network: obs → action probabilities."""

    def __init__(self, obs_dim: int = 4, act_dim: int = 2, hidden: int = 32, lr: float = 0.001, seed: int | None = None) -> None:
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

    def _relu(self, x: np.ndarray) -> np.ndarray:
        return np.maximum(0, x)

    def forward(self, obs: np.ndarray) -> tuple[np.ndarray, dict[str, np.ndarray]]:
        h = obs @ self.w1 + self.b1
        h_act = self._relu(h)
        logits = h_act @ self.w2 + self.b2

        # Softmax
        logits_stable = logits - np.max(logits)
        exp_l = np.exp(logits_stable)
        probs = exp_l / np.sum(exp_l)

        cache = {"obs": obs, "h": h, "h_act": h_act, "logits": logits, "probs": probs}
        return probs, cache

    def select_action(self, obs: np.ndarray) -> tuple[int, dict[str, np.ndarray]]:
        probs, cache = self.forward(obs)
        action = int(self.rng.choice(self.act_dim, p=probs))
        return action, cache

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

    def compute_loss(self, cache: dict[str, np.ndarray], action: int, advantage: float) -> dict[str, np.ndarray]:
        """Compute policy gradient loss and return gradients."""
        probs = cache["probs"]
        h_act = cache["h_act"]
        obs = cache["obs"]

        # Policy gradient: -log_prob * advantage
        log_prob = np.log(probs[action] + 1e-8)
        loss = -log_prob * advantage

        # dlogits
        dlogits = probs.copy()
        dlogits[action] -= 1.0
        dlogits *= advantage

        # Backprop
        dw2 = h_act.reshape(-1, 1) @ dlogits.reshape(1, -1)
        db2 = dlogits

        dh_act = dlogits @ self.w2.T
        dh = dh_act * (cache["h"] > 0).astype(float)

        dw1 = obs.reshape(-1, 1) @ dh.reshape(1, -1)
        db1 = dh

        grads = {"w1": dw1, "b1": db1, "w2": dw2, "b2": db2}
        return grads
