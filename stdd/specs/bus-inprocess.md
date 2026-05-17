# Delta Spec: In-Process Message Bus

> Change: change-20260515-091942-core | Domain: bus/inprocess | Type: ADDED
> Status: Updated to reflect actual implementation

---

## Feature: 发布订阅

```gherkin
Feature: 进程内消息发布
  Agent 通过 InProcessMessageBus 发布消息。

  Scenario: 发布到有订阅者的 topic
    Given topic "task.result" 有 2 个订阅者
    When 发布一条 Message 到 "task.result"
    Then 2 个 handler SHALL 都收到该 Message
    And Message.topic SHALL 为 "task.result"

  Scenario: 发布到无订阅者的 topic
    Given topic "orphan" 没有订阅者
    When 发布消息到 "orphan"
    Then SHALL NOT 抛出异常（_find_matching_topics 返回空列表，循环不执行）
```

```gherkin
Feature: 进程内消息订阅
  Agent 订阅感兴趣的 topic，支持通配符。

  Scenario: 订阅单个 topic
    When 调用 bus.subscribe("agent.task", handler)
    Then SHALL 返回 subscription_id (UUID 字符串)
    And SHALL 为该 subscription 创建 asyncio.Queue (maxsize=queue_capacity)
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
    And 对应的 Queue SHALL 被移除

  Scenario: 取消不存在的订阅
    Given 不存在的 subscription_id
    When 调用 bus.unsubscribe(subscription_id)
    Then SHALL NOT 抛出异常（幂等，早期返回）
```

## Feature: 请求响应

```gherkin
Feature: request/response RPC 模式
  Agent 发送请求并等待响应，支持超时。

  Scenario: 成功的请求-响应
    Given Agent-B 订阅了 "rpc.compute" 且会调用 bus.respond(correlation_id, response)
    When Agent-A 调用 bus.request("rpc.compute", message, timeout=5.0)
    Then Agent-A SHALL 在 5 秒内收到响应

  Scenario: 请求超时
    Given topic "rpc.slow" 无订阅者响应
    When Agent-A 调用 bus.request("rpc.slow", message, timeout=1.0)
    Then SHALL 抛出 RpcTimeout 异常
    And 错误信息 SHALL 包含 topic 和 timeout 值
    And pending Future SHALL 从 _rpc_pending 中移除

  Scenario: respond 解析 pending 请求
    Given 一个 pending RPC Future
    When 调用 bus.respond(correlation_id, response_message)
    Then Future SHALL 被 set_result(response)
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
    And 异常 SHALL 被 try/except 静默捕获（pass）

  Scenario: 队列满时背压处理
    Given handler 使用有界队列，容量为 queue_capacity
    And handler 处理速度跟不上，队列已满
    When 继续发布消息
    Then SHALL 调用 _notify_delivery_failed
    And 最旧的消息 SHALL 被丢弃（_drop_oldest: queue.get_nowait()）
    And 新消息 SHALL 入队
    And SHALL 生成 MessageType.DELIVERY_FAILED 消息发送给 handler
```

## Feature: 消息序列化

```gherkin
Feature: 消息 JSON 编解码
  Message 支持 JSON 序列化/反序列化（dict 格式）。

  Scenario: 序列化为 JSON dict
    Given 一条 Message 对象
    When 调用 Message.to_json()
    Then 结果 SHALL 为 JSON 兼容的 dict（非字符串）
    And UUID SHALL 序列化为字符串
    And datetime SHALL 序列化为 ISO 8601 格式
    And correlation_id 为 None 时 SHALL 序列化为 null

  Scenario: 从 JSON dict 反序列化
    Given 一条 Message 的 JSON dict
    When 调用 Message.from_json(data)
    Then SHALL 返回 Message 对象
    And UUID 字段 SHALL 正确还原
    And datetime SHALL 从 ISO 格式解析
    And MessageType SHALL 从字符串值还原

  Note: 原 spec 提到 "JSON 字符串" 和 MessageDecodeError，
  实际实现 to_json() 返回 dict（非字符串），from_json() 接受 dict（非字符串）。
  没有独立的 MessageDecodeError — 反序列化失败会抛出标准 Python 异常（KeyError, ValueError 等）。
```

## Feature: MessageType Enum

```gherkin
Feature: 消息类型枚举
  MessageType 定义所有支持的消息类型。

  Scenario: 枚举值
    Then MessageType SHALL 包含：
      | 值              | 字符串           |
      | TEXT            | "text"           |
      | JSON            | "json"           |
      | BINARY          | "binary"         |
      | TOOL_CALL       | "tool_call"      |
      | TOOL_RESULT     | "tool_result"    |
      | SYSTEM          | "system"         |
      | DELIVERY_FAILED | "delivery_failed"|
```
