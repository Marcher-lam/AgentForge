# Task Breakdown: Capability Layer (Phase 2)

> Change: change-20260515-091942-capability | Priority: P1 | Depends on: change-20260515-091942-core

---

## Task 1: ToolRegistry + MCP Tool 基础框架
- [ ] 实现 ToolRegistry（register/unregister/get/list）
- [ ] 实现 ToolMetadata dataclass（name, description, parameters JSON Schema）
- [ ] 实现 JSON-RPC 2.0 请求/响应编解码
- [ ] 实现严格 schema 校验（MCP 2025-03-26 spec）
- [ ] 单元测试：注册/查找 + schema 校验 + JSON-RPC 编解码
- **预估**: 30min | **依赖**: change-20260515-091942-core Task 1

## Task 2: Tool 执行引擎 + AsyncGenerator 流式
- [ ] 实现 tool invoke 执行（同步/异步 handler 适配）
- [ ] 实现 AsyncGenerator 流式响应（TextStreamContent）
- [ ] 实现执行超时 + 异常包装
- [ ] 实现调用日志（structlog agent_id/tool_name 上下文）
- [ ] 单元测试：正常调用 + 流式 + 超时 + 异常
- **预估**: 35min | **依赖**: Task 1

## Task 3: Remote MCP Transport（stdio/SSE/WebSocket）
- [ ] 实现 stdio transport（子进程双向通信）
- [ ] 实现 SSE transport（EventSource + POST）
- [ ] 实现 WebSocket transport（ws:// 双向）
- [ ] 实现 MCP handshake（initialize → initialized）
- [ ] 实现断线重连 + 心跳保活
- [ ] 单元测试：三种 transport 握手 + 消息收发
- **预估**: 45min | **依赖**: Task 1

## Task 4: SkillRegistry + DAG 依赖解析
- [ ] 实现 SkillRegistry（register/discover/get）
- [ ] 实现 SkillMetadata dataclass（name, deps, optional_deps）
- [ ] 实现 DAG 拓扑排序 + 循环检测
- [ ] 实现可选依赖跳过（missing optional dep → warn + skip）
- [ ] 单元测试：注册/发现 + DAG 正常 + 循环检测 + 可选依赖
- **预估**: 35min | **依赖**: change-20260515-091942-core Task 1

## Task 5: Skill 执行上下文 + Mutable Context
- [ ] 实现 SkillContext（mutable dict，执行间可修改）
- [ ] 实现 SkillExecutor（按 DAG 顺序执行，注入 context）
- [ ] 实现 skill 生命周期钩子（on_activate/on_deactivate）
- [ ] 实现执行链路追踪（trace_id 透传）
- [ ] 单元测试：上下文传递 + 修改 + DAG 执行顺序
- **预估**: 30min | **依赖**: Task 4

## Task 6: 集成测试 + 覆盖率验证
- [ ] MCP 完整调用链集成测试（local + remote transport）
- [ ] Skill DAG 执行集成测试（含可选依赖场景）
- [ ] Tool + Skill 联合集成测试
- [ ] 验证测试覆盖率 ≥ 80%
- **预估**: 30min | **依赖**: Task 2, Task 3, Task 5
