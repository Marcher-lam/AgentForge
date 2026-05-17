"""Tests for Foundation layer — types, env, buffers, network, callbacks."""

import numpy as np
import pytest
import torch

from rlforge.types.transition import Transition, Episode
from rlforge.envs.base import GymWrapper
from rlforge.buffers.replay import ReplayBuffer, PrioritizedReplayBuffer
from rlforge.buffers.rollout import RolloutBuffer
from rlforge.networks.mlp import MLP, DuelingQNetwork, ActorCriticNetwork, get_device
from rlforge.training.mixin import TrainerMixin
from rlforge.training.callbacks import Callback, CallbackList, StepInfo, EpisodeInfo


class TestTransition:
    def test_create(self):
        t = Transition(obs=np.zeros(4), action=1, reward=1.0, next_obs=np.zeros(4), terminated=False, truncated=False)
        assert t.reward == 1.0
        assert not t.terminated

    def test_episode(self):
        ep = Episode()
        ep.transitions.append(Transition(np.zeros(4), 0, 1.0, np.zeros(4), False, False))
        assert len(ep.transitions) == 1

    def test_episode_length_default(self):
        ep = Episode()
        assert ep.length == 0
        assert ep.total_reward == 0.0


class TestEnvBase:
    def test_gym_wrapper_5tuple(self):
        env = GymWrapper("CartPole-v1", seed=42)
        obs = env.reset()
        assert obs.shape == (4,)
        result = env.step(0)
        assert len(result) == 5
        obs, reward, terminated, truncated, info = result
        assert isinstance(reward, float)
        assert isinstance(terminated, bool)
        env.close()

    def test_seed_reproducibility(self):
        env1 = GymWrapper("CartPole-v1", seed=42)
        env2 = GymWrapper("CartPole-v1", seed=42)
        obs1 = env1.reset()
        obs2 = env2.reset()
        assert np.allclose(obs1, obs2)
        env1.close()
        env2.close()


class TestReplayBuffer:
    def test_push_sample(self):
        buf = ReplayBuffer(capacity=100)
        for i in range(50):
            buf.push(Transition(np.zeros(4), 0, float(i), np.zeros(4), False, False))
        assert len(buf) == 50
        batch = buf.sample(32)
        assert len(batch) == 32

    def test_overflow(self):
        buf = ReplayBuffer(capacity=10)
        for i in range(20):
            buf.push(Transition(np.zeros(4), 0, float(i), np.zeros(4), False, False))
        assert len(buf) == 10
        # Verify oldest were dropped (rewards should be 10..19)
        for t in buf._buffer:
            assert t.reward >= 10.0

    def test_default_capacity(self):
        buf = ReplayBuffer()
        assert buf._capacity == 100_000

    def test_sample_returns_transitions(self):
        buf = ReplayBuffer(capacity=100)
        for i in range(50):
            buf.push(Transition(np.zeros(4), i, float(i), np.zeros(4), False, False))
        batch = buf.sample(10)
        for t in batch:
            assert isinstance(t, Transition)


