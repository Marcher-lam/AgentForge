# Task Breakdown: Memory Layer (Phase 3)

> Change: change-20260515-091942-memory | Priority: P1 | Depends on: change-20260515-091942-core

---

## Task 1: ShortTermMemory（LRU 缓存）
- [ ] 实现 ShortTermMemory（session_id 隔离）
- [ ] 实现 LRU 淘汰策略（容量 100，access 刷新优先级）
- [ ] 实现 store/retrieve/clear 接口
- [ ] 单元测试：存取 + 会话隔离 + LRU 淘汰 + 访问刷新
- **预估**: 25min | **依赖**: change-20260515-091942-core Task 1

## Task 2: LongTermMemory（SQLite 持久化）
- [ ] 实现 SQLite 分表（memory_entries + memory_metadata）
- [ ] 实现 store/retrieve/delete 接口
- [ ] 实现 metadata 过滤查询 + 时间范围查询
- [ ] 实现 TTL 主动清理（后台定时任务）
- [ ] 实现跨重启持久化验证
- [ ] 单元测试：CRUD + 元数据查询 + TTL 过期 + 重启恢复
- **预估**: 40min | **依赖**: change-20260515-091942-core Task 1

## Task 3: VectorMemory（ChromaDB 语义检索）
- [ ] 实现 ChromaDB collection 生命周期管理
- [ ] 实现自动嵌入存储（可配置模型：all-MiniLM-L6-v2 / OpenAI）
- [ ] 实现余弦相似度搜索 top-k
- [ ] 实现搜索结果附带 distance/score
- [ ] 单元测试：存取 + 语义搜索 recall@5 ≥ 0.8 + 相似度排序
- **预估**: 40min | **依赖**: change-20260515-091942-core Task 1

## Task 4: MemoryManager 统一门面
- [ ] 实现 store 智能路由（SHORT_TERM/LONG_TERM/VECTOR）
- [ ] 实现 search 统一搜索（三层合并 + 来源标注）
- [ ] 实现 promote 原子操作（失败回滚）
- [ ] 单元测试：路由 + 合并搜索 + promote 原子性 + 回滚
- **预估**: 35min | **依赖**: Task 1, Task 2, Task 3

## Task 5: 集成测试 + 覆盖率验证
- [ ] 三层记忆完整链路集成测试
- [ ] promote 跨层集成测试（short→long→vector）
- [ ] 并发读写安全性测试
- [ ] 验证测试覆盖率 ≥ 80%
- **预估**: 25min | **依赖**: Task 4
