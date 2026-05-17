# Delta Spec: In-Process Message Bus

> Change: change-20260515-091942-core | Domain: bus/inprocess | Type: ADDED
> Status: Draft

---

## Feature: 发布订阅

```gherkin
Feature: 进程内消息发布
  Agent 通过消息总线发布消息，fire-and-forget 语义。

  Scenario: 发布到有订阅者的 topic
    Given topic "task.result" 有 2 个订阅者
    When 发布一条 Message 到 "task.result"
    Then 2 个 handler SHALL 都收到该 Message
    And Message.topic SHALL 为 "task.result"

  Scenario: 发布到无订阅者的 topic
    Given topic "orphan" 没有订阅者
    When 发布消息到 "orphan"
    Then SHALL NOT 抛出异常（静默丢弃）

  Scenario: 同 topic 消息按顺序投递
    Given topic "ordered" 有 1 个订阅者
    When 依次发布消息 A、B、C
    Then handler SHALL 按顺序收到 A、B、C
```

```gherkin
Feature: 进程内消息订阅
  Agent 订阅感兴趣的 topic，支持通配符。

  Scenario: 订阅单个 topic
    When 调用 bus.subscribe("agent.task", handler)
    Then SHALL 返回 subscription_id (UUID 字符串)
    And 后续发布到 "agent.task" 的消息 SHALL 路由到 handler

  Scenario: 通配符 * 单层匹配
    When 调用 bus.subscribe("agent.*", handler)
    And 消息发布到 "agent.task"
    Then handler SHALL 收到该消息
    When 消息发布到 "agent.task.sub"
    Then handler SHALL NOT 收到该消息

  Scenario: 通配符 ** 递归匹配
    When 调用 bus.subscribe("agent.**", handler)
    And 消息发布到 "agent.task"
    And 消息发布到 "agent.task.sub"
    And 消息发布到 "agent.task.sub.deep"
    Then handler SHALL 收到全部 3 条消息
    When 消息发布到 "system.info"
    Then handler SHALL NOT 收到该消息

  Scenario: 取消订阅
    Given 一个有效的 subscription_id
    When 调用 bus.unsubscribe(subscription_id)
    Then 该 handler SHALL NOT 再收到对应 topic 的消息

  Scenario: 取消不存在的订阅
    Given 不存在的 subscription_id
    When 调用 bus.unsubscribe(subscription_id)
    Then SHALL NOT 抛出异常（幂等）
```

## Feature: 请求响应

```gherkin
Feature: request/response RPC 模式
  Agent 发送请求并等待响应，MUST 支持超时。

  Scenario: 成功的请求-响应
    Given Agent-B 订阅了 "rpc.compute" 且 handler 返回 {"result": 42}
    When Agent-A 调用 bus.request("rpc.compute", payload, timeout=5.0)
    Then Agent-A SHALL 在 5 秒内收到 {"result": 42}

  Scenario: 请求超时
    Given topic "rpc.slow" 无订阅者响应
    When Agent-A 调用 bus.request("rpc.slow", payload, timeout=1.0)
    Then SHALL 抛出 MessageTimeoutError
```

## Feature: 错误处理与背压

```gherkin
Feature: handler 异常隔离
  单个 handler 异常 SHALL NOT 影响其他 handler 和发布者。

  Scenario: handler 抛出异常
    Given topic "test" 有 2 个订阅者: handler_A 和 handler_B
    And handler_A 抛出 ValueError
    When 发布消息到 "test"
    Then handler_B SHALL 正常收到消息
    And SHALL 发布 "message.delivery_failed" 事件，包含原始消息和错误信息

  Scenario: handler 处理慢导致背压
    Given handler 使用有界队列，容量为 10
    And handler 处理速度跟不上，队列已满
    When 继续发布消息
    Then 队列中最旧的消息 SHALL 被丢弃
    And 新消息 SHALL 入队
```

## Feature: 消息序列化

```gherkin
Feature: 消息 JSON 编解码
  Message SHALL 支持 JSON 序列化/反序列化。

  Scenario: 序列化为 JSON
    Given 一条 Message 对象
    When 调用 Message.to_json()
    Then 结果 SHALL 为合法 JSON 字符串
    And UUID SHALL 序列化为字符串
    And datetime SHALL 序列化为 ISO 8601 格式

  Scenario: 从 JSON 反序列化
    Given 一条 Message 的 JSON 字符串
    When 调用 Message.from_json(json_str)
    Then SHALL 返回 Message 对象
    And UUID 和 datetime 字段类型 SHALL 正确

  Scenario: 非法 JSON
    Given 一段非法 JSON 字符串
    When 调用 Message.from_json(bad_json)
    Then SHALL 抛出 MessageDecodeError
```
