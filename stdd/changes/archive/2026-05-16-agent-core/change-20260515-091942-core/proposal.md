# Change Proposal: Core Skeleton (Phase 1)

> Type: feature | Priority: P0 | Status: Clarified
> Created: 2026-05-15 | Clarified: 2026-05-15

---

## 1. Intent

实现多 Agent 协作框架的核心骨架，包括：
- 全局共享类型和 Protocol 接口定义
- Agent 基类（标准化的生命周期状态机）
- 双模通信总线（进程内 + WebSocket）

这是整个框架的地基——所有后续子系统都依赖此 Change。

## 2. Scope

### In Scope
- Core Types & Interfaces（AgentState、Message、Protocol 接口）
- AgentBase ABC（init → run → stop → destroy 状态机 + 事件钩子）
- InProcessMessageBus（anyio.Queue pub/sub + request/response）
- WebSocketMessageBus（跨进程通信 + 断线重连 + 心跳）
- 消息序列化/反序列化（JSON 编解码）
- 分层异常体系（AgentForgeError 层次结构）
- 优雅关机（SIGINT/SIGTERM 信号处理）

### Out of Scope
- MCP 协议适配（Change-2）
- Skill 系统（Change-2）
- 记忆系统（Change-3）
- Agent 调度与编排

## 3. Clarified Decisions (澄清决策)

### 边界问题（Round 1）

| # | 问题 | 决策 |
|---|------|------|
| 1 | stop() 期间收到新消息 | **丢弃新消息** — STOPPED 状态不处理新消息 |
| 2 | WebSocket 重连时订阅关系恢复 | **服务端持久化** — 重连后自动恢复订阅 |
| 3 | Agent init 失败后是否可重试 | **必须销毁重建** — 不允许重试 init |
| 4 | 消息投递到 handler 失败 | **发布错误事件** — 发送 `message.delivery_failed` 事件 |
| 5 | 通配符匹配深度 | **双层** — `*` 单层匹配，`**` 递归匹配 |

### 边界条件（Round 2）

| # | 问题 | 决策 |
|---|------|------|
| 6 | 并发状态转换 | **anyio.Lock 互斥** — 先到先得，后来的操作被拒绝 |
| 7 | 慢 handler 背压 | **有界队列 + 丢弃最旧** — 队列满时丢弃最早的消息 |
| 8 | 优雅关机 | **支持 SIGINT/SIGTERM** — 先 stop 所有 Agent 再 destroy |
| 9 | 异常体系 | **分层异常** — AgentForgeError → 子类异常层次 |

### 非功能性需求（Round 3）

| # | 问题 | 决策 |
|---|------|------|
| 10 | Python 包名 | **agentforge.*** — agentforge/types, agent, bus, mcp, skill, memory |
| 11 | 日志方案 | **structlog** — 结构化 JSON 日志，带 agent_id/topic 上下文 |
| 12 | 配置机制 | **pyproject.toml + env** — [tool.agentforge] 段 + 环境变量覆盖 |
| 13 | WebSocket 库 | **websockets** — 成熟稳定，anyio 原生支持 |

## 4. Boundary Analysis (边界分析)

### 外部可观测行为
1. 创建 Agent 实例 → 初始状态 INIT
2. 调用 init() → 触发初始化钩子 → 保持 INIT
3. 调用 run() → 状态变为 RUNNING → 触发 started 事件
4. 调用 stop() → 状态变为 STOPPED → 触发 stopped 事件 → **丢弃后续消息**
5. 调用 destroy() → 状态变为 DESTROYED → 资源释放 → **不可逆**
6. Agent A 发布消息到 topic → Agent B 的 handler 收到消息
7. Agent A 发起 request → Agent B handler 返回 → Agent A 收到响应
8. handler 处理失败 → **发布 `message.delivery_failed` 事件**

### 隐式约束
- **不可变状态转换**：DESTROYED 是终态，不可逆
- **init 不可重试**：init 失败必须 destroy 后重建
- **并发互斥**：anyio.Lock 保护状态转换，先到先得
- **事件顺序保证**：同一 topic 的消息按发布顺序投递
- **handler 隔离**：单个 handler 异常不影响其他 handler
- **背压保护**：handler 使用有界队列，满时丢弃最旧消息
- **幂等性**：destroy() 和 unsubscribe() 多次调用不报错
- **超时兜底**：stop/destroy/request 都有超时保护
- **通配符双层**：`*` 匹配单层，`**` 递归匹配所有子级

### 异常层次结构
```
AgentForgeError (base)
├── AgentError
│   ├── AgentStateError          # 非法状态转换
│   ├── AgentInitError           # init 失败
│   └── AgentStopTimeoutError    # stop 超时
├── BusError
│   ├── BusConnectionError       # WebSocket 连接失败
│   ├── MessageTimeoutError      # request 超时
│   ├── MessageDecodeError       # JSON 解析失败
│   └── DeliveryError            # 消息投递失败
└── ConfigError                  # 配置错误
```

### 项目结构
```
agentforge/
├── __init__.py
├── types/
│   ├── __init__.py              # 公共类型导出
│   ├── agent.py                 # AgentState, AgentConfig
│   ├── message.py               # Message, MessageType
│   ├── mcp.py                   # ToolDescriptor, ToolCallRequest/Result
│   ├── skill.py                 # SkillDescriptor
│   ├── memory.py                # MemoryEntry, MemoryType
│   └── protocols.py             # MessageBus, ToolRegistry, SkillRegistry, MemoryStore
├── agent/
│   ├── __init__.py
│   ├── base.py                  # AgentBase ABC
│   └── errors.py                # AgentError hierarchy
├── bus/
│   ├── __init__.py
│   ├── base.py                  # MessageBus Protocol impl
│   ├── inprocess.py             # InProcessMessageBus
│   ├── websocket.py             # WebSocketMessageBus
│   ├── serializer.py            # JSON 编解码
│   └── errors.py                # BusError hierarchy
├── config.py                    # pyproject.toml + env 配置加载
├── logging.py                   # structlog 配置
└── shutdown.py                  # SIGINT/SIGTERM 优雅关机
```

## 5. Success Criteria

### 功能验收
- [ ] Agent 完整走完 init → run → stop → destroy，事件正确触发
- [ ] 并发状态转换被 Lock 正确互斥
- [ ] 两个 Agent 进程内 pub/sub 消息收发延迟 < 1ms
- [ ] WebSocket 跨进程消息收发延迟 < 50ms（localhost）
- [ ] 非法状态转换抛出 AgentStateError
- [ ] STOPPED 状态丢弃新消息
- [ ] handler 异常发布 `message.delivery_failed` 事件
- [ ] 通配符 `*` 单层匹配，`**` 递归匹配

### 质量验收
- [ ] 核心模块测试覆盖率 ≥ 85%
- [ ] 所有公共接口有完整 type hints
- [ ] 异常层次完整，调用方可精确 catch
- [ ] structlog 日志包含 agent_id/topic 等上下文
- [ ] SIGINT/SIGTERM 触发优雅关机

## 6. Dependencies

- **无上游依赖**（这是第一个 Change）
- **下游被依赖**：Change-2（MCP/Skill）和 Change-3（Memory）均依赖此 Change 的类型和 Agent 基类

## 7. Tech Stack Summary

| 项 | 选型 |
|---|------|
| 语言 | Python 3.12+ |
| 异步 | anyio（兼容 asyncio + trio） |
| WebSocket | websockets |
| 日志 | structlog |
| 配置 | pyproject.toml [tool.agentforge] + env |
| 依赖管理 | poetry |
| 测试 | pytest + pytest-anyio |
