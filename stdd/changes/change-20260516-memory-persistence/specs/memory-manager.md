# Delta Spec: Memory Manager

> Change: change-20260516-memory-persistence | Domain: memory/manager | Type: ADDED
> Status: Draft

---

## Feature: 统一门面

```gherkin
Feature: MemoryManager 统一门面
  系统 SHALL 提供 MemoryManager 作为三层记忆的统一入口，支持智能路由和 promote 操作。

  Scenario: 智能路由存储
    Given MemoryManager 实例，配置了短期、长期、向量三层
    When 调用 manager.store(session_id="s1", content="内容", memory_type=SHORT_TERM)
    Then SHALL 存储到短期记忆层
    When 调用 manager.store(session_id="s1", content="内容", memory_type=LONG_TERM)
    Then SHALL 存储到长期记忆层
    When 调用 manager.store(session_id="s1", content="内容", memory_type=VECTOR)
    Then SHALL 存储到向量记忆层

  Scenario: 统一搜索跨层检索
    Given 短期记忆存储了 "会话上下文A"
    And 长期记忆存储了 "用户偏好B"
    And 向量记忆存储了 "相关知识C"
    When 调用 manager.search(session_id="s1", query="用户偏好", top_k=5)
    Then 结果 SHALL 包含来自不同层的匹配
    And 每条结果 SHALL 包含 source 字段标识来源层
```

## Feature: 记忆提升 (Promote)

```gherkin
Feature: 记忆层间提升
  MemoryManager SHALL 支持将记忆从低层提升到高层。

  Scenario: 短期提升到长期
    Given 短期记忆有一条条目 entry_id
    When 调用 manager.promote(session_id="s1", entry_id=entry_id, target=LONG_TERM)
    Then 条目 SHALL 存在于长期记忆
    And 短期记忆中的原始条目 SHALL 被保留（不删除）

  Scenario: 长期提升到向量
    Given 长期记忆有一条条目 entry_id
    When 调用 manager.promote(session_id="s1", entry_id=entry_id, target=VECTOR)
    Then 条目 SHALL 存在于向量记忆
    And 长期记忆中的原始条目 SHALL 被保留

  Scenario: 提升失败原子性
    Given 长期记忆有一条条目 entry_id
    And 目标层写入失败（如存储异常）
    When 调用 manager.promote(session_id="s1", entry_id=entry_id, target=VECTOR)
    Then SHALL 抛出异常
    And SHALL NOT 在目标层留下部分数据
```

## Feature: 统一删除与清除

```gherkin
Feature: 统一删除与清除
  MemoryManager SHALL 支持跨层删除和清除操作。

  Scenario: 跨层删除
    Given 一个 entry_id 同时存在于短期和长期记忆
    When 调用 manager.delete(session_id="s1", entry_id=entry_id)
    Then 所有层中的该条目 SHALL 被删除

  Scenario: 清除会话全部记忆
    Given session "s1" 在三层中各有若干条目
    When 调用 manager.clear(session_id="s1")
    Then 所有三层中该会话的记忆 SHALL 被清除
    And 其他会话 SHALL NOT 受影响
```
