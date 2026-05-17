# Tasks: Agent 记忆持久化与向量检索

> Change: change-20260516-memory-persistence | Status: Ready

---

## Phase 1: 核心数据类型

- [x] T1.1: 确认 `MemoryEntry` 和 `MemoryType` 在 core-types 中定义完整
- [x] T1.2: 新增 `SearchResult` 数据类型（entry, score, source）
- [x] T1.3: 单元测试：MemoryEntry 创建、序列化、字段验证

**验收**: 所有数据类型单元测试通过

## Phase 2: ShortTermMemory

- [x] T2.1: 实现 ShortTermMemory（OrderedDict + LRU 淘汰）
  - `store(session_id, content, metadata) -> UUID`
  - `retrieve(session_id, entry_id) -> MemoryEntry | None`
  - `delete(session_id, entry_id)`
  - `clear(session_id)`
  - `search(session_id, query, top_k) -> list[SearchResult]`
- [x] T2.2: 单元测试 — 存储和检索
- [x] T2.3: 单元测试 — LRU 淘汰（容量上限、访问刷新优先级）
- [x] T2.4: 单元测试 — 会话隔离
- [x] T2.5: 单元测试 — 删除和清除

**验收**: spec short-term-memory.md 全部场景通过

## Phase 3: LongTermMemory

- [ ] T3.1: 实现 LongTermMemory（SQLite + aiosqlite）
  - 初始化：创建表结构
  - `store(session_id, content, metadata, ttl) -> UUID`
  - `retrieve(session_id, entry_id) -> MemoryEntry | None`（含 TTL 检查）
  - `query(session_id, since, metadata_filter) -> list[MemoryEntry]`
  - `delete(session_id, entry_id)`
  - `clear(session_id)`
- [ ] T3.2: 单元测试 — 存储和检索
- [ ] T3.3: 单元测试 — 跨会话持久化（关闭重开）
- [ ] T3.4: 单元测试 — TTL 过期
- [ ] T3.5: 单元测试 — 元数据过滤查询
- [ ] T3.6: 单元测试 — 删除操作

**验收**: spec long-term-memory.md 全部场景通过

## Phase 4: VectorMemory

- [ ] T4.1: 实现 VectorMemory（ChromaDB 嵌入式）
  - `store(session_id, content, metadata) -> UUID`
  - `search(session_id, query, top_k) -> list[SearchResult]`
  - `delete(session_id, entry_id)`
- [ ] T4.2: 单元测试 — 存储和语义搜索
- [ ] T4.3: 单元测试 — top-k 限制
- [ ] T4.4: 单元测试 — 会话隔离
- [ ] T4.5: 单元测试 — 删除操作

**验收**: spec vector-memory.md 全部场景通过

## Phase 5: MemoryManager

- [ ] T5.1: 实现 MemoryManager 门面
  - `store(session_id, content, memory_type, **kwargs)`
  - `search(session_id, query, top_k)` — 并行搜索三层
  - `promote(session_id, entry_id, target_type)` — 原子性提升
  - `delete(session_id, entry_id)` — 跨层删除
  - `clear(session_id)` — 跨层清除
- [ ] T5.2: 单元测试 — 智能路由存储
- [ ] T5.3: 单元测试 — 统一搜索（source 标注）
- [ ] T5.4: 单元测试 — promote 正常流程
- [ ] T5.5: 单元测试 — promote 失败回滚
- [ ] T5.6: 单元测试 — 跨层删除和清除

**验收**: spec memory-manager.md 全部场景通过

## Phase 6: 记忆压缩

- [ ] T6.1: 实现 CompressionStrategy 基类
- [ ] T6.2: 实现 SummaryStrategy（摘要压缩）
- [ ] T6.3: 实现 TimeWindowStrategy（时间窗口聚合）
- [ ] T6.4: 实现策略注册机制
- [ ] T6.5: LongTermMemory 集成 compress 方法
- [ ] T6.6: 单元测试 — 时间窗口聚合压缩
- [ ] T6.7: 单元测试 — 信息保留率验证
- [ ] T6.8: 单元测试 — 空记忆压缩
- [ ] T6.9: 单元测试 — 自定义策略注册和执行
- [ ] T6.10: 单元测试 — 无效策略名称异常

**验收**: spec memory-compression.md 全部场景通过

## Phase 7: 集成测试

- [ ] T7.1: 集成测试 — MemoryManager + 三层记忆联调
- [ ] T7.2: 集成测试 — promote 跨层提升完整流程
- [ ] T7.3: 集成测试 — 压缩 + 检索信息保留率

**验收**: 全部集成测试通过，信息保留率 > 80%

---

## 依赖关系

```
T1 → T2, T3, T4（数据类型是基础）
T2 → T5（MemoryManager 依赖 ShortTermMemory）
T3 → T5（MemoryManager 依赖 LongTermMemory）
T4 → T5（MemoryManager 依赖 VectorMemory）
T3 → T6（压缩基于 LongTermMemory）
T5, T6 → T7（集成测试依赖所有模块）
```

## 预估工时

| Phase | 预估 |
|-------|------|
| Phase 1 | 0.5h |
| Phase 2 | 1h |
| Phase 3 | 1.5h |
| Phase 4 | 1h |
| Phase 5 | 1.5h |
| Phase 6 | 1.5h |
| Phase 7 | 1h |
| **合计** | **8h** |
