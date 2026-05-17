# Spec: Communication Bus (MessageBus)

> Phase: 1 (Core Skeleton) | Priority: P0 | Depends on: 00-core-types
> Type: ADDED
> Module: `agentforge/bus/`

---

## Overview

Agent 间通信总线，支持双模运行：进程内（异步框架.Queue）和跨进程（WebSocket）。通过抽象 MessageBus Protocol 实现模式切换。

---

## Feature: InProcessMessageBus - 基础发布订阅

```gherkin
Feature: 进程内消息发布
  作为 Agent
  我需要通过消息总线发布消息
  以便其他 Agent 可以接收并处理

  Background:
    Given 一个 InProcessMessageBus 实例

  Scenario: 发布单条消息
    Given topic "task.result" 已有订阅者
    When Agent 发布一条 Message 到 topic "task.result"
    Then 所有订阅该 topic 的 handler 应收到该 Message
    And Message 的 topic 应为 "task.result"
    And Message 的 sender 应为发送 Agent 的 ID

  Scenario: 向无订阅者的 topic 发布消息
    Given topic "orphan.topic" 没有订阅者
    When Agent 发布一条 Message 到 topic "orphan.topic"
    Then 消息应被静默丢弃
    And 不应抛出异常
```

```gherkin
Feature: 进程内消息订阅
  作为 Agent
  我需要订阅感兴趣的 topic
  以便接收该 topic 的所有消息

  Scenario: 订阅单个 topic
    Given 一个 InProcessMessageBus
    When 我调用 bus.subscribe("agent.task", my_handler)
    Then 应返回一个 subscription_id (UUID)
    And 后续发布到 "agent.task" 的消息应被路由到 my_handler

  Scenario: 多个订阅者同一 topic
    Given topic "broadcast" 有 3 个订阅者
    When 一条消息发布到 "broadcast"
    Then 3 个 handler 都应收到相同的消息

  Scenario: 同一 handler 订阅多个 topic
    Given 一个 handler
    When 它订阅了 "topic.a" 和 "topic.b"
    And 消息分别发布到 "topic.a" 和 "topic.b"
    Then handler 应收到两条消息，topic 分别匹配

  Scenario: 通配符订阅
    When 我调用 bus.subscribe("agent.*", my_handler)
    And 消息发布到 "agent.task"
    And 消息发布到 "agent.result"
    And 消息发布到 "system.info"
    Then my_handler 应收到 2 条消息（agent.task 和 agent.result）
    And 不应收到 system.info
```

```gherkin
Feature: 取消订阅
  作为 Agent
  我需要取消订阅不再关注的 topic
  以避免收到不需要的消息

  Scenario: 正常取消订阅
    Given 一个有效的 subscription_id
    When 我调用 bus.unsubscribe(subscription_id)
    Then 该 handler 不应再收到对应 topic 的消息

  Scenario: 取消不存在的订阅
    Given 一个不存在的 subscription_id
    When 我调用 bus.unsubscribe(subscription_id)
    Then 应静默返回，不抛异常
```

---

## Feature: InProcessMessageBus - 请求响应模式

```gherkin
Feature: 请求-响应 (RPC) 模式
  作为 Agent
  我需要发送请求并等待响应
  以实现同步交互模式

  Scenario: 成功的请求-响应
    Given Agent-B 订阅了 topic "rpc.compute"
    And Agent-B 的 handler 返回 {"result": 42}
    When Agent-A 调用 bus.request("rpc.compute", payload, timeout=5.0)
    Then Agent-A 应在 5 秒内收到 {"result": 42}

  Scenario: 请求超时
    Given topic "rpc.slow" 没有订阅者或订阅者不响应
    When Agent-A 调用 bus.request("rpc.slow", payload, timeout=1.0)
    Then 应抛出 MessageTimeoutError

  Scenario: 响应者抛出异常
    Given Agent-B 的 handler 抛出 ValueError("bad input")
    When Agent-A 调用 bus.request("rpc.compute", bad_payload)
    Then Agent-A 应收到一条 is_error=True 的响应消息
```

---

## Feature: WebSocketMessageBus

