# Delta Spec: Short-Term Memory

> Change: change-20260516-memory-persistence | Domain: memory/short-term | Type: ADDED
> Status: Draft

---

## Feature: 短期记忆读写

```gherkin
Feature: 短期记忆 - 会话级 LRU 缓存
  系统 SHALL 提供会话级短期记忆，支持 LRU 淘汰和会话隔离。

  Scenario: 存储记忆条目
    Given ShortTermMemory 实例，session_id="s1"，max_size=100
    When 调用 memory.store("s1", "用户询问了天气", metadata={"type":"query"})
    Then SHALL 返回生成的 UUID
    And 条目 SHALL 可通过 retrieve 获取

  Scenario: 检索记忆条目
    Given 一条记忆已存储，id 为 entry_id
    When 调用 memory.retrieve("s1", entry_id)
    Then SHALL 返回 MemoryEntry(content="用户询问了天气", metadata={"type":"query"})
    And accessed_at SHALL 被更新为当前时间

  Scenario: 检索不存在的条目
    Given 一个不存在的 UUID
    When 调用 memory.retrieve("s1", nonexistent_id)
    Then SHALL 返回 None

  Scenario: 删除记忆条目
    Given 一条记忆已存储
    When 调用 memory.delete("s1", entry_id)
    Then 再次 retrieve SHALL 返回 None
```

## Feature: LRU 淘汰

```gherkin
Feature: LRU 容量淘汰
  短期记忆 SHALL 使用 LRU 策略淘汰最久未访问的条目。

  Scenario: 达到容量上限淘汰最旧
    Given max_size=3，已有 [A, B, C]
    When 存储第 4 条 D
    Then A SHALL 被淘汰（最久未访问）
    And 记忆 SHALL 变为 [B, C, D]

  Scenario: 访问刷新淘汰优先级
    Given max_size=3，已有 [A, B, C]
    When retrieve A（刷新访问时间）
    And 存储第 4 条 D
    Then B SHALL 被淘汰（A 被刷新后变为最新）
    And 记忆 SHALL 变为 [A, C, D]
```

## Feature: 会话隔离

```gherkin
Feature: 会话隔离
  不同会话的记忆 SHALL 互不可见。

  Scenario: 会话隔离
    Given "session-001" 存储了 "记忆A"
    And "session-002" 存储了 "记忆B"
    When 在 "session-001" 中搜索
    Then SHALL 仅包含 "记忆A"

  Scenario: 清除会话记忆
    Given "session-001" 有 5 条记忆
    When 调用 memory.clear("session-001")
    Then "session-001" SHALL 无记忆
    And 其他会话 SHALL NOT 受影响
```
