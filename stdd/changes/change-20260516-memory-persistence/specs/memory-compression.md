# Delta Spec: Memory Compression

> Change: change-20260516-memory-persistence | Domain: memory/compression | Type: ADDED
> Status: Draft

---

## Feature: 长期记忆压缩

```gherkin
Feature: 长期记忆压缩
  系统 SHALL 支持对长期记忆进行摘要/聚合压缩，减少存储量同时保留关键信息。

  Scenario: 时间窗口聚合压缩
    Given 长期记忆中有 50 条记忆，时间跨度 7 天
    And 压缩策略为 "时间窗口聚合"，窗口大小 = 1 天
    When 调用 memory.compress(session_id="s1", strategy="time_window", window_days=1)
    Then 每个窗口内的记忆 SHALL 被聚合为 1 条摘要
    And 原始条目 SHALL 被标记为已压缩
    And 压缩后总条目数 SHALL 不超过 7 条（每天一条摘要）

  Scenario: 压缩后信息保留率
    Given 长期记忆中有 100 条关于 "用户偏好" 的记忆
    When 执行压缩操作
    Then 摘要 SHALL 包含原始记忆中的关键实体和关系
    And 信息保留率 SHALL 大于 80%（通过关键信息点数量衡量）

  Scenario: 空记忆压缩
    Given 长期记忆中无任何条目
    When 调用 memory.compress(session_id="s1")
    Then SHALL 返回空列表（无压缩操作执行）
    And SHALL NOT 抛出异常
```

## Feature: 压缩策略选择

```gherkin
Feature: 可插拔压缩策略
  压缩策略 SHALL 可插拔，支持自定义策略。

  Scenario: 内置摘要压缩策略
    Given 配置 strategy="summary"
    When 执行压缩
    Then SHALL 使用内置摘要策略（基于内容语义聚合）

  Scenario: 自定义压缩策略
    Given 注册了一个自定义压缩策略 "custom_strategy"
    When 调用 memory.compress(session_id="s1", strategy="custom_strategy")
    Then SHALL 使用自定义策略执行压缩

  Scenario: 无效策略名称
    Given 未注册的策略名 "nonexistent"
    When 调用 memory.compress(session_id="s1", strategy="nonexistent")
    Then SHALL 抛出策略未找到异常
```
