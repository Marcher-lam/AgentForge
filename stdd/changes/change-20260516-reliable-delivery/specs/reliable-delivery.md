# Delta Spec: Reliable Delivery

> Change: change-20260516-reliable-delivery | Domain: bus/delivery | Type: MODIFIED
> Status: Fixed

---

## Feature: 背压投递

```gherkin
Feature: 消息背压投递
  发布者 SHALL 使用 await queue.put 而非 put_nowait，确保消息不被静默丢弃。

  Scenario: 队列满时背压等待
    Given queue_capacity=2，sync handler
    When 并发发布 20 条消息
    Then 所有消息 SHALL 最终被投递（发布者等待队列有空位）

  Scenario: 投递顺序保持
    Given 一个订阅者和 20 条有序消息
    When 按顺序发布
    Then 投递顺序 SHALL 与发布顺序一致
```

## Feature: 异常隔离

```gherkin
Feature: Handler 异常隔离
  单条消息的 handler 异常 SHALL NOT 阻断后续消息投递。

  Scenario: Handler 抛异常后后续消息正常投递
    Given handler 在第 2 条消息时抛出 ValueError
    When 发布 5 条消息
    Then 第 3、4、5 条消息 SHALL 正常投递

  Scenario: Async handler 异常隔离
    Given async handler 在第 3 条消息时抛出 RuntimeError
    When 发布 5 条消息
    Then 第 4、5 条消息 SHALL 正常投递
```

## Feature: 投递保证

```gherkin
Feature: 至少一次投递
  所有发布的消息 SHALL 至少到达每个匹配的订阅者一次。

  Scenario: 多订阅者投递保证
    Given 2 个订阅者订阅同一 topic
    When 发布 30 条消息
    Then 每个订阅者 SHALL 收到恰好 30 条消息
```
