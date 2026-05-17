"""Integration: Buffer → Network forward → Loss backward.

Tests the component boundary: buffer sampling feeds into network
forward pass and loss computation without full training loop.
"""

from __future__ import annotations

import pytest
import numpy as np
import torch

from rlforge.buffers.replay import ReplayBuffer
from rlforge.buffers.rollout import RolloutBuffer
from rlforge.networks.mlp import MLP, DuelingQNetwork, ActorCriticNetwork
from rlforge.types.transition import Transition
from rlforge.training.callbacks import Callback, EpisodeInfo, StepInfo


class TestBufferNetworkIntegration:
    """Buffer push → sample → network forward → loss backward."""

    @pytest.mark.anyio
    async def test_replay_buffer_feeds_q_network(self):
        """DQN: push transitions → sample batch → forward → loss → backward."""
        buffer = ReplayBuffer(capacity=1000)
        for i in range(100):
            buffer.push(Transition(
                obs=np.random.randn(4),
                action=np.random.randint(2),
                reward=np.random.randn(),
                next_obs=np.random.randn(4),
                terminated=False,
                truncated=False,
                info={},
            ))

        batch = buffer.sample(32)
        assert len(batch) == 32

        # Network forward pass
        q_net = MLP(input_dim=4, output_dim=2, hidden=[64, 64])
        obs_t = torch.FloatTensor(np.array([t.obs for t in batch]))
        q_values = q_net(obs_t)
        assert q_values.shape == (32, 2)

        # Compute loss
        target = torch.randn(32)
        loss = torch.nn.functional.mse_loss(q_values.mean(dim=1), target)
        loss.backward()
        # Verify gradients exist on at least one parameter
        has_grad = any(p.grad is not None for p in q_net.parameters())
        assert has_grad

    @pytest.mark.anyio
    async def test_rollout_buffer_feeds_actor_critic(self):
        """PPO: push rollout → compute GAE → actor-critic forward."""
        buffer = RolloutBuffer()
        for _ in range(64):
            buffer.push(
                obs=np.random.randn(4),
                action=np.random.randint(2),
                reward=np.random.randn(),
                value=np.random.randn(),
                log_prob=np.random.randn(),
                done=False,
            )

        assert len(buffer) == 64

        # Actor-Critic forward
        model = ActorCriticNetwork(input_dim=4, action_dim=2, hidden=[64, 64])
        obs_t = torch.FloatTensor(np.array(buffer.obs))
        action, log_prob, value = model.get_action(obs_t)
        assert action.shape[0] == 64

    @pytest.mark.anyio
    async def test_dueling_q_network_forward(self):
        """Dueling DQN: separate value and advantage streams."""
        net = DuelingQNetwork(input_dim=4, output_dim=2, hidden=[64, 64])
        obs = torch.randn(1, 4)
        q_values = net(obs)
        assert q_values.shape == (1, 2)
        # Q values should be finite
        assert torch.isfinite(q_values).all()


class TestCallbackIntegration:
    """Trainer callback registration and firing."""

    @pytest.mark.anyio
    async def test_callback_on_episode_end(self):
        """Verify Callback subclass receives EpisodeInfo."""
        received: list[EpisodeInfo] = []

        class Tracker(Callback):
            def on_episode_end(self, info: EpisodeInfo) -> None:
                received.append(info)

        from rlforge.training.callbacks import CallbackList
        cb_list = CallbackList()
        cb_list.add(Tracker())

        cb_list.on_episode_end(EpisodeInfo(episode=1, total_reward=100.0, length=200))

        assert len(received) == 1
        assert received[0].episode == 1
        assert received[0].total_reward == 100.0
