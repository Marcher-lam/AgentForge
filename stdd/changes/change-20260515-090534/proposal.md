# Change Proposal: Multi-Agent Collaboration Framework Core Engine

> Type: feature | Priority: high | Status: Confirmed
> Created: 2026-05-15 | Confirmed: 2026-05-15 | Author: AI Copilot

---

## 1. Intent (意图)

实现一个多 Agent 协作框架的核心引擎，为上层应用提供 Agent 生命周期管理、Agent 间通信、工具协议适配、Skill 执行和记忆检索的完整基础设施。

**核心价值**：
- 标准化 Agent 的创建、运行、销毁流程
- 提供统一的 Agent 间通信机制
- 通过 MCP 协议打通外部工具生态
- Skill 系统实现能力的动态注册与组合
- 记忆系统支撑 Agent 的上下文感知和长期学习

---

## 2. Scope (范围)

### In Scope (本期实现)

| # | 子系统 | 核心能力 | 技术选型 |
|---|--------|---------|---------|
| 1 | Agent 基类与生命周期 | init → run → stop → destroy 状态机 | Python ABC + anyio |
| 2 | Agent 通信总线 | WebSocket pub/sub，支持 topic/channel | anyio.Queue + websockets |
| 3 | MCP 协议适配层 | 工具注册、调用、结果解析 | MCP spec 2025-03-26 / JSON-RPC 2.0 |
| 4 | Skill 系统 | 注册、发现、执行、依赖解析 | Registry pattern + DAG |
| 5 | 记忆系统 | 短期记忆、长期记忆、向量检索 | In-memory + ChromaDB |

### Out of Scope (不在本期)

- Agent 调度与编排引擎（Supervisor/Router 模式）
- 分布式 Agent 部署与跨节点通信
- 用户权限与安全沙箱
- 可视化监控 Dashboard
- Agent 性能指标采集与告警
- 持久化存储层（本期记忆系统仅用内存+ChromaDB）

---

## 3. Approach (方案)

### 3.1 架构分层

```
┌─────────────────────────────────────────┐
│           Application Layer             │
├─────────────────────────────────────────┤
│  Agent Lifecycle  │  Skill System       │
│  (AgentBase)      │  (SkillRegistry)    │
├─────────────────────────────────────────┤
│  Communication Bus  │  MCP Adapter      │
│  (MessageBus)       │  (ToolProtocol)   │
├─────────────────────────────────────────┤
│           Memory System                  │
│  (ShortTerm │ LongTerm │ VectorStore)   │
├─────────────────────────────────────────┤
│           Core Types & Interfaces        │
└─────────────────────────────────────────┘
```

### 3.2 关键设计决策

1. **Python 3.12+**：利用 PEP 702 @deprecated、Self 类型、改进的异常处理
2. **anyio 异步框架**：兼容 asyncio 和 trio，提高框架移植性
3. **双模通信**：抽象 MessageBus 接口，默认 anyio.Queue（进程内），可切换到 WebSocket（跨进程）
4. **MCP 2025-03-26**：适配最新 MCP spec，支持 tools/list, tools/call, resources, prompts
5. **插件化 Skill**：Skill 通过 Registry 注册，支持依赖声明和 DAG 拓扑排序
6. **ChromaDB 向量存储**：嵌入式部署，零外部服务依赖
7. **poetry 依赖管理**：成熟稳定，社区广泛使用

### 3.3 分期建议

鉴于 scope 较大（5 个子系统），建议分 3 期交付：

- **Phase 1（核心骨架）**：Agent 基类 + 通信总线 + Core Types
- **Phase 2（能力层）**：MCP 适配层 + Skill 系统
- **Phase 3（记忆层）**：记忆系统 + 集成测试

---

## 4. Success Criteria (验收标准)

### 功能验收

- [ ] Agent 可完成完整的 init → run → stop → destroy 生命周期
- [ ] 两个 Agent 可通过通信总线进行 pub/sub 消息收发（进程内 + WebSocket 双模）
- [ ] 可通过 MCP 协议注册工具并由 Agent 调用，正确解析返回结果
- [ ] Skill 可注册、发现、执行，依赖关系被正确解析
- [ ] 短期记忆可在同一会话内读写，长期记忆跨会话持久化
- [ ] 向量检索能根据 query 返回 top-k 相关记忆（ChromaDB）

### 质量验收

- [ ] 核心模块单元测试覆盖率 ≥ 80%
- [ ] 所有公共接口有 Python type hints
- [ ] 关键路径有集成测试覆盖
- [ ] 使用 pytest + pytest-asyncio 进行异步测试

---

## 5. Risks & Open Questions (风险与待确认)

### 风险

| # | 风险 | 影响 | 缓解措施 |
|---|------|------|---------|
| 1 | MCP spec 可能有版本变动 | 适配层返工 | 抽象 Protocol 接口，隔离具体实现 |
| 2 | 5 个子系统耦合度需要仔细控制 | 改一处动全身 | 依赖注入 + Protocol 接口契约 |
| 3 | ChromaDB 嵌入模型选型 | 向量质量影响检索效果 | 默认 all-MiniLM-L6-v2，可配置 |

### 已确认决策

| # | 问题 | 决策 |
|---|------|------|
| 1 | 语言选型 | **Python 3.12+** |
| 2 | 向量数据库 | **ChromaDB**（嵌入式，本地优先） |
| 3 | 通信模式 | **双模**（anyio.Queue 进程内 + WebSocket 跨进程） |
| 4 | MCP 版本 | **2025-03-26**（最新稳定版） |
| 5 | 异步框架 | **anyio**（兼容 asyncio + trio） |
| 6 | 依赖管理 | **poetry** |

---

## 6. References (参考)

- MCP Protocol Spec (2025-03-26): https://modelcontextprotocol.io/specification/2025-03-26
- JSON-RPC 2.0: https://www.jsonrpc.org/specification
- ChromaDB: https://docs.trychroma.com/
- anyio: https://anyio.readthedocs.io/
- STDD Config: `stdd/config.yaml`
