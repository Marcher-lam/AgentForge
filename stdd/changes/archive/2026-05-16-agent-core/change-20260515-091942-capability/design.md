# Technical Design: Capability Layer (Phase 2)

> Change: change-20260515-091942-capability | Depends on: change-20260515-091942-core

---

## 1. Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│                     Skill System                         │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────┐  │
│  │ SkillRegistry│  │ DAG Resolver  │  │SkillExecutor │  │
│  │              │→ │ (topo sort)   │→ │ (context)    │  │
│  └──────────────┘  └───────────────┘  └──────────────┘  │
│         ▲                                    │           │
│         │ @skill装饰器                        ▼           │
│  ┌──────────────┐                    ┌──────────────┐   │
│  │ SkillContext │                    │ Callbacks    │   │
│  │ (mutable)    │                    │ on_activate  │   │
│  └──────────────┘                    └──────────────┘   │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│                     MCP Adapter                          │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────┐  │
│  │ ToolRegistry │  │ JSON-RPC 2.0  │  │ Schema       │  │
│  │              │→ │ Encoder/Decode│→ │ Validator    │  │
│  └──────────────┘  └───────────────┘  └──────────────┘  │
│         ▲                                    │           │
│         │ @tool装饰器                         ▼           │
│  ┌──────────────┐                    ┌──────────────┐   │
│  │ ToolInvoker  │                    │ Transport    │   │
│  │ (async/sync) │                    │ stdio/SSE/WS │   │
│  └──────────────┘                    └──────────────┘   │
└──────────────────────────────────────────────────────────┘
```

---

## 2. Architecture Decision Records

### ADR-1: DAG 拓扑排序 + 可选依赖

**Context**: Skill 之间存在依赖关系，可选依赖缺失不应阻断执行。

**Decision**: Kahn 算法拓扑排序 + 三阶段解析：先解析 required deps，再标记 optional deps 缺失，最后生成执行计划。

**Rationale**: O(V+E) 线性复杂度；可选依赖跳过而非报错，提高鲁棒性。

**Consequences**: 循环依赖需显式检测并抛出 `CyclicDependencyError`。

### ADR-2: Mutable SkillContext

**Context**: 下游 Skill 需要读取上游 Skill 的输出。

**Decision**: `SkillContext` 为 mutable dict，每个 Skill 执行后可写入，下游 Skill 通过 key 读取。

**Rationale**: 灵活、无类型约束，适合动态组合场景。

**Consequences**: key 冲突时后写覆盖；无类型安全，需文档约定。

### ADR-3: Remote MCP Transport 三合一

**Context**: MCP Server 支持 stdio、SSE、WebSocket 三种传输。

**Decision**: 统一 `Transport` Protocol + 三种实现，由 `transport_url` scheme 自动选择。

**Rationale**: 用户只需一个 URL 即可连接，降低使用门槛。

**Consequences**: 三种 transport 共享握手逻辑但有不同连接管理（进程/HTTP/WS）。

### ADR-4: AsyncGenerator 流式响应

**Context**: 工具执行可能产生流式输出（如文件读取、LLM 生成）。

**Decision**: Tool handler 返回 `AsyncGenerator[str, None]` 时自动流式投递。

**Rationale**: 零侵入——handler 只需 yield 即可，框架负责分片投递。

**Consequences**: 非流式 handler 返回普通值，由框架包装为单次 yield。

---

## 3. Data Model

```python
@dataclass
class ToolMetadata:
    name: str
    description: str
    parameters: dict  # JSON Schema
    returns: dict | None = None

@dataclass
class SkillMetadata:
    name: str
    version: str
    dependencies: list[str]
    optional_dependencies: list[str]
    tags: list[str]

class SkillContext(dict):
    """Mutable context passed through skill execution chain."""
    trace_id: str
    agent_id: UUID
```

---

## 4. File Structure

```
agentforge/
├── mcp/
│   ├── __init__.py
│   ├── registry.py          # ToolRegistry
│   ├── metadata.py          # ToolMetadata
│   ├── invoker.py           # ToolInvoker (sync/async + streaming)
│   ├── jsonrpc.py           # JSON-RPC 2.0 encode/decode
│   ├── schema.py            # Strict JSON Schema validation
│   ├── transport/
│   │   ├── __init__.py      # Transport Protocol + auto-select
│   │   ├── stdio.py         # StdioTransport
│   │   ├── sse.py           # SSETransport
│   │   └── websocket.py     # WebSocketTransport
│   └── handshake.py         # MCP initialize/initialized
├── skill/
│   ├── __init__.py
│   ├── registry.py          # SkillRegistry + decorator
│   ├── metadata.py          # SkillMetadata
│   ├── resolver.py          # DAG topological sort + cycle detection
│   ├── executor.py          # SkillExecutor + context injection
│   └── context.py           # SkillContext
```

### File Change List

| Action | File | Description |
|--------|------|-------------|
| CREATE | agentforge/mcp/registry.py | ToolRegistry (register/unregister/get/list) |
| CREATE | agentforge/mcp/metadata.py | ToolMetadata dataclass |
| CREATE | agentforge/mcp/invoker.py | ToolInvoker (sync wrap + AsyncGenerator streaming) |
| CREATE | agentforge/mcp/jsonrpc.py | JSON-RPC 2.0 request/response codec |
| CREATE | agentforge/mcp/schema.py | Strict schema validation (MCP 2025-03-26) |
| CREATE | agentforge/mcp/transport/\_\_init\_\_.py | Transport Protocol + factory |
| CREATE | agentforge/mcp/transport/stdio.py | Subprocess stdio transport |
| CREATE | agentforge/mcp/transport/sse.py | SSE transport |
| CREATE | agentforge/mcp/transport/websocket.py | WebSocket transport |
| CREATE | agentforge/mcp/handshake.py | MCP handshake flow |
| CREATE | agentforge/skill/registry.py | SkillRegistry + @skill decorator |
| CREATE | agentforge/skill/metadata.py | SkillMetadata dataclass |
| CREATE | agentforge/skill/resolver.py | DAG resolver (Kahn + cycle detection) |
| CREATE | agentforge/skill/executor.py | SkillExecutor (DAG order + context) |
| CREATE | agentforge/skill/context.py | Mutable SkillContext |

---

## 5. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| DAG 循环检测误报 | Low | Medium | Tarjan 算法二次验证 + 详细错误信息 |
| MCP Schema 校验过严拒绝合法请求 | Medium | High | 提供宽松模式选项 + 详细 rejection reason |
| Transport 连接泄漏 | Medium | High | async context manager + 连接池 + heartbeat |
| SkillContext key 冲突 | Medium | Low | namespace prefix convention (skill_name.key) |

---

## 6. Testing Strategy

| Layer | Type | Key Scenarios |
|-------|------|---------------|
| MCP Registry | Unit | register, duplicate name, decorator |
| MCP Invoker | Unit | sync/async/streaming/timeout |
| JSON-RPC | Unit | encode/decode/error |
| Schema | Unit | valid/invalid/extra fields |
| Transport | Integration | 3 transport handshake + message roundtrip |
| Skill DAG | Unit | linear/diamond/cyclic/optional deps |
| Skill Executor | Integration | full chain with context passing |
| **Coverage Target** | | **≥ 80%** |
