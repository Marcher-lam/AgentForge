# Change Proposal: Capability Layer (Phase 2)

> Type: feature | Priority: P0 | Status: Confirmed
> Depends on: change-20260515-091942-core
> Created: 2026-05-15 | Clarified: 2026-05-15 | Confirmed: 2026-05-15

---

## 1. Intent

实现 Agent 的能力层，包括：
- MCP 协议适配层（工具注册、调用、结果解析，遵循 MCP 2025-03-26 spec）
- Skill 系统（注册、发现、依赖解析、执行）

这两个子系统让 Agent 具备"调用外部工具"和"组合内部能力"的核心能力。

## 2. Scope

### In Scope
- MCPToolRegistry（工具注册/发现/调用，支持流式 AsyncGenerator）
- JSON-RPC 2.0 消息解析和响应生成
- MCP initialize/capabilities 握手
- 远程 MCP Server 连接（stdio + SSE + WebSocket 全传输层）
- SkillRegistry（注册/发现/版本管理，装饰器注册）
- 依赖解析 DAG（拓扑排序 + 循环检测 + 可选依赖）
- SkillExecutor（执行 + 超时 + mutable context 注入）
- 装饰器注册（@registry.tool / @skill_registry.skill）
- sync handler 自动包装（anyio.to_thread）

### Out of Scope
- Skill 的持久化存储
- Skill 市场/分发机制
- MCP resources/prompts（本期仅 tools）

## 3. Clarified Decisions

| # | 问题 | 决策 |
|---|------|------|
| 1 | 流式响应 | **支持**（AsyncGenerator） |
| 2 | 可选依赖 | **支持 optional 标记**（optional 缺失不阻断） |
| 3 | schema 校验 | **严格模式**（拒绝多余字段） |
| 4 | 执行上下文 | **可修改（mutable）**（下游 Skill 可读修改） |
| 5 | 同步 handler | **自动包装** sync → async（anyio.to_thread） |
| 6 | 装饰器注册 | **支持**（@registry.tool / @skill_registry.skill） |
| 7 | 远程 MCP | **全部支持**（本地 + 远程 stdio/SSE/WebSocket） |
| 8 | 异常体系 | **融入 agentforge**（MCPError / SkillError 继承 AgentForgeError） |

## 4. Module Design

### 项目结构
```
agentforge/
├── mcp/
│   ├── __init__.py
│   ├── registry.py             # MCPToolRegistry (local + remote)
│   ├── protocol.py             # JSON-RPC 2.0 handler
│   ├── transport/
│   │   ├── __init__.py
│   │   ├── local.py            # 本地 in-process
│   │   ├── stdio.py            # stdio transport
│   │   ├── sse.py              # SSE transport
│   │   └── websocket.py        # WebSocket transport
│   ├── decorator.py            # @registry.tool
│   └── errors.py               # MCPError hierarchy
├── skill/
│   ├── __init__.py
│   ├── registry.py             # SkillRegistry
│   ├── executor.py             # SkillExecutor
│   ├── dependency.py           # DAG resolver
│   ├── decorator.py            # @skill_registry.skill
│   └── errors.py               # SkillError hierarchy
```

### 异常层次
```
AgentForgeError (from core)
├── MCPError
│   ├── ToolAlreadyRegisteredError
│   ├── ToolNotFoundError
│   ├── ToolCallError
│   ├── SchemaValidationError    # 严格校验失败
│   └── MCPConnectionError       # 远程连接失败
└── SkillError
    ├── SkillAlreadyRegisteredError
    ├── SkillNotFoundError
    ├── CyclicDependencyError
    ├── SkillDependencyNotFoundError
    ├── SkillExecutionError
    └── SkillTimeoutError
```

## 5. Success Criteria

- [ ] MCP initialize → tools/list → tools/call 完整流程（本地）
- [ ] 远程 MCP Server 通过 stdio/SSE/WebSocket 连接并调用工具
- [ ] 流式工具调用返回 AsyncGenerator
- [ ] 严格 input_schema 校验（多余字段被拒绝）
- [ ] 装饰器 @registry.tool 自动推断 input_schema
- [ ] sync handler 自动包装为 async
- [ ] Skill DAG 依赖正确解析（含 optional）
- [ ] Skill mutable context 传递到下游
- [ ] 核心模块测试覆盖率 ≥ 80%

## 6. Dependencies

- **上游**：change-20260515-091942-core
- **可与 Memory 并行开发**