class TestPrioritizedReplayBuffer:
    def test_push_sample(self):
        buf = PrioritizedReplayBuffer(capacity=100)
        for i in range(50):
            buf.push(Transition(np.zeros(4), 0, float(i), np.zeros(4), False, False), priority=i + 1)
        samples, weights, indices = buf.sample(16)
        assert len(samples) == 16

    def test_default_params(self):
        buf = PrioritizedReplayBuffer()
        assert buf._capacity == 100_000
        assert buf._alpha == 0.6
        assert buf._beta == 0.4

    def test_update_priorities(self):
        buf = PrioritizedReplayBuffer(capacity=100)
        for i in range(20):
            buf.push(Transition(np.zeros(4), 0, float(i), np.zeros(4), False, False), priority=1.0)
        _, _, indices = buf.sample(10)
        buf.update_priorities(indices, [5.0] * len(indices))
        # After update, priorities should be (5.0 + 1e-6) ** alpha
        for idx in indices:
            assert buf._priorities[idx] > 1.0

    def test_weights_are_normalized(self):
        buf = PrioritizedReplayBuffer(capacity=100)
        for i in range(50):
            buf.push(Transition(np.zeros(4), 0, float(i), np.zeros(4), False, False), priority=float(i + 1))
        _, weights, _ = buf.sample(16)
        assert max(weights) == pytest.approx(1.0)

    def test_priority_alpha_power(self):
        buf = PrioritizedReplayBuffer(capacity=100, alpha=0.5)
        buf.push(Transition(np.zeros(4), 0, 0.0, np.zeros(4), False, False), priority=4.0)
        # priority should be stored as 4.0 ** 0.5 = 2.0
        assert len(buf._priorities) == 1
        assert buf._priorities[0] == pytest.approx(2.0)

    def test_fifo_eviction_order(self):
        buf = PrioritizedReplayBuffer(capacity=5)
        for i in range(8):
            buf.push(Transition(np.zeros(4), 0, float(i), np.zeros(4), False, False), priority=1.0)
        assert len(buf) == 5
        # Should keep newest (rewards 3..7)
        for t in buf._buffer:
            assert t.reward >= 3.0

    def test_update_priorities_formula(self):
        buf = PrioritizedReplayBuffer(capacity=100, alpha=0.5)
        for i in range(10):
            buf.push(Transition(np.zeros(4), 0, float(i), np.zeros(4), False, False), priority=1.0)
        _, _, indices = buf.sample(5)
        # Update with priority 9.0 → (9.0 + 1e-6) ** 0.5
        buf.update_priorities(indices, [9.0] * len(indices))
        for idx in indices:
            expected = (9.0 + 1e-6) ** 0.5
            assert buf._priorities[idx] == pytest.approx(expected, rel=1e-4)

    def test_sample_probabilities(self):
        buf = PrioritizedReplayBuffer(capacity=100, alpha=1.0)
        # High priority item should be sampled more often
        for i in range(10):
            buf.push(Transition(np.zeros(4), 0, float(i), np.zeros(4), False, False), priority=1.0)
        buf.push(Transition(np.zeros(4), 0, 99.0, np.zeros(4), False, False), priority=100.0)
        # Sample many times and check high-priority item appears often
        high_count = 0
        for _ in range(100):
            samples, _, _ = buf.sample(5)
            for s in samples:
                if s.reward == 99.0:
                    high_count += 1
        assert high_count > 50  # Should be sampled frequently


class TestRolloutBuffer:
    def test_gae(self):
        buf = RolloutBuffer()
        for i in range(10):
            buf.push(obs=np.zeros(4), action=0, reward=1.0, value=0.5, log_prob=-0.1, done=False)
        adv, ret = buf.compute_gae(gamma=0.99, lam=0.95)
        assert adv.shape == (10,)
        assert ret.shape == (10,)

    def test_gae_td0_known_values(self):
        buf = RolloutBuffer()
        # Single step: r=1, V=0.5, done=False → TD0 = 1 + 0.99*0.5 - 0.5 = 0.995
        buf.push(obs=np.zeros(4), action=0, reward=1.0, value=0.5, log_prob=-0.1, done=True)
        adv, ret = buf.compute_gae(gamma=0.99, lam=0.0)
        assert adv.shape == (1,)
        assert ret.shape == (1,)
        # With lam=0, GAE = delta = r + gamma*0 - V = 1 + 0 - 0.5 = 0.5 (terminal, next_value=0)
        assert adv[0] == pytest.approx(0.5, abs=1e-5)
        # return = advantage + value = 0.5 + 0.5 = 1.0
        assert ret[0] == pytest.approx(1.0, abs=1e-5)

    def test_len(self):
        buf = RolloutBuffer()
        assert len(buf) == 0
        buf.push(obs=np.zeros(4), action=0, reward=1.0, value=0.5, log_prob=-0.1, done=False)
        assert len(buf) == 1


