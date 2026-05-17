# Delta Spec: WebSocket Message Bus

> Change: change-20260515-091942-core | Domain: bus/websocket | Type: ADDED
> Status: Draft

---

## Feature: WebSocket 服务启动

```gherkin
Feature: WebSocket 服务端
  框架 SHALL 提供 WebSocket 消息总线服务，支持跨进程通信。

  Scenario: 启动 WebSocket 服务
    Given WebSocketMessageBus 配置 host="127.0.0.1" port=8765
    When 调用 bus.start_server()
    Then WebSocket 服务 SHALL 在 ws://127.0.0.1:8765 监听

  Scenario: Agent 连接到总线
    Given WebSocket 服务已启动
    When Agent 调用 bus.connect("ws://127.0.0.1:8765")
    Then 连接 SHALL 成功建立
    And Agent SHALL 可通过 WebSocket 收发消息

  Scenario: 连接失败
    Given WebSocket 服务未启动
    When Agent 调用 bus.connect("ws://127.0.0.1:8765")
    Then SHALL 抛出 BusConnectionError
```

## Feature: 跨进程消息传输

```gherkin
Feature: 跨进程 pub/sub
  不同进程的 Agent SHALL 可通过 WebSocket 通信。

  Scenario: 跨进程消息投递
    Given 进程 A 的 Agent-1 已连接到 WebSocket 总线
    And 进程 B 的 Agent-2 已连接到同一总线
    And Agent-2 订阅了 "cross.task"
    When Agent-1 发布消息到 "cross.task"
    Then Agent-2 SHALL 收到该消息
    And 端到端延迟（localhost）SHALL < 50ms

  Scenario: 消息使用 JSON 编码传输
    Given WebSocket 连接已建立
    When 发送一条 Message
    Then WebSocket 帧 SHALL 为 JSON 格式
    And 接收端 SHALL 正确反序列化为 Message 对象
```

## Feature: 断线重连

```gherkin
Feature: 断线重连与订阅恢复
  WebSocket 连接断开后 SHALL 自动重连并恢复订阅。

  Scenario: 自动重连
    Given Agent 已连接到 WebSocket 总线
    When 连接意外断开
    Then SHALL 自动尝试重连，最多 3 次，间隔 2 秒

  Scenario: 服务端持久化订阅关系
    Given Agent 订阅了 "task.a" 和 "task.b"
    And 服务端已持久化订阅关系
    When Agent 断线后重连成功
    Then 订阅关系 SHALL 自动恢复
    And Agent SHALL 继续收到 "task.a" 和 "task.b" 的消息
    And Agent SHALL NOT 需要重新调用 subscribe

  Scenario: 重连全部失败
    Given Agent 连接断开
    When 连续 3 次重连均失败
    Then SHALL 触发 "bus.connection_lost" 事件
```

## Feature: 心跳

```gherkin
Feature: WebSocket 心跳保活
  连接 SHALL 通过心跳检测存活性。

  Scenario: 定期心跳
    Given Agent 已连接到 WebSocket 总线
    Then 每 30 秒 SHALL 发送一次 ping
    And 如果 60 秒内未收到 pong，SHALL 触发重连

  Scenario: 心跳超时
    Given 服务端 60 秒内未收到 Agent 的 ping
    Then 服务端 SHALL 关闭该连接
```

## Feature: 优雅关机

```gherkin
Feature: SIGINT/SIGTERM 优雅关机
  框架 SHALL 拦截系统信号并优雅关闭所有 Agent。

  Scenario: SIGINT 触发优雅关机
    Given 运行中的 Agent 列表 [Agent-A, Agent-B]
    When 收到 SIGINT 信号
    Then SHALL 先对每个 Agent 调用 stop()
    And 然后对每个 Agent 调用 destroy()
    And WebSocket 服务 SHALL 关闭
    And 所有资源 SHALL 被释放

  Scenario: SIGTERM 触发优雅关机
    Given 运行中的 Agent 列表
    When 收到 SIGTERM 信号
    Then 行为 SHALL 与 SIGINT 一致

  Scenario: 关机超时保护
    Given 优雅关机超时设置为 10 秒
    And Agent 的 stop 需要 15 秒
    When 触发优雅关机
    Then 10 秒后 SHALL 强制退出
```
