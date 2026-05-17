"""Unit tests for PPOTrainer."""

import numpy as np
import pytest
import torch

from rlforge.algorithms.ppo.trainer import PPOTrainer, PPOConfig
from rlforge.envs.base import GymWrapper


class TestPPOConfig:
    def test_defaults(self):
        cfg = PPOConfig()
        assert cfg.n_steps == 2048
        assert cfg.batch_size == 64
        assert cfg.epochs == 10
        assert cfg.hidden_layers == [256, 256]


class TestPPOTrainer:
    def test_actor_critic_forward(self):
        env = GymWrapper("CartPole-v1", seed=42)
        trainer = PPOTrainer(env, seed=42)
        obs = torch.randn(1, 4)
        probs, value = trainer.model(obs)
        assert probs.shape == (1, 2)
        assert value.shape == (1, 1)
        env.close()

    def test_action_selection(self):
        env = GymWrapper("CartPole-v1", seed=42)
        trainer = PPOTrainer(env, seed=42)
        obs = env.reset()
        action, log_prob, value = trainer._select_action(obs)
        assert isinstance(action, (int, np.integer, np.ndarray))
        env.close()

    def test_train_short(self):
        env = GymWrapper("CartPole-v1", seed=42)
        trainer = PPOTrainer(env, config=PPOConfig(
            n_steps=64, batch_size=32, epochs=2,
        ), seed=42)
        result = trainer.train(max_steps=300)
        assert result["total_steps"] >= 300
        assert result["updates"] > 0
        env.close()

    def test_gae_computation(self):
        from rlforge.buffers.rollout import RolloutBuffer
        buf = RolloutBuffer()
        for i in range(10):
            buf.push(obs=np.zeros(4), action=0, reward=float(i), value=float(i) * 0.5, log_prob=-0.1, done=(i == 9))
        adv, ret = buf.compute_gae(gamma=0.99, lam=0.95)
        assert adv.shape == (10,)
        assert ret.shape == (10,)
        # lambda=0 → TD(0) approximation
        adv_td, _ = buf.compute_gae(gamma=0.99, lam=0.0)
        assert adv_td.shape == (10,)

    def test_initial_counters(self):
        env = GymWrapper("CartPole-v1", seed=42)
        trainer = PPOTrainer(env, seed=42)
        assert trainer._total_steps == 0
        assert trainer._episodes == 0
        assert trainer._updates == 0
        env.close()

    def test_continuous_action_space(self):
        env = GymWrapper("Pendulum-v1", seed=42)
        trainer = PPOTrainer(env, continuous=True, seed=42)
        assert trainer.continuous is True
        obs = env.reset()
        action, log_prob, value = trainer._select_action(obs)
        assert isinstance(action, np.ndarray)
        env.close()

    def test_train_returns_metrics(self):
        env = GymWrapper("CartPole-v1", seed=42)
        trainer = PPOTrainer(env, config=PPOConfig(
            n_steps=64, batch_size=32, epochs=2,
        ), seed=42)
        result = trainer.train(max_steps=300)
        assert "total_steps" in result
        assert "updates" in result
        assert result["total_steps"] >= 300
        assert result["updates"] > 0
        env.close()

    def test_collect_rollout_episode_counting(self):
        env = GymWrapper("CartPole-v1", seed=42)
        trainer = PPOTrainer(env, config=PPOConfig(n_steps=64), seed=42)
        trainer._collect_rollout()
        assert trainer._episodes >= 0
        assert trainer._total_steps > 0
        env.close()

    def test_continuous_vs_discrete(self):
        env_d = GymWrapper("CartPole-v1", seed=42)
        trainer_d = PPOTrainer(env_d, continuous=False, seed=42)
        assert trainer_d.continuous is False

        env_c = GymWrapper("Pendulum-v1", seed=42)
        trainer_c = PPOTrainer(env_c, continuous=True, seed=42)
        assert trainer_c.continuous is True
        env_d.close()
        env_c.close()

    def test_update_produces_finite_loss(self):
        env = GymWrapper("CartPole-v1", seed=42)
        trainer = PPOTrainer(env, config=PPOConfig(
            n_steps=64, batch_size=32, epochs=2,
        ), seed=42)
        trainer._collect_rollout()
        result = trainer._update()
        assert np.isfinite(result["policy_loss"])
        assert np.isfinite(result["value_loss"])
        assert np.isfinite(result["entropy"])
        assert result["entropy"] > 0
        env.close()

    def test_advantage_normalization(self):
        env = GymWrapper("CartPole-v1", seed=42)
        trainer = PPOTrainer(env, config=PPOConfig(n_steps=64, batch_size=32, epochs=1), seed=42)
        trainer._collect_rollout()
        # The _update method normalizes advantages internally
        # After update, losses should be finite (not NaN from bad normalization)
        result = trainer._update()
        assert np.isfinite(result["policy_loss"])
        env.close()

    def test_episode_count_increments(self):
        env = GymWrapper("CartPole-v1", seed=42)
        trainer = PPOTrainer(env, config=PPOConfig(
            n_steps=64, batch_size=32, epochs=1,
        ), seed=42)
        initial_episodes = trainer._episodes
        trainer.train(max_steps=500)
        assert trainer._episodes > initial_episodes
        env.close()

    def test_discrete_action_in_rollout(self):
        env = GymWrapper("CartPole-v1", seed=42)
        trainer = PPOTrainer(env, continuous=False, config=PPOConfig(n_steps=64), seed=42)
        trainer._collect_rollout()
        assert trainer._total_steps >= 64
        env.close()

    def test_done_flag_truncation(self):
        env = GymWrapper("CartPole-v1", seed=42)
        trainer = PPOTrainer(env, config=PPOConfig(n_steps=500), seed=42)
        trainer._collect_rollout()
        # CartPole has a 500-step limit, should get truncation
        assert trainer._total_steps > 0
        env.close()

    def test_n_updates_calculation(self):
        env = GymWrapper("CartPole-v1", seed=42)
        trainer = PPOTrainer(env, config=PPOConfig(
            n_steps=64, batch_size=32, epochs=3,
        ), seed=42)
        result = trainer.train(max_steps=300)
        # Multiple updates should have occurred
        assert result["updates"] >= 3
        env.close()