```gherkin
Feature: WebSocket 消息总线启动
  作为框架管理者
  我需要启动 WebSocket 消息总线服务
  以支持跨进程 Agent 通信

  Scenario: 启动 WebSocket 服务
    Given 一个 WebSocketMessageBus 配置了 host="127.0.0.1" port=8765
    When 我调用 bus.start_server()
    Then WebSocket 服务应在 ws://127.0.0.1:8765 上监听

  Scenario: Agent 连接到 WebSocket 总线
    Given WebSocket 服务已启动
    When 一个 Agent 调用 bus.connect("ws://127.0.0.1:8765")
    Then 连接应成功建立
    And Agent 应能通过 WebSocket 收发消息

  Scenario: 连接失败
    Given WebSocket 服务未启动
    When Agent 调用 bus.connect("ws://127.0.0.1:8765")
    Then 应抛出 BusConnectionError
```

```gherkin
Feature: WebSocket 消息传输
  作为跨进程 Agent
  我需要通过 WebSocket 收发消息
  以实现分布式通信

  Scenario: 跨进程 pub/sub
    Given 进程 A 的 Agent-1 连接到 WebSocket 总线
    And 进程 B 的 Agent-2 连接到同一总线
    And Agent-2 订阅了 topic "cross.task"
    When Agent-1 发布消息到 "cross.task"
    Then Agent-2 应在 1 秒内收到该消息

  Scenario: WebSocket 断线重连
    Given Agent 连接到 WebSocket 总线
    When 连接意外断开
    Then 应自动尝试重连（最多 3 次，间隔 2 秒）
    And 重连成功后，订阅关系应自动恢复

  Scenario: WebSocket 心跳
    Given Agent 已连接到 WebSocket 总线
    Then 每 30 秒应发送一次 ping
    And 如果 60 秒内未收到 pong，应触发重连
```

---

## Feature: 消息序列化

```gherkin
Feature: 消息编解码
  作为通信总线
  我需要将 Message 对象序列化/反序列化
  以支持跨进程传输

  Scenario: Message 序列化为 JSON
    Given 一条 Message 对象
    When 我调用 Message.to_json()
    Then 结果应为合法 JSON 字符串
    And 包含 id, sender, topic, payload, timestamp 字段
    And UUID 应序列化为字符串
    And datetime 应序列化为 ISO 8601 格式

  Scenario: JSON 反序列化为 Message
    Given 一条 Message 的 JSON 字符串
    When 我调用 Message.from_json(json_str)
    Then 结果应为 Message 对象
    And 所有字段类型正确（UUID、datetime 反序列化）

  Scenario: 无效 JSON 反序列化
    Given 一段非法 JSON 字符串
    When 我调用 Message.from_json(bad_json)
    Then 应抛出 MessageDecodeError
```

---

## Feature: 消息过滤与路由

```gherkin
Feature: 消息过滤器
  作为消息总线
  我需要在路由前过滤消息
  以支持细粒度的消息控制

  Scenario: 基于 sender 过滤
    Given Agent-B 订阅 "task" 时指定了 filter: sender != "agent-A"
    When agent-A 发布消息到 "task"
    Then Agent-B 不应收到该消息
    When agent-C 发布消息到 "task"
    Then Agent-B 应收到该消息

  Scenario: 基于 payload 字段过滤
    Given Agent-B 订阅 "task" 时指定了 filter: payload["priority"] == "high"
    When 发布一条 priority="low" 的消息到 "task"
    Then Agent-B 不应收到
    When 发布一条 priority="high" 的消息到 "task"
    Then Agent-B 应收到
```

---

## Acceptance Criteria

- [ ] InProcessMessageBus 和 WebSocketMessageBus 均实现 MessageBus Protocol
- [ ] 发布操作为 fire-and-forget（不阻塞发送者）
- [ ] 订阅 handler 执行异常不应影响其他订阅者或发布者
- [ ] WebSocket 消息使用 JSON 编码
- [ ] 通配符仅支持单层 `*`（不递归匹配）
- [ ] 所有异步操作使用 异步框架 API
- [ ] request 超时使用 `异步框架.move_on_after`
