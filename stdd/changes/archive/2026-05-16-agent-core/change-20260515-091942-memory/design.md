# Technical Design: Memory Layer (Phase 3)

> Change: change-20260515-091942-memory | Depends on: change-20260515-091942-core

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                  MemoryManager (Facade)              │
│  ┌─────────────┐ ┌─────────────┐ ┌──────────────┐  │
│  │ route store │ │ merge search│ │ atomic       │  │
│  │ (type→impl) │ │ (3-layer)   │ │ promote      │  │
│  └─────────────┘ └─────────────┘ └──────────────┘  │
│         │              │              │              │
└─────────┼──────────────┼──────────────┼─────────────┘
          │              │              │
    ┌─────┴────┐   ┌─────┴────┐   ┌────┴─────────┐
    │ShortTerm │   │LongTerm  │   │Vector        │
    │Memory    │   │Memory    │   │Memory        │
    │(LRU 100) │   │(SQLite)  │   │(ChromaDB)    │
    └──────────┘   └──────────┘   └──────────────┘
         │              │              │
    OrderedDict    aiosqlite      chromadb +
    per session    2 tables       sentence-transformers
```

---

## 2. Architecture Decision Records

### ADR-1: SQLite 分表设计

**Context**: 长期记忆需要结构化查询（metadata 过滤、时间范围、TTL）。

**Decision**: 两张表：`memory_entries`（id, content, session_id, type, created_at, expires_at）+ `memory_metadata`（entry_id FK, key, value）。

**Rationale**: 范式化避免 JSON 列查询性能问题；metadata 表支持灵活索引。

**Consequences**: 跨表 JOIN 查询需注意性能；需 WAL mode 保证并发读写。

### ADR-2: ChromaDB 内嵌模式

**Context**: 向量检索需要 embedding 计算 + 相似度搜索。

**Decision**: ChromaDB PersistentClient（本地文件存储），余弦相似度。

**Rationale**: 零外部依赖（无 Vector DB 服务）；PersistentClient 重启不丢数据。

**Consequences**: 不适合超大规模（>1M vectors）；embedding 模型需首次下载。

### ADR-3: Promote 原子操作

**Context**: 短期→长期→向量的提升需保证数据一致性。

**Decision**: 使用 SQLite transaction（长期记忆）+ ChromaDB upsert（向量）的两阶段提交。失败时 ChromaDB delete + SQLite rollback。

**Rationale**: 保证"要么全成功，要么全不变"。

**Consequences**: 性能开销略高于非原子方案；ChromaDB 无原生事务支持需手动补偿。

---

## 3. Data Model

```python
@dataclass(frozen=True, slots=True)
class MemoryEntry:
    entry_id: UUID
    content: str
    session_id: str
    memory_type: Literal["short_term", "long_term", "vector"]
    metadata: dict[str, Any]
    created_at: datetime
    expires_at: datetime | None = None
    embedding: list[float] | None = None  # vector layer only

class SearchTarget(Enum):
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    VECTOR = "vector"
    ALL = "all"

@dataclass
class SearchResult:
    entry: MemoryEntry
    score: float  # similarity or relevance
    source: Literal["short_term", "long_term", "vector"]
```

### SQLite Schema

```sql
CREATE TABLE memory_entries (
    entry_id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    session_id TEXT NOT NULL,
    memory_type TEXT NOT NULL DEFAULT 'long_term',
    created_at TEXT NOT NULL,
    expires_at TEXT
);
CREATE INDEX idx_entries_session ON memory_entries(session_id);
CREATE INDEX idx_entries_expires ON memory_entries(expires_at);

CREATE TABLE memory_metadata (
    entry_id TEXT NOT NULL REFERENCES memory_entries(entry_id) ON DELETE CASCADE,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    PRIMARY KEY (entry_id, key)
);
CREATE INDEX idx_metadata_key_value ON memory_metadata(key, value);
```

---

## 4. File Structure

```
agentforge/
├── memory/
│   ├── __init__.py
│   ├── manager.py          # MemoryManager facade
│   ├── short_term.py       # ShortTermMemory (LRU per session)
│   ├── long_term.py        # LongTermMemory (SQLite)
│   ├── vector.py           # VectorMemory (ChromaDB)
│   ├── embedding.py        # Embedding provider (default/configurable)
│   ├── search.py           # Unified search + merge + ranking
│   ├── promote.py          # Atomic promote logic
│   ├── ttl.py              # TTL cleanup background task
│   └── schema.sql          # SQLite DDL
```

### File Change List

| Action | File | Description |
|--------|------|-------------|
| CREATE | agentforge/memory/manager.py | MemoryManager facade (route/merge/promote) |
| CREATE | agentforge/memory/short_term.py | LRU cache (OrderedDict per session, capacity 100) |
| CREATE | agentforge/memory/long_term.py | SQLite store (aiosqlite, 2-table, TTL cleanup) |
| CREATE | agentforge/memory/vector.py | ChromaDB store (auto-embed, cosine, top-k) |
| CREATE | agentforge/memory/embedding.py | Embedding provider (all-MiniLM-L6-v2 / OpenAI) |
| CREATE | agentforge/memory/search.py | Unified search across 3 layers |
| CREATE | agentforge/memory/promote.py | Atomic promote with rollback |
| CREATE | agentforge/memory/ttl.py | Background TTL cleanup task |
| CREATE | agentforge/memory/schema.sql | SQLite DDL |

---

## 5. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| ChromaDB embedding 模型首次下载慢 | High | Medium | Lazy init + 缓存模型文件 + 文档说明 |
| SQLite WAL mode 并发写入冲突 | Low | Medium | aiosqlite 单 writer + retry |
| Promote 两阶段提交部分失败 | Low | High | ChromaDB 补偿删除 + 日志告警 |
| 向量检索 recall@5 < 0.8 | Medium | High | 测试集验证 + embedding 模型可配置切换 |

---

## 6. Testing Strategy

| Layer | Type | Key Scenarios |
|-------|------|---------------|
| ShortTerm | Unit | store/retrieve/LRU淘汰/session隔离/访问刷新 |
| LongTerm | Unit | CRUD/metadata查询/时间范围/TTL过期/跨重启 |
| Vector | Unit | embed/store/search/recall@5/余弦相似度 |
| Manager | Unit | route/merge search/promote atomic |
| Promote | Integration | short→long→vector 完整链路 + 失败回滚 |
| TTL | Integration | 后台清理 + 已过期不可retrieve |
| **Coverage Target** | | **≥ 80%** |
