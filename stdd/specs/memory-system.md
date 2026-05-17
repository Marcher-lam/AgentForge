# Delta Spec: Memory System

> Change: change-20260515-091942-memory | Domain: memory | Type: ADDED
> Status: Updated to reflect actual implementation

---

## Feature: Short-Term Memory

```gherkin
Feature: 短期记忆 (会话级 LRU)
  Agent 在同一会话内读写短期记忆，容量 100，LRU 淘汰。

  Scenario: 存储和检索
    Given 短期记忆 session_id="s1"
    When 调用 store("s1", "用户询问了天气", metadata={"type":"query"})
    Then 返回 UUID (entry_id)
    When 调用 retrieve("s1", entry_id)
    Then SHALL 返回 MemoryEntry(content="用户询问了天气")

  Scenario: 会话隔离
    Given session "s1" 存储了 "记忆A"
    And session "s2" 存储了 "记忆B"
    When 在 "s1" 中调用 search("记忆")
    Then SHALL 仅包含 "记忆A"

  Scenario: LRU 淘汰
    Given 容量为 3，已有 [A, B, C]
    When 存储第 4 条 D
    Then A SHALL 被淘汰（最久未访问，OrderedDict.popitem(last=False)）

  Scenario: 访问刷新优先级
    Given 容量为 3，已有 [A, B, C]
    When retrieve A（move_to_end）
    And 存储第 4 条 D
    Then B SHALL 被淘汰（A 被刷新到末尾）

  Scenario: 清除会话
    When 调用 memory.clear("s1")
    Then "s1" SHALL 无记忆（session 从 _sessions 中移除）
    And 其他会话不受影响

  Scenario: 搜索功能
    Given session "s1" 有多条记忆
    When 调用 search("s1", "天气", top_k=5)
    Then SHALL 按最近访问顺序（reversed）搜索
    And 匹配条件为 content.lower() 包含 query.lower()
    And SHALL 返回 list[SearchResult]，每个结果包含 entry, score=1.0, source="short_term"
    And 结果 SHALL 最多 top_k 条

  Scenario: 删除单条记忆
    Given session "s1" 有 entry_id=E1
    When 调用 delete("s1", E1)
    Then E1 SHALL 从 session 中移除
    And 删除不存在的 entry_id SHALL 不抛出异常
```

## Feature: Long-Term Memory

```gherkin
Feature: 长期记忆 (SQLite 持久化)
  NOT_IMPLEMENTED

  agentforge/memory/__init__.py 仅导出 ShortTermMemory。
  以下功能均未实现：
  - SQLite 持久化存储
  - 跨会话检索
  - 按元数据查询
  - 时间范围查询
  - TTL 过期清理
  - 重启后持久化
```

## Feature: Vector Memory

```gherkin
Feature: 向量记忆 (ChromaDB 语义检索)
  NOT_IMPLEMENTED

  以下功能均未实现：
  - ChromaDB 集成
  - 自动嵌入存储
  - 语义搜索 top-k
  - 余弦相似度度量
  - 可配置嵌入模型
```

## Feature: MemoryManager

```gherkin
Feature: MemoryManager 统一门面
  NOT_IMPLEMENTED

  以下功能均未实现：
  - 三层记忆路由存储
  - 统一搜索
  - 原子 promote 操作
  - promote 到向量层
```
