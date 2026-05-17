# Design: Agent 记忆持久化与向量检索

> Change: change-20260516-memory-persistence | Status: Draft
> Depends on: 00-core-types, 01-agent-lifecycle

---

## 架构总览

```
                    ┌──────────────────┐
                    │  MemoryManager   │  ← 统一门面
                    │  (Facade)        │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
    ┌─────────▼──────┐ ┌────▼────────┐ ┌───▼──────────┐
    │ ShortTermMemory│ │LongTermMemory│ │ VectorMemory  │
    │ (LRU Cache)    │ │ (SQLite)     │ │ (ChromaDB)    │
    └────────────────┘ └──────────────┘ └───────────────┘
```

## 数据类型

```python
# 复用 core-types 中的定义
class MemoryType(Enum):
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    VECTOR = "vector"

@dataclass
class MemoryEntry:
    id: str                    # UUID
    session_id: str
    content: str
    metadata: dict[str, Any]
    memory_type: MemoryType
    created_at: datetime
    accessed_at: datetime
    ttl: int | None = None     # 秒数，仅长期记忆使用

@dataclass
class SearchResult:
    entry: MemoryEntry
    score: float               # 相似度分数
    source: MemoryType         # 来源层
```

## 模块设计

### ShortTermMemory

- 内部使用 `OrderedDict` 实现 LRU
- key = entry_id (UUID), value = MemoryEntry
- `store` → 检查容量，淘汰 LRU 条目，插入尾部
- `retrieve` → 移动到尾部（刷新 accessed_at）
- `delete` → 按 key 移除
- `clear` → 按 session_id 过滤清除
- 线程安全：非必须（单会话内使用）

### LongTermMemory

- 持久化到 SQLite（aiosqlite）
- 表结构：`memories(id, session_id, content, metadata_json, memory_type, created_at, accessed_at, ttl, expires_at)`
- `store` → INSERT 行，设置 expires_at = now + ttl
- `retrieve` → SELECT + UPDATE accessed_at，检查 expires_at
- `query` → SELECT with WHERE（session_id, since, metadata_filter）
- `delete` → DELETE by id
- `compress` → 按策略聚合，生成摘要条目，标记原始为 compressed
- TTL 惰性检查：retrieve 时检查，query 时过滤

### VectorMemory

- 基于 ChromaDB（嵌入式模式）
- Collection 按 session_id 隔离（或使用 metadata filter）
- `store` → 调用 embedding model 生成向量，add to collection
- `search` → query collection with embedding，返回 top-k
- `delete` → delete from collection by id
- 嵌入模型：sentence-transformers all-MiniLM-L6-v2（384 维）

### MemoryManager

- 持有三层 Memory 实例的引用
- `store(session_id, content, memory_type, **kwargs)` → 路由到对应层
- `search(session_id, query, top_k)` → 并行搜索三层，合并排序
- `promote(session_id, entry_id, target_type)` → 从源层读取，写入目标层，失败则回滚
- `delete(session_id, entry_id)` → 在所有层中查找并删除
- `clear(session_id)` → 清除三层中该会话的所有记忆

### 压缩策略

- `CompressionStrategy` 抽象基类：`compress(entries) -> list[MemoryEntry]`
- 内置 `SummaryStrategy`：按时间窗口分组，对每组内容生成摘要
- 内置 `TimeWindowStrategy`：按时间窗口聚合，保留每组最新 N 条
- 自定义策略通过注册机制添加

## 依赖

```
agentforge.memory
├── __init__.py
├── types.py          # MemoryEntry, MemoryType, SearchResult（或从 core-types 导入）
├── short_term.py     # ShortTermMemory
├── long_term.py      # LongTermMemory
├── vector_memory.py  # VectorMemory
├── manager.py        # MemoryManager
└── compression/
    ├── __init__.py
    ├── base.py       # CompressionStrategy
    └── strategies.py # SummaryStrategy, TimeWindowStrategy
```

## 关键设计决策

1. **LRU 用 OrderedDict 而非 functools.lru_cache**：需要按 session_id 隔离，标准 lru_cache 不支持
2. **SQLite 而非文件**：单文件、零配置、支持查询、跨平台
3. **ChromaDB 嵌入式模式**：无需外部服务，开发阶段零运维
4. **promote 不删除源条目**：保留原始层的数据完整性，避免信息丢失
5. **压缩策略可插拔**：通过注册机制支持自定义策略
6. **所有 async**：使用 anyio 兼容 API，不阻塞事件循环
