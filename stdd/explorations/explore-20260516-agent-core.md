# Exploration Report: agent-core

> Generated: 2026-05-16 | Target: agentforge/ (agent-core change)
> Tests: 104 passed, 1 skipped | Coverage: 95%

---

## 1. 架构总览

```
agentforge/                          # 1,428 行 Python
├── __init__.py                      # 空包初始化
├── types/                           # 核心类型定义（纯数据，无副作用）
│   ├── state.py                     # AgentState 枚举 + 转换表
│   ├── message.py                   # Message frozen dataclass + MessageType
│   ├── errors.py                    # 异常层级（5 层继承树）
│   ├── protocols.py                 # 4 个 runtime_checkable Protocol
│   └── __init__.py                  # 14 symbol 公开 API
├── agent/                           # Agent 生命周期
│   ├── base.py                      # AgentBase ABC + 状态机
│   └── events.py                    # EventEmitter 同步+异步
├── bus/                             # 消息通信层
│   ├── topic_matcher.py             # 通配符匹配（*, **）
│   ├── inprocess.py                 # InProcessMessageBus（async pub/sub + RPC）
│   └── websocket.py                 # WebSocketMessageBus（跨进程）
└── infra/                           # 基础设施
    ├── config.py                    # ENV 配置加载
    ├── logging.py                   # structlog 配置
    └── shutdown.py                  # SIGINT/SIGTERM 优雅关闭
```

## 2. 模块依赖图

```
types ← agent ← bus
  ↑        ↑       ↑
  └────────┴───────┘
       infra (独立，仅被 agent 间接使用)
```

**关键约束**: `types` 是最底层，零依赖；`agent` 依赖 `types`；`bus` 依赖 `types`；`agent` 和 `bus` 互不直接依赖。

## 3. 核心模式分析

### 3.1 AgentBase 状态机

```
CREATED → INITIALIZED → RUNNING ⇄ STOPPED
    ↓          ↓            ↓        ↓
  DESTROYED ←────────────────────────┘
```

- 状态转换通过 `is_valid_transition()` 校验
- `anyio.Lock` 保证 `init/run/stop/destroy` 互斥
- init 失败设置 DESTROYED（不可恢复）
- destroy 幂等（已 DESTROYED 则直接返回）
- 4 个 abstract method: `_on_init/_on_run/_on_stop/_on_destroy`

**约束**: Agent 状态转换是严格的单向/双向有限状态机，DESTROYED 是终态。

### 3.2 InProcessMessageBus

- 每个 subscription 独立 `asyncio.Queue`（容量可配）
- 通配符路由: `*` 单层, `**` 递归
- RPC: `request()` + `respond()` 基于 `asyncio.Future`
- 背压: `await queue.put()` 阻塞式投递（最新修复）
- `_deliver()`: 同步 drain + `ensure_future` 调度异步 handler
- 异常隔离: per-message try/except（最新修复）

**约束**: 所有 async 操作基于 `asyncio`，部分使用 `anyio`（仅 AgentBase._lock）。混用 asyncio/anyio 是潜在风险。

### 3.3 Protocol 接口

4 个 Protocol 定义了跨模块契约:

| Protocol | 方法 | 已有实现 |
|----------|------|----------|
| `MessageBus` | subscribe, unsubscribe, publish, request | InProcessMessageBus, WebSocketMessageBus |
| `ToolRegistry` | register, unregister, get, list_tools | **未实现** |
| `SkillRegistry` | register, get, discover | **未实现** |
| `MemoryStore` | store, retrieve, delete | **未实现**（key-value 版本，非三层记忆） |

## 4. 已识别问题

### P0（需立即修复）

| ID | 问题 | 位置 | 影响 |
|----|------|------|------|
| BUG-1 | `_handle_client` 在 subscribe frame 上崩溃 | `websocket.py:54` | subscribe frame 缺少 `message` 字段 → KeyError → 连接断开 |
| BUG-2 | `_deliver` 用 `asyncio.ensure_future` | `inprocess.py:90` | anyio 环境下可能不执行 async handler |