class TestMLP:
    def test_forward_shape(self):
        net = MLP(4, 2)
        x = torch.randn(8, 4)
        y = net(x)
        assert y.shape == (8, 2)

    def test_dueling_shape(self):
        net = DuelingQNetwork(4, 2)
        x = torch.randn(8, 4)
        y = net(x)
        assert y.shape == (8, 2)

    def test_actor_critic_discrete(self):
        net = ActorCriticNetwork(4, 2, continuous=False)
        x = torch.randn(1, 4)
        action, log_prob, value = net.get_action(x)
        assert value.shape == (1, 1)

    def test_weights_roundtrip(self):
        net = MLP(4, 2)
        weights = net.get_numpy_weights()
        new_net = MLP(4, 2)
        new_net.set_numpy_weights(weights)
        for (k1, v1), (k2, v2) in zip(net.state_dict().items(), new_net.state_dict().items()):
            assert torch.allclose(v1, v2)

    def test_get_device_cpu(self):
        d = get_device()
        assert d == "cpu"  # Forced CPU due to MPS issues

    def test_mlp_hidden_layers(self):
        net = MLP(4, 2, hidden=[32, 16])
        x = torch.randn(1, 4)
        y = net(x)
        assert y.shape == (1, 2)

    def test_dueling_value_and_advantage(self):
        net = DuelingQNetwork(4, 2, hidden=[32, 32])
        x = torch.randn(1, 4)
        q = net(x)
        assert torch.isfinite(q).all()

    def test_dueling_feat_dim(self):
        net = DuelingQNetwork(4, 3, hidden=[16, 16])
        # Verify both heads exist with correct dims
        x = torch.randn(2, 4)
        q = net(x)
        assert q.shape == (2, 3)

    def test_actor_critic_continuous(self):
        net = ActorCriticNetwork(4, 2, continuous=True, hidden=[32, 32])
        x = torch.randn(1, 4)
        mean, std, value = net.forward(x)
        assert mean.shape == (1, 2)
        assert std.shape == (2,)
        assert value.shape == (1, 1)
        assert (std > 0).all()
        # std = exp(clamp(log_std, -5, 2)) → bounded in [exp(-5), exp(2)]
        assert (std <= torch.exp(torch.tensor(2.0)) + 0.01).all()

    def test_get_action_continuous(self):
        net = ActorCriticNetwork(4, 2, continuous=True, hidden=[32, 32])
        x = torch.randn(1, 4)
        action, log_prob, value = net.get_action(x)
        assert action.shape == (1, 2)
        assert log_prob.shape == (1,)
        assert value.shape == (1, 1)

    def test_discrete_action_selection(self):
        net = ActorCriticNetwork(4, 3, continuous=False, hidden=[32, 32])
        x = torch.randn(1, 4)
        action, log_prob, value = net.get_action(x)
        assert isinstance(action.item(), (int, float))
        assert 0 <= action.item() < 3

    def test_discrete_softmax_sums_to_one(self):
        net = ActorCriticNetwork(4, 3, continuous=False, hidden=[32, 32])
        x = torch.randn(1, 4)
        probs, value = net.forward(x)
        assert probs.sum().item() == pytest.approx(1.0, abs=1e-5)


class TestCallbacks:
    def test_callback_list(self):
        log: list[str] = []

        class CB(Callback):
            def on_step_end(self, info):
                log.append(f"step:{info.step}")

        cbs = CallbackList([CB()])
        cbs.on_step_end(StepInfo(step=1, reward=0.0))
        assert log == ["step:1"]


class TestTrainerMixin:
    def test_seed_reproducibility(self):
        m1 = TrainerMixin()
        m1.setup_seed(42)
        m2 = TrainerMixin()
        m2.setup_seed(42)
        v1 = torch.randn(10)
        m2.setup_seed(42)
        v2 = torch.randn(10)
        assert torch.allclose(v1, v2)

    def test_seed_none_no_crash(self):
        m = TrainerMixin()
        m.setup_seed(None)  # Should not crash

    def test_device_is_cpu(self):
        m = TrainerMixin()
        device = m.setup_device()
        assert device == "cpu"
        assert m._device == "cpu"

    def test_checkpoint_roundtrip(self, tmp_path):
        net = MLP(4, 2)
        opt = torch.optim.Adam(net.parameters())
        m = TrainerMixin()
        path = str(tmp_path / "test_ckpt.pt")
        m.save_checkpoint(net, opt, path, extra={"step": 100})
        extra = m.load_checkpoint(net, opt, path)
        assert extra["step"] == 100
