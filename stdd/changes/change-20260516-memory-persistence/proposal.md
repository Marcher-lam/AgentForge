# Proposal: Agent 记忆持久化与向量检索

> Change: change-20260516-memory-persistence | Status: Approved
> Depends on: 00-core-types, 01-agent-lifecycle
> Module: `agentforge/memory/`

---

## 需求概述

实现 Agent 的三层记忆系统：短期记忆（会话级 LRU）、长期记忆（SQLite 持久化）、向量记忆（ChromaDB 语义检索），并通过 MemoryManager 门面统一管理，支持记忆层间提升和长期记忆压缩。

## 边界

### IN（包含）
- ShortTermMemory: 会话级 LRU 缓存，容量可配
- LongTermMemory: SQLite 持久化存储，支持 TTL 过期和元数据查询
- VectorMemory: ChromaDB 向量存储，语义检索 top-k
- MemoryManager: 统一门面，智能路由、promote、统一搜索
- 记忆压缩：长期记忆的摘要/聚合压缩策略
- MemoryEntry 数据类型和 MemoryType 枚举（在 core-types 中定义）

### OUT（不包含）
- 分布式记忆共享（多 Agent 间记忆同步）
- 记忆加密和安全访问控制
- 记忆版本管理和回滚
- 自定义嵌入模型训练

## 隐含约束

1. 所有操作为 async，使用 anyio 兼容 API
2. 向量维度由嵌入模型决定，不硬编码
3. LongTermMemory 持久化到磁盘，跨重启存活
4. ShortTermMemory 的淘汰策略为 LRU（基于 accessed_at）
5. 搜索结果包含 source 字段标识来源层

## 技术选型

| 组件 | 技术 | 理由 |
|------|------|------|
| 短期存储 | dict + OrderedDict | 纯内存，LRU 天然支持 |
| 长期存储 | SQLite (aiosqlite) | 单文件、零配置、跨平台 |
| 向量存储 | ChromaDB | 轻量嵌入式、自动嵌入 |
| 嵌入模型 | sentence-transformers (all-MiniLM-L6-v2) | 384 维、速度快 |
| 压缩策略 | 摘要压缩（基于时间窗口聚合） | 保留关键信息、减少存储量 |

## 验收标准

- [ ] 三层记忆各自独立读写
- [ ] MemoryManager 统一门面工作正常
- [ ] promote 操作原子性（失败回滚）
- [ ] 统一搜索返回 source 标注
- [ ] 长期记忆压缩后信息保留率 > 80%
- [ ] 所有操作 async，不阻塞事件循环
