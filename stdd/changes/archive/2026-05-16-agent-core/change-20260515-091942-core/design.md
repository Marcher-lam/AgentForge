# Technical Design: Core Skeleton

> Change: change-20260515-091942-core | Status: Draft

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────┐
│                    AgentBase (ABC)                │
│  ┌──────────┐  ┌──────────┐  ┌───────────────┐  │
│  │ State    │  │ Event    │  │ Lifecycle     │  │
│  │ Machine  │  │ Emitter  │  │ Hooks         │  │
│  └──────────┘  └──────────┘  └───────────────┘  │
│         ▲              ▲                         │
│         │ anyio.Lock   │                         │
└─────────┼──────────────┼─────────────────────────┘
          │              │
┌─────────┴──┐    ┌──────┴──────────────────────┐
│   Types    │    │      Message Bus            │
│ ┌────────┐ │    │ ┌──────────┐ ┌────────────┐ │
│ │State   │ │    │ │InProcess │ │ WebSocket  │ │
│ │Enum    │ │    │ │Bus       │ │Bus         │ │
│ ├────────┤ │    │ │(anyio)   │ │(websockets)│ │
│ │Message │ │    │ └──────────┘ └────────────┘ │
│ │DC      │ │    └──────────────────────────────┘
│ ├────────┤ │
│ │Protocol│ │    ┌──────────────────────────────┐
│ │s       │ │    │    Infrastructure            │
│ └────────┘ │    │ ┌──────┐ ┌──────┐ ┌───────┐ │
│ ┌────────┐ │    │ │struct│ │config│ │graceful│ │
│ │Error   │ │    │ │log   │ │      │ │shutdown│ │
│ │Hier.   │ │    │ └──────┘ └──────┘ └───────┘ │
│ └────────┘ │    └──────────────────────────────┘
└────────────┘
```

### 分层策略

| 层 | 职责 | 关键模块 |
|----|------|---------|
| Types | 纯数据定义，零依赖 | AgentState, Message, Protocols, Exceptions |
| Agent | 生命周期 + 状态机 + 并发控制 | AgentBase ABC |
| Communication | 消息传递（进程内 + 跨进程） | InProcessBus, WebSocketBus |
| Infrastructure | 横切关注点 | structlog, config, shutdown |

---

## 2. Architecture Decision Records

### ADR-1: anyio 替代 asyncio

**Context**: 需要同时支持 InProcessBus（async queue）和 WebSocketBus（网络 IO）。

**Decision**: 使用 anyio 作为 async 运行时。

**Rationale**: anyio 提供 abstract event loop，可在 asyncio 和 trio 间切换；anyio.Lock 提供跨后端的互斥原语。

**Consequences**: 所有 async 代码必须使用 anyio API（`anyio.sleep` 而非 `asyncio.sleep`）；不支持 asyncio 原生特性如 `loop.add_reader`。

### ADR-2: frozen dataclass + slots for Message

**Context**: Message 在 bus 中高频传递，需要不可变性和低内存开销。

**Decision**: `@dataclass(frozen=True, slots=True)`。

**Rationale**: frozen 保证消息不可变（线程安全）；slots 减少 ~40% 内存（`__dict__` 开销消除）。

**Consequences**: 无法动态添加属性；必须通过 `dataclasses.replace()` 创建变体。

### ADR-3: Protocol 替代 ABC for Registry

**Context**: MessageBus、ToolRegistry、SkillRegistry 需要多实现。

**Decision**: 使用 `typing.Protocol`（结构化子类型）而非 ABC。

**Rationale**: Protocol 不要求显式继承，降低耦合；第三方实现无需 import 基类。

**Consequences**: 无运行时强制检查（除非用 `runtime_checkable`）；IDE 补全依赖 type checker。

### ADR-4: 有界队列 + drop-oldest 背压

**Context**: handler 消费速度可能慢于生产速度。

**Decision**: 每个 handler 绑定 `anyio.create_memory_object_stream(max_buffer_size=N)`，溢出时 drop oldest。

**Rationale**: 保证最新消息优先处理，避免 OOM；失败时发 `message.delivery_failed` 事件。

**Consequences**: 慢消费者可能丢失历史消息；需要客户端处理 delivery_failed。

### ADR-5: WebSocket 服务端持久化订阅

**Context**: 客户端断线重连后需恢复订阅状态。

**Decision**: 服务端维护 `session_id → [subscriptions]` 映射，重连时按 session_id 恢复。

**Rationale**: 客户端无需重新订阅；保证重连期间的消息在重连后可投递。

**Consequences**: 服务端需额外内存存储订阅；需 TTL 清理僵尸 session。

---

## 3. Data Model

### AgentState 枚举 + 转换表

```python
class AgentState(Enum):
    CREATED = "created"
    INITIALIZED = "initialized"
    RUNNING = "running"
    STOPPED = "stopped"
    DESTROYED = "destroyed"

