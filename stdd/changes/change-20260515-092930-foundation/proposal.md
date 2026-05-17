# Change Proposal: RL Foundation Layer

> Type: feature | Priority: P0 | Status: Clarified
> Created: 2026-05-15 | Clarified: 2026-05-15

---

## 1. Intent

实现 RL 引擎的基础层：环境抽象、核心数据结构、经验回放缓冲区、网络抽象和 TensorBoard 日志。所有算法层（DQN/PPO/MADDPG）都依赖此 Change。

## 2. Scope

### In Scope
- **环境抽象**：EnvBase ABC（reset/step/render/close）+ Gymnasium 0.29+ Wrapper + VectorEnv（默认 8 并行，上限 32，multiprocessing）
- **核心数据结构**：Transition、Trajectory、Episode dataclass
- **缓冲区**：ReplayBuffer、PrioritizedReplayBuffer、RolloutBuffer（线程安全，加锁）
- **网络抽象**：Network Protocol 接口（完全抽象，隐藏 PyTorch）、MLP 实现
- **日志**：RLLogger 接口 + TensorBoardLogger 实现（每 step 记录，可配置采样率）
- **设备抽象**：CPU / CUDA / MPS 自动检测
- **基础设施**：分层异常、structlog、pyproject.toml 配置

### Out of Scope
- 具体 RL 算法（Change-2、Change-3）
- 分布式训练
- 模型导出

## 3. Clarified Decisions (澄清决策)

### 技术栈

| 项 | 选型 |
|---|------|
| 语言 | Python 3.12+ |
| 深度学习 | PyTorch ≥ 2.0（通过 Network Protocol 抽象） |
| 环境 API | Gymnasium 0.29+（5-tuple 新 API） |
| 设备 | CPU + CUDA + MPS（全平台） |
| 包名 | rlforge.* |
| 依赖管理 | poetry |
| 日志 | structlog |
| 配置 | pyproject.toml [tool.rlforge] + env |

### 边界决策

| # | 问题 | 决策 |
|---|------|------|
| 1 | Env step() 返回值 | **5-tuple** (obs, reward, terminated, truncated, info) |
| 2 | VectorEnv 并行策略 | **multiprocessing** — 避免 GIL |
| 3 | Buffer 线程安全 | **加锁** — 支持异步采样和训练并发 |
| 4 | TensorBoard 日志粒度 | **每 step 记录** — 可配置采样率 |
| 5 | 网络层封装 | **完全抽象** — 自定义 Network Protocol 隐藏 PyTorch |
| 6 | 异常体系 | **分层异常** — RLForgeError 层次结构 |
| 7 | 配置机制 | **pyproject.toml + env** |
| 8 | 日志方案 | **structlog** — 结构化 JSON |

### 异常层次结构
```
RLForgeError (base)
├── EnvError
│   ├── EnvResetError            # reset 失败
│   ├── EnvStepError             # step 失败
│   └── VectorEnvError           # 并行环境异常
├── BufferError
│   ├── BufferEmptyError         # 采样时空 buffer
│   └── BufferFullError          # buffer 溢出
├── NetworkError
│   ├── NetworkInitError         # 网络初始化失败
│   └── DeviceError              # 设备不可用
└── ConfigError                  # 配置错误
```

### 项目结构
```
rlforge/
├── __init__.py
├── types/
│   ├── __init__.py              # 公共类型导出
│   ├── transition.py            # Transition, Trajectory, Episode
│   └── protocols.py             # Network, Agent, Logger Protocol
├── envs/
│   ├── __init__.py
│   ├── base.py                  # EnvBase ABC
│   ├── gym_wrapper.py           # Gymnasium 适配
│   ├── vector.py                # VectorEnv (multiprocessing)
│   └── errors.py                # EnvError hierarchy
├── buffers/
│   ├── __init__.py
│   ├── replay.py                # ReplayBuffer (线程安全)
│   ├── prioritized.py           # PrioritizedReplayBuffer
│   ├── rollout.py               # RolloutBuffer (PPO 用)
│   └── errors.py                # BufferError hierarchy
├── networks/
│   ├── __init__.py
│   ├── protocol.py              # Network Protocol (抽象接口)
│   ├── mlp.py                   # MLP 实现 (PyTorch backend)
│   └── device.py                # CPU/CUDA/MPS 自动检测
├── logging/
│   ├── __init__.py
│   ├── base.py                  # RLLogger Protocol
│   ├── tensorboard.py           # TensorBoardLogger
│   └── console.py               # ConsoleLogger
├── config.py                    # pyproject.toml + env 配置
└── errors.py                    # RLForgeError base
```

## 4. Success Criteria

### 功能验收
- [ ] EnvBase 兼容 Gymnasium 0.29+ 5-tuple API
- [ ] VectorEnv 8 并行环境正常运行，multiprocessing 无 GIL 瓶颈
- [ ] ReplayBuffer 线程安全，支持并发 push/sample
- [ ] PrioritizedReplayBuffer 按 TD-error 优先采样
- [ ] RolloutBuffer 支持 GAE 计算
- [ ] Network Protocol 可被 PyTorch backend 实现
- [ ] 设备自动检测 CPU/CUDA/MPS
- [ ] TensorBoardLogger 可配置采样率记录 scalar/histogram

### 质量验收
- [ ] 测试覆盖率 ≥ 85%
- [ ] 所有公共接口有完整 type hints
- [ ] 异常层次完整
- [ ] structlog 日志包含 episode/step/env 上下文

## 5. Dependencies

- **无上游依赖**
- **下游被依赖**：Change-2（DQN/PPO）和 Change-3（MADDPG）
