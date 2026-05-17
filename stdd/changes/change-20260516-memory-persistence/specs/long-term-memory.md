# Delta Spec: Long-Term Memory

> Change: change-20260516-memory-persistence | Domain: memory/long-term | Type: ADDED
> Status: Draft

---

## Feature: 跨会话持久化

```gherkin
Feature: 长期记忆 - SQLite 持久化存储
  系统 SHALL 提供基于 SQLite 的长期记忆存储，支持跨会话持久化和 TTL 过期。

  Scenario: 存储长期记忆
    Given LongTermMemory 实例，db_path 为临时文件路径
    When 调用 memory.store(session_id="s1", content="用户偏好暗色主题", metadata={"category":"preference"})
    Then SHALL 返回生成的 UUID
    And 数据 SHALL 写入 SQLite 数据库

  Scenario: 检索长期记忆
    Given 一条长期记忆已存储，id 为 entry_id
    When 调用 memory.retrieve(session_id="s1", entry_id=entry_id)
    Then SHALL 返回 MemoryEntry(content="用户偏好暗色主题", metadata={"category":"preference"})
    And accessed_at SHALL 被更新

  Scenario: 跨会话持久化
    Given LongTermMemory 实例，db_path 为固定文件路径
    And 存储了一条记忆
    When 关闭实例并创建新实例指向同一 db_path
    Then 新实例 SHALL 能检索到之前存储的记忆

  Scenario: 检索不存在的条目
    Given 一个不存在的 UUID
    When 调用 memory.retrieve("s1", nonexistent_id)
    Then SHALL 返回 None
```

## Feature: TTL 过期

```gherkin
Feature: TTL 自动过期
  长期记忆 SHALL 支持 TTL（Time-To-Live），过期条目不可检索。

  Scenario: 设置 TTL 并过期
    Given 存储一条记忆，ttl_seconds=1
    When 等待超过 1 秒
    And 调用 memory.retrieve
    Then SHALL 返回 None（已过期）

  Scenario: 无 TTL 的条目永不过期
    Given 存储一条记忆，未设置 ttl
    When 等待任意时间
    Then 条目 SHALL 仍可检索

  Scenario: 按时间范围查询
    Given 存储了 3 条记忆，时间分别为 T1, T2, T3
    When 调用 memory.query(session_id, since=T2)
    Then SHALL 仅返回 T2 和 T3 之后的记忆
```

## Feature: 元数据查询

```gherkin
Feature: 元数据过滤查询
  长期记忆 SHALL 支持按元数据键值过滤。

  Scenario: 按元数据过滤
    Given 存储了 3 条记忆
      | content   | metadata               |
      | "偏好A"   | {"type":"preference"}  |
      | "事实B"   | {"type":"fact"}        |
      | "偏好C"   | {"type":"preference"}  |
    When 调用 memory.query(session_id, metadata_filter={"type":"preference"})
    Then SHALL 返回 2 条结果（"偏好A" 和 "偏好C"）

  Scenario: 删除长期记忆
    Given 一条长期记忆已存储
    When 调用 memory.delete(session_id, entry_id)
    Then 再次检索 SHALL 返回 None
```