VALID_TRANSITIONS = {
    AgentState.CREATED: {AgentState.INITIALIZED, AgentState.DESTROYED},
    AgentState.INITIALIZED: {AgentState.RUNNING, AgentState.DESTROYED},
    AgentState.RUNNING: {AgentState.STOPPED, AgentState.DESTROYED},
    AgentState.STOPPED: {AgentState.RUNNING, AgentState.DESTROYED},
    AgentState.DESTROYED: set(),  # terminal
}
```

### Message

```python
@dataclass(frozen=True, slots=True)
class Message:
    message_id: UUID
    topic: str
    message_type: MessageType
    sender_id: UUID
    payload: dict[str, Any]
    timestamp: datetime
    correlation_id: UUID | None = None
```

### Protocol Interfaces

```python
class MessageBus(Protocol):
    async def subscribe(self, topic: str, handler: Callable) -> str: ...
    async def unsubscribe(self, subscription_id: str) -> None: ...
    async def publish(self, topic: str, message: Message) -> None: ...
    async def request(self, topic: str, message: Message, timeout: float) -> Message: ...
```

---

## 4. File Structure

```
agentforge/
├── __init__.py
├── types/
│   ├── __init__.py          # re-export all
│   ├── state.py             # AgentState, VALID_TRANSITIONS
│   ├── message.py           # Message, MessageType
│   ├── protocols.py         # MessageBus, ToolRegistry, SkillRegistry, MemoryStore
│   └── errors.py            # AgentForgeError hierarchy
├── agent/
│   ├── __init__.py
│   ├── base.py              # AgentBase ABC
│   ├── state_machine.py     # State transition logic
│   └── events.py            # EventEmitter
├── bus/
│   ├── __init__.py
│   ├── inprocess.py         # InProcessMessageBus
│   ├── websocket.py         # WebSocketMessageBus
│   ├── topic_matcher.py     # Wildcard matching (* and **)
│   └── serialization.py     # Message.to_json / from_json
├── infra/
│   ├── __init__.py
│   ├── logging.py           # structlog config
│   ├── config.py            # pyproject.toml + env loader
│   └── shutdown.py          # SIGINT/SIGTERM graceful shutdown
└── pyproject.toml
```

### File Change List

| Action | File | Description |
|--------|------|-------------|
| CREATE | agentforge/types/\_\_init\_\_.py | Package init + \_\_all\_\_ |
| CREATE | agentforge/types/state.py | AgentState enum + transitions |
| CREATE | agentforge/types/message.py | Message dataclass + MessageType |
| CREATE | agentforge/types/protocols.py | Protocol interfaces |
| CREATE | agentforge/types/errors.py | AgentForgeError hierarchy |
| CREATE | agentforge/agent/base.py | AgentBase ABC + lifecycle hooks |
| CREATE | agentforge/agent/state_machine.py | Transition validation |
| CREATE | agentforge/agent/events.py | EventEmitter (on/off/emit) |
| CREATE | agentforge/bus/inProcess.py | InProcessMessageBus implementation |
| CREATE | agentforge/bus/websocket.py | WebSocketMessageBus implementation |
| CREATE | agentforge/bus/topic_matcher.py | Wildcard topic matching |
| CREATE | agentforge/bus/serialization.py | JSON serialization |
| CREATE | agentforge/infra/logging.py | structlog configuration |
| CREATE | agentforge/infra/config.py | Configuration loading |
| CREATE | agentforge/infra/shutdown.py | Graceful shutdown handler |

---

## 5. Dependency Graph

```
types (zero deps)
  ↑
  ├── agent/base.py → types, anyio
  ├── bus/inProcess.py → types, anyio
  ├── bus/websocket.py → bus/inProcess.py, websockets
  └── infra/* → structlog, types
```

外部依赖: `anyio`, `websockets`, `structlog`, `pydantic` (optional, for config validation)

---

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| anyio Lock 在高并发下性能瓶颈 | Low | Medium | Benchmark with >1000 concurrent transitions; fallback to asyncio.Lock if needed |
| WebSocket 重连期间消息丢失 | Medium | High | Server-side message buffer (bounded) + delivery_failed event |
| Topic 通配符匹配性能 | Low | Low | Pre-compile topic patterns; benchmark with >10k subscriptions |
| structlog 配置冲突 | Low | Low | Use separate logger per agent_id; no global config override |

---

## 7. Testing Strategy

| Layer | Type | Coverage Target |
|-------|------|----------------|
| types/ | Unit (pure functions) | 95% |
| agent/ | Unit + concurrency tests (anyio) | 90% |
| bus/inProcess | Unit + property-based (topic matching) | 90% |
| bus/websocket | Integration (two processes) | 85% |
| infra/ | Unit | 80% |
| **Overall** | | **≥ 85%** |

### Key Test Scenarios

1. **Lifecycle**: init→run→stop→destroy 完整序列 + 事件顺序验证
2. **Concurrency**: 2 tasks 同时调用 run() → 仅一个成功
3. **Invalid transitions**: stop() on CREATED → raises InvalidTransition
4. **Bus wildcard**: subscribe("agent.*") matches "agent.status" but not "agent.status.detail"
5. **RPC timeout**: request() with 1s timeout → raises on timeout
6. **Backpressure**: fill handler queue → oldest dropped + delivery_failed emitted
7. **WS reconnection**: kill connection → auto-reconnect within 3 attempts
8. **Serialization roundtrip**: Message → JSON → Message → identical
