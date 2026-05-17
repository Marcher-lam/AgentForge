# Delta Spec: WebSocket Message Bus

> Change: change-20260515-091942-core | Domain: bus/websocket | Type: ADDED
> Status: Updated to reflect actual implementation

---

## Feature: WebSocket 服务启动

```gherkin
Feature: WebSocket 服务端
  WebSocketMessageBus 继承 InProcessMessageBus，提供跨进程通信。

  Scenario: 启动 WebSocket 服务
    Given WebSocketMessageBus 配置 host="0.0.0.0" port=8080
    When 调用 bus.start_server(host, port)
    Then WebSocket 服务 SHALL 在 ws://0.0.0.0:8080 监听
    And _running SHALL 设为 True

  Scenario: Agent 连接到总线
    Given WebSocket 服务已启动
    When Agent 调用 bus.connect("ws://host:port")
    Then 连接 SHALL 成功建立
    And SHALL 启动 _heartbeat_loop 协程

  Scenario: 连接失败
    Given WebSocket 服务未启动
    When Agent 调用 bus.connect("ws://host:port")
    Then SHALL 重试最多 3 次（_reconnect_attempts），间隔 2 秒
    When 全部失败
    Then SHALL 抛出 ConnectionError

  Scenario: 客户端处理
    Given 客户端连接到服务端
    When 发送 JSON {"subscribe": true, "topic": "task.a"}
    Then 服务端 SHALL 注册订阅（通过 subscribe 方法）
    And 消息 SHALL 通过 _send_to_client 转发
    When 发送 JSON {"message": ..., "topic": "..."}
    Then 服务端 SHALL 反序列化并 publish 到对应 topic
```

## Feature: 跨进程消息传输

```gherkin
Feature: 跨进程 pub/sub
  不同进程的 Agent 通过 WebSocket 通信。

  Scenario: 跨进程消息投递
    Given 进程 A 的 Agent-1 已连接到 WebSocket 总线
    And 进程 B 的 Agent-2 已连接到同一总线
    And Agent-2 已发送 subscribe 消息订阅 "cross.task"
    When Agent-1 通过 ws_publish 发布消息到 "cross.task"
    Then Agent-2 SHALL 收到该消息

  Scenario: 消息使用 JSON 编码传输
    Given WebSocket 连接已建立
    When 发送一条 Message
    Then WebSocket 帧 SHALL 为 JSON 格式 {"message": {...}, "topic": "..."}
    And 接收端 SHALL 正确反序列化为 Message 对象

  Scenario: 客户端断开清理
    Given 客户端已连接且有订阅
    When 客户端断开连接 (ConnectionClosed)
    Then 服务端 SHALL 清理该客户端的订阅
    And SHALL 从 _clients 和 _client_subs 中移除
```

## Feature: 断线重连

```gherkin
Feature: 断线重连
  WebSocket 连接断开后自动重连。

  Scenario: 自动重连
    Given Agent 已通过 connect() 连接到 WebSocket 总线
    When 连接意外断开
    Then SHALL 自动尝试重连，最多 3 次，间隔 2 秒

  Scenario: 重连全部失败
    Given Agent 连接断开
    When 连续 3 次重连均失败
    Then SHALL 抛出 ConnectionError

  Note: 订阅恢复 NOT_IMPLEMENTED — 重连成功后不会自动恢复之前的订阅关系。
  客户端需要重新发送 subscribe 消息。服务端不持久化订阅关系。
```

## Feature: 心跳

```gherkin
Feature: WebSocket 心跳保活
  连接通过心跳检测存活性。

  Scenario: 定期心跳
    Given Agent 已连接到 WebSocket 总线（通过 connect）
    Then 每 30 秒 SHALL 发送一次 ping（_heartbeat_interval）
    And 如果 60 秒内未收到 pong（_heartbeat_timeout），SHALL 退出心跳循环

  Scenario: 心跳失败触发日志
    Given 心跳 ping 超时
    Then SHALL 记录 warning 日志 "Heartbeat failed, triggering reconnect"
    And 心跳循环 SHALL 退出

  Note: 服务端心跳超时未显式实现 — 服务端不主动关闭不活跃的客户端连接。
  依赖 websockets 库的默认行为。
```

## Feature: 优雅关机

```gherkin
Feature: 优雅关机
  NOT_IMPLEMENTED — 没有 SIGINT/SIGTERM 信号处理。

  WebSocketMessageBus 提供 stop_server() 方法手动关闭，但没有：
  - SIGINT/SIGTERM 信号拦截
  - 自动对每个 Agent 调用 stop() 和 destroy()
  - 关机超时保护
  - 强制退出机制

  infra/shutdown.py 模块可能提供部分关机逻辑，但与 WebSocketMessageBus 无集成。
```
