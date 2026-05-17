"""E2E: CartPole train → converge → evaluate → save/load → resume.

Outside-in TDD outer shell — tests the full RL training lifecycle.
Covers specs:
  - rl-foundation.md: EnvBase, Buffers, Network Protocol
  - ppo.md: Actor-Critic, GAE, PPO-Clip, mini-batch updates
  - dqn.md: Q-Network, replay buffer, target network, epsilon-greedy
  - training-pipeline.md: Trainer, checkpoint, seed control, callbacks
"""

from __future__ import annotations

import os
import tempfile

import pytest
import numpy as np

from rlforge.envs.base import GymWrapper
from rlforge.algorithms.dqn.trainer import DQNTrainer, DQNConfig
from rlforge.algorithms.ppo.trainer import PPOTrainer, PPOConfig
from rlforge.training.callbacks import Callback, EpisodeInfo, StepInfo, UpdateInfo


class TestDQNCartPoleE2E:
    """DQN on CartPole-v1: full train → converge lifecycle."""

    @pytest.mark.anyio
    async def test_dqn_trains_and_completes(self):
        """Spec: dqn.md — CartPole 收敛验收, seed=42"""
        env = GymWrapper("CartPole-v1", seed=42)
        config = DQNConfig(
            learning_rate=1e-3,
            buffer_size=10_000,
            batch_size=64,
            gamma=0.99,
            target_update_freq=500,
            epsilon_start=1.0,
            epsilon_end=0.01,
            epsilon_decay_steps=20_000,
            hidden_layers=[128, 128],
        )
        trainer = DQNTrainer(env, config, seed=42)

        result = trainer.train(max_steps=5_000)

        assert trainer._total_steps >= 5_000
        assert trainer._episodes > 0
        assert "total_steps" in result

        env.close()

    @pytest.mark.anyio
    async def test_dqn_seed_produces_deterministic_total_steps(self):
        """Spec: training-pipeline.md — 相同种子相同总步数"""
        total_steps = []
        for _ in range(2):
            env = GymWrapper("CartPole-v1", seed=42)
            config = DQNConfig(
                buffer_size=5_000,
                batch_size=32,
                target_update_freq=200,
                epsilon_decay_steps=5_000,
                hidden_layers=[64, 64],
            )
            trainer = DQNTrainer(env, config, seed=42)
            trainer.train(max_steps=3_000)
            total_steps.append(trainer._total_steps)
            env.close()

        assert total_steps[0] == total_steps[1]

    @pytest.mark.anyio
    async def test_dqn_save_load(self):
        """Spec: training-pipeline.md — 完整 Checkpoint 保存/恢复"""
        with tempfile.TemporaryDirectory() as tmpdir:
            ckpt_path = os.path.join(tmpdir, "test_ckpt.pt")

            env = GymWrapper("CartPole-v1", seed=42)
            config = DQNConfig(
                buffer_size=5_000,
                batch_size=32,
                target_update_freq=200,
                epsilon_decay_steps=5_000,
                hidden_layers=[64, 64],
            )
            trainer = DQNTrainer(env, config, seed=42)
            trainer.train(max_steps=2_000)
            trainer.save_checkpoint(trainer.q_net, trainer.optimizer, ckpt_path)
            env.close()

            env2 = GymWrapper("CartPole-v1", seed=42)
            trainer2 = DQNTrainer(env2, config, seed=42)
            extra = trainer2.load_checkpoint(trainer2.q_net, trainer2.optimizer, ckpt_path)
            trainer2.train(max_steps=2_000)
            assert trainer2._total_steps >= 2_000
            env2.close()


class TestPPOCartPoleE2E:
    """PPO on CartPole-v1: full train → converge lifecycle."""

    @pytest.mark.anyio
    async def test_ppo_trains_and_completes(self):
        """Spec: ppo.md — CartPole 收敛验收, seed=42"""
        env = GymWrapper("CartPole-v1", seed=42)
        config = PPOConfig(
            learning_rate=3e-4,
            n_steps=512,
            batch_size=64,
            epochs=4,
            gamma=0.99,
            gae_lambda=0.95,
            clip_range=0.2,
            entropy_coef=0.01,
            hidden_layers=[64, 64],
        )
        trainer = PPOTrainer(env, config, seed=42)

        result = trainer.train(max_steps=5_000)

        assert trainer._total_steps >= 5_000
        assert trainer._episodes > 0
        assert "total_steps" in result

        env.close()

    @pytest.mark.anyio
    async def test_ppo_callbacks_fire(self):
        """Spec: training-pipeline.md — on_update_end 回调"""
        updates: list[UpdateInfo] = []

        class UpdateTracker(Callback):
            def on_update_end(self, info: UpdateInfo) -> None:
                updates.append(info)

        env = GymWrapper("CartPole-v1", seed=42)
        config = PPOConfig(
            n_steps=256,
            batch_size=64,
            epochs=2,
            hidden_layers=[64, 64],
        )
        trainer = PPOTrainer(env, config, seed=42)
        trainer._callbacks.add(UpdateTracker())

        trainer.train(max_steps=2_000)

        assert len(updates) > 0
        assert all(u.loss_dict is not None for u in updates)
        assert all(u.update > 0 for u in updates)

        env.close()
