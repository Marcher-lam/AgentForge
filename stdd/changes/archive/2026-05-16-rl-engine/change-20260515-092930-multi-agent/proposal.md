# Change Proposal: Multi-Agent RL (MADDPG)

> Type: feature | Priority: P1 | Status: Clarified
> Depends on: change-20260515-092930-foundation
> Created: 2026-05-15 | Clarified: 2026-05-15

---

## 1. Intent

实现多 Agent 强化学习协调机制，包括 MADDPG 算法（集中式 Critic + 分布式 Actor）、共享经验池和多 Agent 环境抽象。支持协作和竞争两种交互模式。

## 2. Scope

### In Scope
- **MADDPG**：多 Agent Replay Buffer、集中式 Critic（全局 obs + action）、分布式 Actor（局部 obs）、可配置噪声策略
- **共享经验池**：SharedReplayBuffer、可配置采样策略（均匀/优先级/Agent-aware）、可配置共享粒度（全局/按 Agent 分组）
- **多 Agent 环境**：MultiAgentEnv ABC、自建简单 GridWorld（协作+竞争）、PettingZoo Wrapper
- **训练管线**：独立 MADDPGTrainer + 共享 TrainerMixin、per-Agent + 全局日志、完整 Checkpoint

### Out of Scope
- 其他 MARL 算法（QMIX、MAPPO 等）
- 通信协议（CommNet、TarMAC）
- 参数共享（本期仅独立网络）

## 3. Clarified Decisions (澄清决策)

### Round 1: 核心边界

| # | 问题 | 决策 |
|---|------|------|
| 1 | Agent 数量上限 | **无限制**（用户自负） |
| 2 | 测试环境 | **自建 GridWorld + PettingZoo Wrapper** |
| 3 | 经验池共享粒度 | **可配置**（默认全局共享，可切换按 Agent 分组） |
| 4 | 探索噪声 | **可配置**（默认 Gaussian，可切换 OU Noise） |

### Round 2: 架构约束

| # | 问题 | 决策 |
|---|------|------|
| 5 | 交互模式 | **协作 + 竞争** 都支持 |
| 6 | Critic 信息量 | **全局 obs + 全局 action** |
| 7 | 参数共享 | **本期不实现**，仅独立网络 |
| 8 | 收敛标准 | **收敛趋势**（reward 曲线上升 + 不退化） |

### Round 3: 非功能需求

| # | 问题 | 决策 |
|---|------|------|
| 9 | Trainer 设计 | **独立 MADDPGTrainer** + 共享 TrainerMixin |
| 10 | 采样策略 | **可配置**（均匀/优先级/Agent-aware） |
| 11 | 日志粒度 | **per-Agent + 全局**（每个 Agent 单独 + 全局聚合） |
| 12 | Episode 超时 | **由环境决定**，框架不设上限 |

## 4. Module Design

### 项目结构
```
rlforge/
├── multi_agent/
│   ├── __init__.py
│   ├── env/
│   │   ├── __init__.py
│   │   ├── base.py              # MultiAgentEnv ABC
│   │   ├── gridworld.py         # 自建 GridWorld (协作+竞争)
│   │   └── pettingzoo_wrapper.py # PettingZoo 适配
│   ├── maddpg/
│   │   ├── __init__.py
│   │   ├── actor.py             # 分布式 Actor (局部 obs)
│   │   ├── critic.py            # 集中式 Critic (全局 obs+action)
│   │   ├── noise.py             # Gaussian / OU Noise
│   │   └── trainer.py           # MADDPGTrainer
│   ├── buffers/
│   │   ├── __init__.py
│   │   ├── shared.py            # SharedReplayBuffer
│   │   └── samplers.py          # Uniform / Priority / AgentAware
│   └── configs/
│       ├── __init__.py
│       └── maddpg.py            # MADDPG default config
```

### MultiAgentEnv 接口
```python
class MultiAgentEnv(ABC):
    @property
    @abstractmethod
    def num_agents(self) -> int: ...

    @property
    @abstractmethod
    def agent_ids(self) -> list[str]: ...

    @abstractmethod
    async def reset(self) -> dict[str, ObsType]: ...       # per-agent obs

    @abstractmethod
    async def step(self, actions: dict[str, ActionType]) -> tuple[
        dict[str, ObsType],       # per-agent obs
        dict[str, float],         # per-agent reward
        dict[str, bool],          # per-agent terminated
        dict[str, bool],          # per-agent truncated
        dict[str, dict],          # shared info
    ]: ...
```

### MADDPG 配置
```python
@dataclass
class MADDPGConfig:
    # Network
    actor_hidden: list[int] = field(default_factory=lambda: [256, 256])
    critic_hidden: list[int] = field(default_factory=lambda: [256, 256])
    learning_rate_actor: float = 1e-4
    learning_rate_critic: float = 1e-3
    # Buffer
    buffer_size: int = 100_000
    batch_size: int = 256
    shared_buffer: bool = True            # 全局 vs 按 Agent 分组
    sampler_type: str = "uniform"         # uniform / priority / agent_aware
    # Noise
    noise_type: str = "gaussian"          # gaussian / ou
    noise_sigma: float = 0.2
    # Training
    gamma: float = 0.99
    tau: float = 0.01                     # soft update
    max_steps: int = 500_000
    eval_freq: int = 10
```

## 5. Success Criteria

### 功能验收
- [ ] MADDPG 在 GridWorld 协作环境中 reward 曲线上升
- [ ] MADDPG 在 GridWorld 竞争环境中 reward 曲线上升
- [ ] 共享经验池正确聚合多 Agent 经验，采样策略可切换
- [ ] 集中式 Critic 接收全局 obs + action
- [ ] 自建 GridWorld + PettingZoo Wrapper 都可运行
- [ ] Checkpoint 完整保存/恢复
- [ ] TensorBoard per-Agent + 全局日志正常输出

### 质量验收
- [ ] 核心模块测试覆盖率 ≥ 80%
- [ ] 所有公共接口有完整 type hints
- [ ] MADDPGTrainer 复用 TrainerMixin 基础逻辑
- [ ] structlog 日志包含 agent_id / episode / step 上下文

## 6. Dependencies

- **上游**：change-20260515-092930-foundation
  - EnvBase（环境基类参考）
  - Network Protocol / MLP（网络）
  - TensorBoardLogger（日志）
  - RLForgeError（异常）
- **可与 Single Agent 并行开发**：无直接依赖