### P1（近期修复）

| ID | 问题 | 位置 | 影响 |
|----|------|------|------|
| RISK-1 | asyncio/anyio 混用 | `base.py` vs `inprocess.py` | anyio trio backend 下 ensure_future 失效 |
| RISK-2 | `_handle_client` 无 message 字段时先解析再判断类型 | `websocket.py:52-61` | 所有非标准帧类型都崩溃 |
| GAP-1 | `load_config` 不解析 pyproject.toml | `config.py:25-42` | 只读 ENV，`[tool.agentforge]` 配置被忽略 |
| GAP-2 | `MemoryStore` Protocol 与三层记忆设计不匹配 | `protocols.py:37-41` | key-value 接口 vs session-based 三层记忆 |

### P2（持续改进）

| ID | 问题 | 位置 | 影响 |
|----|------|------|------|
| COV-1 | websocket.py 88%（heartbeat, client cleanup 未覆盖） | `websocket.py` | 重连/心跳逻辑缺少测试 |
| COV-2 | shutdown.py 90%（signal handler 和 async callback 未覆盖） | `shutdown.py` | 信号处理路径缺少测试 |
| ARCH-1 | AgentBase 无周期性任务/heartbeat 支持 | `base.py` | Agent 无法自我检查健康状态 |
| ARCH-2 | 无消息序列化版本号 | `message.py` | 消息格式变更时无法向后兼容 |

## 5. 技术栈约束

| 约束 | 详情 |
|------|------|
| Python >= 3.12 | 使用 `X \| None` 语法 |
| asyncio + anyio 混用 | AgentBase 用 anyio.Lock，Bus 用 asyncio.Queue/Future |
| structlog | 日志框架，JSON/Console 双输出 |
| websockets >= 12.0 | 跨进程通信 |
| frozen dataclass (slots=True) | Message 不可变 |
| runtime_checkable Protocol | 运行时 `isinstance()` 检查 |
| pytest-anyio | 所有 async 测试需要 `@pytest.mark.anyio` |
| mypy --strict | 类型检查严格模式 |

## 6. 扩展点分析

### 已定义但未实现的接口

1. **ToolRegistry** — 工具注册/查找，需实现类
2. **SkillRegistry** — 技能注册/发现，需实现类
3. **MemoryStore** — 记忆存储 Protocol，但与三层记忆设计冲突

### AgentBase 扩展点

- `_on_init/_on_run/_on_stop/_on_destroy` — 4 个抽象钩子
- `events` EventEmitter — 状态变更事件
- `agent_id/name` — 身份标识

### Bus 扩展点

- 通配符路由已支持 `*` 和 `**`
- RPC 已支持 request/respond
- WebSocket 支持 start_server / connect 双模式

## 7. 代码质量评估

| 维度 | 评分 | 说明 |
|------|------|------|
| 可读性 | A | 函数短小，命名清晰，注释精炼 |
| 类型安全 | A | mypy --strict 通过，Protocol runtime_checkable |
| 测试覆盖 | A- | 95% 总体，websocket 88% 待提升 |
| 异常处理 | B | bus 层异常隔离已修复，websocket handler 仍有 bug |
| 可扩展性 | B+ | Protocol 接口定义良好，但实现类较少 |
| 并发安全 | B | anyio.Lock 保护状态转换，但 bus 层 asyncio/anyio 混用 |

## 8. 推荐下一步

1. **修复 BUG-1** (websocket subscribe 帧解析) — 最高优先级
2. **统一 async 运行时** — 决定全部用 asyncio 或全部用 anyio，消除混用风险
3. **实现 ToolRegistry/SkillRegistry** — 解除 Protocol 空定义
4. **MemoryStore Protocol 重设计** — 对齐三层记忆架构（session-based + MemoryType）

---

> 此探索报告可直接作为后续 `/stdd:propose` 或 `/stdd:issue` 的输入上下文。
