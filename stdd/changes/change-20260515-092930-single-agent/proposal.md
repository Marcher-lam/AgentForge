# Change Proposal: Single Agent RL (DQN + PPO)

> Type: feature | Priority: P0 | Status: Clarified
> Depends on: change-20260515-092930-foundation
> Created: 2026-05-15 | Clarified: 2026-05-15

---

## 1. Intent

实现两个经典单 Agent RL 算法：DQN（值函数方法）和 PPO（策略梯度方法），均在 CartPole-v1 上达到 score ≥ 475。

## 2. Scope

### In Scope
- **DQN**：Q-Network、Experience Replay、Target Network（硬/软更新可配置）、ε-greedy、Double DQN、Dueling DQN
- **PPO**：Actor-Critic 网络、GAE 计算、PPO-Clip loss、Mini-batch 更新、Entropy bonus、支持离散+连续动作空间
- **训练管线**：独立 Trainer 类、完整 Checkpoint（权重+optimizer+buffer+计数器）、seed 控制、Callback 系统、定期评估+可选渲染
- **网络配置**：默认 2 层 256 单元 MLP，层数和宽度可配置

### Out of Scope
- 其他 RL 算法（SAC、TD3、A2C 等）
- 多 Agent 算法（Change-3）
- 超参数自动搜索

## 3. Clarified Decisions (澄清决策)

### Round 1: 算法边界

| # | 问题 | 决策 |
|---|------|------|
| 1 | Target Network 更新策略 | **可配置**（默认硬更新每 1000 step，可切换软更新 τ=0.005） |
| 2 | PPO epoch 数 | **可配置**（默认 10） |
| 3 | CartPole 收敛标准 | **100 episode 均值 ≥ 475** |
| 4 | DQN 变体 | **Double + Dueling 都包含**，配置项切换 |

### Round 2: 训练管线

| # | 问题 | 决策 |
|---|------|------|
| 5 | Trainer 架构 | **独立 Trainer 类**（DQNTrainer / PPOTrainer，共享 TrainerMixin） |
| 6 | Checkpoint 内容 | **完整 checkpoint**（权重 + optimizer + buffer + 训练计数器） |
| 7 | 动作空间 | **DQN 仅离散，PPO 支持连续+离散** |
| 8 | 网络结构 | **默认 MLP + 可配置**（2 层 256 单元） |

### Round 3: 非功能需求

| # | 问题 | 决策 |
|---|------|------|
| 9 | 回调系统 | **Callback 系统**（on_step_end / on_episode_end / on_update_end） |
| 10 | 日志级别 | **TensorBoard 详细 + 控制台详细** |
| 11 | 评估模式 | **定期评估 + 可选渲染**（如每 10 episode 评估一次） |
| 12 | 收敛预算 | **DQN ≤ 500k steps / PPO ≤ 200k steps** |

## 4. Module Design

### 项目结构
```
rlforge/
├── algorithms/
│   ├── __init__.py
│   ├── dqn/
│   │   ├── __init__.py
│   │   ├── network.py          # Q-Network + Dueling variant
│   │   ├── policy.py           # ε-greedy policy
│   │   └── trainer.py          # DQNTrainer
│   └── ppo/
│       ├── __init__.py
│       ├── network.py          # Actor-Critic
│       ├── policy.py           # Gaussian / Categorical policy
│       └── trainer.py          # PPOTrainer
├── training/
│   ├── __init__.py
│   ├── base.py                 # TrainerMixin (shared logic)
│   ├── callbacks.py            # Callback system
│   ├── checkpoint.py           # Checkpoint save/load
│   └── evaluator.py            # Periodic evaluation + render
└── configs/
    ├── __init__.py
    ├── dqn.py                  # DQN default config
    └── ppo.py                  # PPO default config
```

### Callback 接口
```python
class TrainingCallback(Protocol):
    async def on_step_end(self, step: int, metrics: dict) -> None: ...
    async def on_episode_end(self, episode: int, reward: float) -> None: ...
    async def on_update_end(self, update: int, loss: dict) -> None: ...
```

### DQN 配置
```python
@dataclass
class DQNConfig:
    # Network
    hidden_layers: list[int] = field(default_factory=lambda: [256, 256])
    # Replay
    buffer_size: int = 100_000
    batch_size: int = 64
    learning_rate: float = 1e-3
    # Target Network
    target_update_freq: int = 1000        # 硬更新频率
    target_update_tau: float = 0.005      # 软更新系数
    use_soft_update: bool = False         # 切换硬/软更新
    # Exploration
    epsilon_start: float = 1.0
    epsilon_end: float = 0.01
    epsilon_decay: int = 50_000
    # Variants
    use_double_dqn: bool = True
    use_dueling: bool = True
    # Training
    max_steps: int = 500_000
    eval_freq: int = 10                   # 每 10 episode 评估
```

### PPO 配置
```python
@dataclass
class PPOConfig:
    # Network
    hidden_layers: list[int] = field(default_factory=lambda: [256, 256])
    # Rollout
    n_steps: int = 2048
    batch_size: int = 64
    # Update
    epochs: int = 10                      # 可配置 epoch 数
    learning_rate: float = 3e-4
    # PPO-specific
    clip_range: float = 0.2
    entropy_coef: float = 0.01
    value_coef: float = 0.5
    gamma: float = 0.99
    gae_lambda: float = 0.95
    # Training
    max_steps: int = 200_000
    eval_freq: int = 10
```

## 5. Success Criteria

### 功能验收
- [ ] DQN 在 CartPole-v1 达到 100 episode 均值 ≥ 475（≤ 500k steps）
- [ ] PPO 在 CartPole-v1 达到 100 episode 均值 ≥ 475（≤ 200k steps）
- [ ] Double DQN 和 Dueling DQN 可通过配置开关
- [ ] PPO 同时支持离散（CartPole）和连续（Pendulum）动作空间
- [ ] Checkpoint 完整保存/恢复（权重 + optimizer + buffer + 计数器）
- [ ] seed 控制确保结果可复现（同 seed 同结果）
- [ ] Callback 系统支持 on_step/episode/update 事件注入
- [ ] 定期评估 + 可选 render 正常工作

### 质量验收
- [ ] 核心模块测试覆盖率 ≥ 80%
- [ ] 所有公共接口有完整 type hints
- [ ] DQN 和 PPO Trainer 共享 TrainerMixin 基础逻辑
- [ ] structlog + TensorBoard 日志详细记录训练过程

## 6. Dependencies

- **上游**：change-20260515-092930-foundation
  - EnvBase / VectorEnv（环境）
  - ReplayBuffer / RolloutBuffer（缓冲区）
  - Network Protocol / MLP（网络）
  - TensorBoardLogger（日志）
  - RLForgeError（异常）
