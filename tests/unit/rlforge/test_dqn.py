"""Unit tests for DQNTrainer."""

import numpy as np
import pytest
import torch

from rlforge.algorithms.dqn.trainer import DQNTrainer, DQNConfig
from rlforge.envs.base import GymWrapper


class TestDQNConfig:
    def test_defaults(self):
        cfg = DQNConfig()
        assert cfg.buffer_size == 100_000
        assert cfg.batch_size == 64
        assert cfg.target_update_freq == 1000
        assert cfg.epsilon_decay_steps == 50_000
        assert cfg.hidden_layers == [256, 256]


class TestDQNTrainer:
    def test_epsilon_decay(self):
        env = GymWrapper("CartPole-v1", seed=42)
        trainer = DQNTrainer(env, config=DQNConfig(epsilon_decay_steps=100), seed=42)
        assert trainer.epsilon == pytest.approx(1.0)
        trainer._total_steps = 50
        assert 0.01 < trainer.epsilon < 1.0
        trainer._total_steps = 200
        assert trainer.epsilon == pytest.approx(0.01)
        env.close()

    def test_q_network_forward(self):
        env = GymWrapper("CartPole-v1", seed=42)
        trainer = DQNTrainer(env, seed=42)
        obs = torch.randn(1, 4)
        q = trainer.q_net(obs)
        assert q.shape == (1, 2)
        env.close()

    def test_dueling_network(self):
        env = GymWrapper("CartPole-v1", seed=42)
        trainer = DQNTrainer(env, config=DQNConfig(dueling=True), seed=42)
        obs = torch.randn(1, 4)
        q = trainer.q_net(obs)
        assert q.shape == (1, 2)
        env.close()

    def test_train_short(self):
        env = GymWrapper("CartPole-v1", seed=42)
        trainer = DQNTrainer(env, config=DQNConfig(
            buffer_size=1000, batch_size=32, epsilon_decay_steps=100,
        ), seed=42)
        result = trainer.train(max_steps=200)
        assert result["total_steps"] == 200
        assert result["episodes"] > 0
        env.close()

    def test_td_target_computation(self):
        env = GymWrapper("CartPole-v1", seed=42)
        trainer = DQNTrainer(env, config=DQNConfig(buffer_size=1000, batch_size=4), seed=42)
        obs = env.reset()
        for _ in range(50):
            action = env.action_space.sample()
            next_obs, reward, term, trunc, _ = env.step(action)
            from rlforge.types.transition import Transition
            trainer.buffer.push(Transition(
                obs=obs, action=action, reward=reward, next_obs=next_obs,
                terminated=term, truncated=trunc,
            ))
            obs = next_obs if not (term or trunc) else env.reset()
        loss = trainer._update()
        assert isinstance(loss, float)
        assert np.isfinite(loss)
        env.close()

    def test_epsilon_explore(self):
        env = GymWrapper("CartPole-v1", seed=42)
        trainer = DQNTrainer(env, config=DQNConfig(epsilon_decay_steps=10, epsilon_start=1.0, epsilon_end=1.0), seed=42)
        obs = env.reset()
        action = trainer._select_action(obs)
        assert isinstance(action, (int, np.integer))
        env.close()

    def test_initial_episode_count(self):
        env = GymWrapper("CartPole-v1", seed=42)
        trainer = DQNTrainer(env, seed=42)
        assert trainer._episodes == 0
        env.close()

    def test_hard_target_update_copies_weights(self):
        env = GymWrapper("CartPole-v1", seed=42)
        trainer = DQNTrainer(env, config=DQNConfig(
            target_update_type="hard", target_update_freq=1,
            buffer_size=100, batch_size=4, epsilon_decay_steps=10,
        ), seed=42)
        # Before update, target and online should differ
        online_sd = trainer.q_net.state_dict()
        trainer._total_steps = 1  # trigger hard update at freq=1
        trainer._update_target()
        # After hard update, target should match online
        for (k1, v1), (k2, v2) in zip(
            trainer.q_net.state_dict().items(),
            trainer.target_net.state_dict().items()
        ):
            assert torch.allclose(v1, v2)
        env.close()

    def test_soft_target_update(self):
        env = GymWrapper("CartPole-v1", seed=42)
        trainer = DQNTrainer(env, config=DQNConfig(
            target_update_type="soft", tau=0.5,
            buffer_size=100, batch_size=4, epsilon_decay_steps=10,
        ), seed=42)
        # Modify online weights to differ from target
        with torch.no_grad():
            for p in trainer.q_net.parameters():
                p.fill_(1.0)
        old_target = {k: v.clone() for k, v in trainer.target_net.state_dict().items()}
        trainer._update_target()
        # With tau=0.5 and online=all-ones, target should have moved
        changed = False
        for (k, old_v), (_, new_v) in zip(old_target.items(), trainer.target_net.state_dict().items()):
            if not torch.allclose(old_v, new_v):
                changed = True
        assert changed, "Soft update should change target network weights"
        env.close()

    def test_epsilon_explore_and_exploit(self):
        env = GymWrapper("CartPole-v1", seed=42)
        trainer = DQNTrainer(env, config=DQNConfig(epsilon_decay_steps=10), seed=42)
        # At step 0, epsilon=1.0 → always random
        trainer._total_steps = 0
        actions = set()
        for _ in range(50):
            actions.add(trainer._select_action(env.reset()))
        assert len(actions) > 1  # Should explore both actions
        env.close()
