# Technical Design: Single-Agent RL (DQN + PPO)

> Change: change-20260515-092930-single-agent | Depends on: change-20260515-092930-foundation

---

## 1. Architecture Overview

```
┌───────────────────────────────────────────────────────────┐
│                    Single-Agent RL                         │
│                                                           │
│  ┌──────────────┐    ┌───────────────┐    ┌────────────┐ │
│  │   DQN        │    │    PPO        │    │  Shared    │ │
│  │ ┌──────────┐ │    │ ┌───────────┐ │    │  Training  │ │
│  │ │Q-Network │ │    │ │ActorCritic│ │    │  Infra     │ │
│  │ │(Dueling) │ │    │ │(shared sep│ │    │            │ │
│  │ └──────────┘ │    │ │ backbone) │ │    │ TrainerMixin│ │
│  │ ┌──────────┐ │    │ └───────────┘ │    │ Callbacks  │ │
│  │ │Double DQN│ │    │ ┌───────────┐ │    │ Checkpoint │ │
│  │ │Target Net│ │    │ │GAE        │ │    │ Eval       │ │
│  │ └──────────┘ │    │ └───────────┘ │    └────────────┘ │
│  │ ┌──────────┐ │    │ ┌───────────┐ │                    │
│  │ │ε-greedy  │ │    │ │PPO-Clip   │ │                    │
│  │ └──────────┘ │    │ │Entropy    │ │                    │
│  │ DQNTrainer  │    │ │Mini-batch │ │                    │
│  └──────────────┘    │ │PPOTrainer │ │                    │
│                      │ └───────────┘ │                    │
│                      └───────────────┘                    │
└───────────────────────────────────────────────────────────┘
```

---

## 2. Architecture Decision Records

### ADR-1: Dueling DQN 为默认架构

**Context**: 标准 DQN 在 action-value 估计上存在过估计问题。

**Decision**: 默认使用 Dueling 架构（Value + Advantage 分支）。

**Rationale**: Dueling 在动作间差异小时更稳定（如 CartPole 的"不做特殊动作"状态）。

**Consequences**: 网络参数略多；需 `advantage - mean(advantage)` 归一化。

### ADR-2: Double DQN + 可配置目标更新

**Context**: 标准 DQN 的目标 Q 值计算存在过估计。

**Decision**: 默认 Double DQN（online 选动作，target 评估价值）。支持 hard（定期复制）和 soft（Polyak 平均）两种更新。

**Rationale**: Double DQN 显著减少过估计；hard 更新简单稳定，soft 更新平滑。

**Consequences**: 需维护 online + target 两套网络。

### ADR-3: PPO Mini-batch 多 epoch 更新

**Context**: PPO 需要在同一批数据上多次更新。

**Decision**: 默认 n_steps=2048, batch_size=64, epochs=10。每次 epoch reshuffle。

**Rationale**: 多 epoch 提高数据利用率；reshuffle 减少 mini-batch 相关性。

**Consequences**: 需仔细控制 clip 防止策略崩溃。

---

## 3. Data Model

```python
@dataclass
class DQNConfig:
    learning_rate: float = 1e-3
    buffer_size: int = 100_000
    batch_size: int = 64
    gamma: float = 0.99
    target_update_freq: int = 1000
    target_update_type: Literal["hard", "soft"] = "hard"
    tau: float = 0.005
    epsilon_start: float = 1.0
    epsilon_end: float = 0.01
    epsilon_decay_steps: int = 50_000
    dueling: bool = True
    hidden_layers: list[int] = field(default_factory=lambda: [256, 256])

@dataclass
class PPOConfig:
    learning_rate: float = 3e-4
    n_steps: int = 2048
    batch_size: int = 64
    epochs: int = 10
    gamma: float = 0.99
    gae_lambda: float = 0.95
    clip_range: float = 0.2
    entropy_coef: float = 0.01
    hidden_layers: list[int] = field(default_factory=lambda: [256, 256])
```

---

## 4. File Structure

```
rlforge/
├── algorithms/
│   ├── __init__.py
│   ├── dqn/
│   │   ├── __init__.py
│   │   ├── network.py        # QNetwork + DuelingQNetwork
│   │   ├── policy.py         # EpsilonGreedyPolicy
│   │   ├── trainer.py        # DQNTrainer
│   │   └── config.py         # DQNConfig
│   └── ppo/
│       ├── __init__.py
│       ├── network.py        # ActorCriticNetwork
│       ├── gae.py            # GAE computation
│       ├── loss.py           # PPO-Clip + entropy + value loss
│       ├── trainer.py        # PPOTrainer
│       └── config.py         # PPOConfig
└── configs/
    └── defaults.py           # Default config values
```

---

## 5. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| DQN CartPole 收敛 >500k steps | Medium | High | Double+Dueling 默认 + 种子调优 |
| PPO 策略崩溃（clip 失效） | Low | High | 监控 KL divergence + entropy；早停 |
| GAE 数值不稳定 | Low | Medium | 归一化 advantage + clip |
| Checkpoint 恢复后 RNG 状态不一致 | Medium | High | 保存 numpy + torch RNG state |

---

## 6. Testing Strategy

| Layer | Type | Key Scenarios |
|-------|------|---------------|
| Q-Network | Unit | forward shape, dueling split |
| EpsilonGreedy | Unit | decay curve, final epsilon |
| DQNTrainer | Unit | single step, target update, gradient flow |
| ActorCritic | Unit | discrete/continuous output shape |
| GAE | Unit | lambda=0→TD(0), lambda=1→MC |
| PPO Loss | Unit | clip range, ratio computation |
| PPOTrainer | Unit | mini-batch update, data flow |
| CartPole Convergence | Integration | DQN ≤500k mean≥475, PPO ≤200k mean≥475 |
| Checkpoint | Integration | save/load/reproduce |
| **Coverage Target** | | **≥ 80%** |
