# Technical Design: RL Foundation Layer

> Change: change-20260515-092930-foundation | No upstream dependency

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                      rlforge                             │
│                                                          │
│  ┌──────────┐    ┌──────────────┐    ┌───────────────┐  │
│  │ Types    │    │ Environments │    │ Buffers       │  │
│  │Transition│    │EnvBase ABC   │    │ReplayBuffer   │  │
│  │Episode   │    │GymWrapper    │    │PrioritizedRB  │  │
│  │Protocols │    │VectorEnv(×8) │    │RolloutBuffer  │  │
│  └──────────┘    └──────────────┘    └───────────────┘  │
│       │                  │                    │          │
│       └──────────────────┼────────────────────┘          │
│                          │                               │
│  ┌──────────────┐    ┌───┴──────┐    ┌───────────────┐  │
│  │ Networks     │    │ Training │    │ Logging       │  │
│  │Protocol(ABC) │    │Mixin     │    │RLLogger iface │  │
│  │MLP(PyTorch)  │    │Callback  │    │TensorBoard    │  │
│  │Device detect │    │Checkpoint│    │Console        │  │
│  └──────────────┘    └──────────┘    └───────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Architecture Decision Records

### ADR-1: Network Protocol 完全抽象 PyTorch

**Context**: PyTorch 是实现细节，不应泄漏到算法层。

**Decision**: 定义 `Network` Protocol（forward/get_weights/set_weights/trainable），MLP 为默认实现。

**Rationale**: 算法层只依赖 Protocol，可替换 JAX/Flax 后端。

**Consequences**: 无法直接使用 `nn.Module` 的高级特性（如 `model.to(device)`）；需 Protocol 层封装 device 管理。

### ADR-2: VectorEnv 使用 multiprocessing

**Context**: Python GIL 限制真正的并行环境交互。

**Decision**: `multiprocessing.Process` + `Queue` 通信。

**Rationale**: 每个 env 在独立进程中运行，避免 GIL；CPU-bound env step 可真正并行。

**Consequences**: 进程间通信有序列化开销；不共享内存（需 pickle obs/reward）。

### ADR-3: Buffer 线程安全加锁

**Context**: 训练线程采样和采集线程写入需要并发安全。

**Decision**: `threading.Lock` 保护 `push` 和 `sample` 操作。

**Rationale**: 简单可靠；Lock 粒度为单次操作，竞争窗口小。

**Consequences**: 高频 push/sample 可能有锁竞争；可优化为双缓冲减少锁持有时间。

### ADR-4: Gymnasium 5-tuple API

**Context**: Gymnasium 0.29+ 的 step() 返回 5-tuple。

**Decision**: EnvBase.step() 返回 `(obs, reward, terminated, truncated, info)`。

**Rationale**: 区分 terminated（失败/成功）和 truncated（时间到），影响 Q-value 计算。

**Consequences**: 旧 Gym 4-tuple 环境需适配层。

---

## 3. Data Model

```python
@dataclass(frozen=True, slots=True)
class Transition:
    obs: np.ndarray
    action: int | np.ndarray
    reward: float
    next_obs: np.ndarray
    terminated: bool
    truncated: bool
    info: dict

@dataclass
class Episode:
    transitions: list[Transition]
    total_reward: float
    length: int
    seed: int | None = None

class Network(Protocol):
    def forward(self, x: np.ndarray) -> np.ndarray: ...
    def get_weights(self) -> dict[str, np.ndarray]: ...
    def set_weights(self, weights: dict[str, np.ndarray]) -> None: ...
    @property
    def trainable(self) -> bool: ...
```

---

## 4. File Structure

```
rlforge/
├── __init__.py
├── types/
│   ├── __init__.py
│   ├── transition.py        # Transition, Trajectory, Episode
│   └── protocols.py         # Network, Agent, Logger Protocol
├── envs/
│   ├── __init__.py
│   ├── base.py              # EnvBase ABC (5-tuple)
│   ├── gym_wrapper.py       # Gymnasium 适配器
│   ├── vector.py            # VectorEnv (multiprocessing)
│   └── errors.py            # EnvError hierarchy
├── buffers/
│   ├── __init__.py
│   ├── replay.py            # ReplayBuffer (thread-safe)
│   ├── prioritized.py       # PrioritizedReplayBuffer (sum-tree)
│   ├── rollout.py           # RolloutBuffer (GAE)
│   └── errors.py            # BufferError hierarchy
├── networks/
│   ├── __init__.py
│   ├── protocol.py          # Network Protocol
│   ├── mlp.py               # MLP (PyTorch backend)
│   └── device.py            # CPU/CUDA/MPS auto-detect
├── logging/
│   ├── __init__.py
│   ├── base.py              # RLLogger Protocol
│   ├── tensorboard.py       # TensorBoardLogger
│   └── console.py           # ConsoleLogger
├── training/
│   ├── __init__.py
│   ├── mixin.py             # TrainerMixin (seed/checkpoint/device)
│   └── callbacks.py         # Callback Protocol + hooks
├── config.py                # pyproject.toml + env loader
└── errors.py                # RLForgeError base
```

---

## 5. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| VectorEnv 进程泄漏 | Medium | High | atexit handler + context manager |
| PrioritizedReplay sum-tree 实现 bug | Medium | Medium | Property-based testing + 分布验证 |
| MPS device 兼容性 | Medium | Low | Runtime detection + fallback to CPU |
| TensorBoard 日志积压 | Low | Medium | 可配置采样率 + 异步写入 |

---

## 6. Testing Strategy

| Layer | Type | Key Scenarios |
|-------|------|---------------|
| Types | Unit | Transition construction, Episode stats |
| EnvBase | Unit | reset/step 5-tuple, seed reproducibility |
| VectorEnv | Integration | 8 parallel envs, multiprocessing throughput |
| Buffers | Unit | push/sample/overflow/thread-safety/sum-tree |
| Network Protocol | Unit | forward shape, get/set weights roundtrip |
| TrainerMixin | Unit | seed control, checkpoint save/load, device detect |
| TensorBoard | Unit | scalar/histogram write, sampling rate |
| **Coverage Target** | | **≥ 85%** |
