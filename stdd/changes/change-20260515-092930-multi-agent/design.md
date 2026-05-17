# Technical Design: Multi-Agent RL (MADDPG)

> Change: change-20260515-092930-multi-agent | Depends on: change-20260515-092930-foundation

---

## 1. Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│                    Multi-Agent RL                         │
│                                                          │
│  ┌──────────────────┐    ┌──────────────────────────┐   │
│  │ MultiAgentEnv    │    │ MADDPG Architecture      │   │
│  │ ┌──────────────┐ │    │ ┌────────┐ ┌────────┐   │   │
│  │ │ABC           │ │    │ │Actor-0 │ │Actor-1 │   │   │
│  │ ├──────────────┤ │    │ │(local  │ │(local  │   │   │
│  │ │GridWorld     │ │    │ │obs→act)│ │obs→act)│   │   │
│  │ ├──────────────┤ │    │ └────────┘ └────────┘   │   │
│  │ │PettingZoo    │ │    │ ┌────────────────────┐   │   │
│  │ │Wrapper       │ │    │ │Critic-0            │   │   │
│  │ └──────────────┘ │    │ │(global obs+act→Q)  │   │   │
│  └──────────────────┘    │ └────────────────────┘   │   │
│                          └──────────────────────────┘   │
│  ┌──────────────────┐    ┌──────────────────────────┐   │
│  │ Shared Buffer    │    │ MADDPGTrainer            │   │
│  │ ┌──────────────┐ │    │ (centralized training,   │   │
│  │ │Uniform/      │ │    │  distributed execution)   │   │
│  │ │Priority/     │ │    └──────────────────────────┘   │
│  │ │Agent-aware   │ │                                    │
│  │ └──────────────┘ │                                    │
│  └──────────────────┘                                    │
└──────────────────────────────────────────────────────────┘
```

---

## 2. Architecture Decision Records

### ADR-1: 集中式 Critic + 分布式 Actor

**Context**: MADDPG 的核心是集中式训练、分布式执行。

**Decision**: Critic 输入全局 obs + 全局 action；Actor 仅输入本地 obs。

**Rationale**: Critic 利用全局信息稳定训练；Actor 执行时无需其他 Agent 信息。

**Consequences**: Critic 输入维度 = N×obs_dim + N×act_dim，网络较大。

### ADR-2: 无参数共享

**Context**: 多 Agent 是否共享网络参数。

**Decision**: 每个 Agent 独立 Actor + 独立 Critic，不共享参数。

**Rationale**: 支持异构 Agent（不同 obs/action 空间）；行为多样性。

**Consequences**: 参数量 ×N；训练内存开销更大。

### ADR-3: 可配置采样策略

**Context**: 共享经验池的采样方式影响训练效果。

**Decision**: 三种采样器：Uniform（默认）、Priority（TD-error）、Agent-aware（均衡采样每个 Agent）。

**Rationale**: 不同场景下最优采样策略不同；可配置提高灵活性。

**Consequences**: Agent-aware 采样需额外分组逻辑。

---

## 3. Data Model

```python
@dataclass
class MADDPGConfig:
    actor_hidden: list[int] = field(default_factory=lambda: [256, 256])
    critic_hidden: list[int] = field(default_factory=lambda: [256, 256])
    learning_rate_actor: float = 1e-4
    learning_rate_critic: float = 1e-3
    buffer_size: int = 100_000
    batch_size: int = 256
    shared_buffer: bool = True
    sampler_type: Literal["uniform", "priority", "agent_aware"] = "uniform"
    noise_type: Literal["gaussian", "ou"] = "gaussian"
    noise_sigma: float = 0.2
    gamma: float = 0.99
    tau: float = 0.01
    max_steps: int = 500_000
    eval_freq: int = 10

@dataclass
class MultiAgentTransition:
    obs: dict[str, np.ndarray]        # per-agent obs
    actions: dict[str, np.ndarray]    # per-agent action
    rewards: dict[str, float]         # per-agent reward
    next_obs: dict[str, np.ndarray]
    terminated: dict[str, bool]
    truncated: dict[str, bool]
    info: dict[str, dict]
```

---

## 4. File Structure

```
rlforge/
├── multi_agent/
│   ├── __init__.py
│   ├── env/
│   │   ├── __init__.py
│   │   ├── base.py              # MultiAgentEnv ABC
│   │   ├── gridworld.py         # GridWorld (协作+竞争)
│   │   └── pettingzoo_wrapper.py # PettingZoo ParallelEnv → MultiAgentEnv
│   ├── maddpg/
│   │   ├── __init__.py
│   │   ├── actor.py             # MADDPGActor (local obs → action)
│   │   ├── critic.py            # MADDPGCritic (global obs+action → Q)
│   │   ├── noise.py             # Gaussian / OU Noise
│   │   └── trainer.py           # MADDPGTrainer
│   ├── buffers/
│   │   ├── __init__.py
│   │   ├── shared.py            # MultiAgentReplayBuffer
│   │   └── samplers.py          # Uniform / Priority / AgentAware
│   └── configs/
│       ├── __init__.py
│       └── maddpg.py            # MADDPGConfig
```

---

## 5. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| MADDPG 收敛困难 | Medium | High | GridWorld 简单场景验证 + 超参调优 |
| 共享 Buffer 采样不均衡 | Medium | Medium | Agent-aware 采样器保证均衡 |
| OU 噪声参数敏感 | Medium | Low | Gaussian 为默认，OU 为可选项 |
| 多进程环境通信开销 | Low | Medium | PettingZoo 已优化；自建 GridWorld 轻量 |

---

## 6. Testing Strategy

| Layer | Type | Key Scenarios |
|-------|------|---------------|
| MultiAgentEnv | Unit | reset/step dict format, agent_ids |
| GridWorld | Unit | 协作模式完成条件, 竞争模式胜负 |
| PettingZoo Wrapper | Integration | parallel API → MultiAgentEnv 转换 |
| Actor/Critic | Unit | input/output shape, soft update |
| Shared Buffer | Unit | store/sample 3种采样策略 |
| MADDPGTrainer | Integration | GridWorld 收敛 + per-agent log |
| Checkpoint | Integration | save/load multi-agent state |
| **Coverage Target** | | **≥ 80%** |
