# Change Proposal: Memory Layer (Phase 3)

> Type: feature | Priority: P1 | Status: Confirmed
> Depends on: change-20260515-091942-core
> Created: 2026-05-15 | Clarified: 2026-05-15 | Confirmed: 2026-05-15

---

## 1. Intent

实现 Agent 的记忆系统，包括：
- 短期记忆（会话级 LRU 缓存）
- 长期记忆（跨会话 SQLite 持久化）
- 向量记忆（ChromaDB 语义检索）
- MemoryManager 统一门面

## 2. Scope

### In Scope
- ShortTermMemory（LRU 淘汰、会话隔离、默认容量 100）
- LongTermMemory（SQLite 分表持久化、元数据查询、TTL 主动清理）
- VectorMemory（ChromaDB 余弦相似度、可配置嵌入模型）
- MemoryManager（统一接口、自动路由、原子 promote）

### Out of Scope
- 分布式记忆存储
- 记忆压缩/摘要
- 记忆权限控制
- 自定义嵌入模型训练

## 3. Clarified Decisions

| # | 问题 | 决策 |
|---|------|------|
| 1 | 持久化格式 | **SQLite 分表设计**（memory_entries + memory_metadata） |
| 2 | 短期记忆容量 | **100 条**（LRU 淘汰） |
| 3 | 向量距离度量 | **余弦相似度** |
| 4 | promote 原子性 | **原子操作**（失败则回滚） |
| 5 | TTL 清理策略 | **主动清理**（后台定时任务） |
| 6 | 嵌入模型 | **可配置**（默认 all-MiniLM-L6-v2，可切换 OpenAI） |

## 4. Success Criteria

- [ ] 短期记忆 LRU 淘汰，访问刷新优先级，容量 100
- [ ] 长期记忆跨会话持久化，重启后可 retrieve
- [ ] 向量搜索余弦相似度，recall@5 ≥ 0.8
- [ ] MemoryManager.search 合并三层结果且标注来源
- [ ] promote 原子操作，失败回滚
- [ ] TTL 主动清理过期条目
- [ ] ChromaDB collection 生命周期正确管理
- [ ] 核心模块测试覆盖率 ≥ 80%

## 5. Dependencies

- **上游**：change-20260515-091942-core（MemoryEntry, MemoryStore Protocol）
- **可与 Capability 并行开发**
