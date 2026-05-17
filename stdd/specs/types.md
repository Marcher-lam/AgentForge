# Delta Spec: Core Types & Interfaces

> Change: change-20260515-091942-core | Domain: types | Type: ADDED
> Status: Draft

---

## Feature: Agent State Enum

```gherkin
Feature: AgentState 枚举定义（5 状态）
  系统定义 5 种合法 Agent 状态及其转换规则，所有子系统 MUST 使用此枚举。

  Scenario: 定义 5 种合法状态
    Given AgentState 枚举已定义
    Then 它 SHALL 包含:
      | 枚举值       | 字符串值      |
      | CREATED     | "created"    |
      | INITIALIZED | "initialized" |
      | RUNNING     | "running"    |
      | STOPPED     | "stopped"    |
      | DESTROYED   | "destroyed"  |

  Scenario: VALID_TRANSITIONS 转换表
    Given VALID_TRANSITIONS 字典已定义
    Then 以下转换 SHALL 合法:
      | from        | to                           |
      | CREATED     | {INITIALIZED, DESTROYED}     |
      | INITIALIZED | {RUNNING, DESTROYED}         |
      | RUNNING     | {STOPPED, DESTROYED}         |
      | STOPPED     | {RUNNING, DESTROYED}         |
      | DESTROYED   | {} (空集合)                    |

  Scenario: is_valid_transition 辅助函数
    Given is_valid_transition 函数
    When 调用 is_valid_transition(AgentState.CREATED, AgentState.INITIALIZED)
    Then SHALL 返回 True
    When 调用 is_valid_transition(AgentState.CREATED, AgentState.RUNNING)
    Then SHALL 返回 False
    When 调用 is_valid_transition(AgentState.DESTROYED, AgentState.RUNNING)
    Then SHALL 返回 False

  Scenario: DESTROYED 是终态
    Given Agent 处于 DESTROYED 状态
    Then VALID_TRANSITIONS[DESTROYED] SHALL 为空集合
    And 任何状态转换 MUST 抛出 InvalidStateTransition
```

## Feature: MessageType Enum

```gherkin
Feature: MessageType 枚举定义
  系统定义 7 种消息类型。

  Scenario: 定义 7 种消息类型
    Given MessageType 枚举已定义
    Then 它 SHALL 包含:
      | 枚举值           | 字符串值          | 用途              |
      | TEXT            | "text"          | 文本消息           |
      | JSON            | "json"          | JSON 结构化消息    |
      | BINARY          | "binary"        | 二进制消息         |
      | TOOL_CALL       | "tool_call"     | 工具调用请求       |
      | TOOL_RESULT     | "tool_result"   | 工具调用结果       |
      | SYSTEM          | "system"        | 系统消息           |
      | DELIVERY_FAILED | "delivery_failed" | 投递失败通知    |
```

## Feature: Message Data Structure

```gherkin
Feature: Message 不可变数据类
  Message 是 frozen dataclass with slots，支持 JSON 序列化。

  Scenario: Message 必填字段
    Given Message 数据类型已定义
    Then 它 SHALL 包含以下字段:
      | field           | type              | default             |
      | topic           | str               | (必填)              |
      | sender_id       | uuid.UUID         | (必填)              |
      | message_type    | MessageType       | (必填)              |
      | payload         | dict[str, Any]    | field(default_factory=dict) |
      | message_id      | uuid.UUID         | field(default_factory=uuid.uuid4) |
      | timestamp       | datetime          | field(default_factory=utcnow) |
      | correlation_id  | uuid.UUID | None  | None                |

  Scenario: Message 不可变性
    Given Message 定义为 frozen=True, slots=True
    When 尝试修改 Message 实例的字段
    Then SHALL 抛出 FrozenInstanceError

  Scenario: to_json 序列化
    Given Message 实例
    When 调用 msg.to_json()
    Then SHALL 返回 dict:
      | key            | value 格式              |
      | message_id     | str(uuid)               |
      | topic          | str                     |
      | message_type   | str (enum value)        |
      | sender_id      | str(uuid)               |
      | payload        | dict                    |
      | timestamp      | ISO format string       |
      | correlation_id | str(uuid) or None       |

  Scenario: from_json 反序列化
    Given JSON dict 数据
    When 调用 Message.from_json(data)
    Then SHALL 还原为 Message 实例
    And message_id, sender_id, correlation_id SHALL 还原为 uuid.UUID
    And timestamp SHALL 还原为 datetime
    And message_type SHALL 还原为 MessageType 枚举
```

## Feature: Protocol Interfaces

```gherkin
Feature: InProcessMessageBus 接口
  InProcessMessageBus 提供异步 pub/sub、RPC 和背压机制。

  Scenario: pub/sub 方法签名
    Given InProcessMessageBus 实例
    Then 它 SHALL 暴露以下异步方法:
      | method       | signature                                       |
      | subscribe    | async (topic: str, handler: Callable) -> str    |
      | unsubscribe  | async (subscription_id: str) -> None            |
      | publish      | async (topic: str, message: Message) -> None    |
      | request      | async (topic: str, message: Message, timeout: float) -> Message |
      | respond      | async (correlation_id: str, response: Message) -> None |

  Scenario: 通配符 topic 匹配规则
    Given topic_matches 函数支持通配符
    When pattern="agent.*" 且 topic="agent.task"
    Then SHALL 匹配（单层通配符）
    When pattern="agent.*" 且 topic="agent.task.sub"
    Then SHALL NOT 匹配（多层）
    When pattern="agent.**" 且 topic="agent.task.sub"
    Then SHALL 匹配（递归通配符）
    When pattern="agent.**" 且 topic="agent.task"
    Then SHALL 匹配（递归包含单层）

  Scenario: 背压机制
    Given InProcessMessageBus(queue_capacity=1000)
    And 订阅者队列已满
    When publish 消息
    Then SHALL 丢弃最旧消息
    And SHALL 向 handler 发送 MessageType.DELIVERY_FAILED 消息

  Scenario: RPC 请求-响应
    Given InProcessMessageBus 实例
    When 调用 request(topic, message, timeout=5.0)
    Then SHALL 发布消息并等待响应
    When 超时
    Then SHALL 抛出 RpcTimeout

  Scenario: 处理器隔离
    Given handler 抛出异常
    When _deliver 调用 handler
    Then 异常 SHALL 被捕获并静默忽略
    And SHALL NOT 影响其他消息投递
```

```gherkin
Feature: WebSocketMessageBus 接口
  WebSocketMessageBus 继承 InProcessMessageBus，添加 WebSocket 传输层。

  Scenario: 服务器模式
    Given WebSocketMessageBus 实例
    When 调用 start_server(host="0.0.0.0", port=8080)
    Then SHALL 启动 WebSocket 服务器
    And 客户端连接后 SHALL 处理 subscribe 和 publish 消息

  Scenario: 客户端重连
    Given WebSocketMessageBus 配置 reconnect_attempts=3, reconnect_interval=2.0
    When 调用 connect(url)
    Then SHALL 尝试连接最多 3 次
    And 每次失败 SHALL 等待 2 秒
    And 全部失败 SHALL 抛出 ConnectionError

  Scenario: 订阅不持久化（NOT IMPLEMENTED）
    Given WebSocket 客户端已订阅 topic
    When 连接断开并重连
    Then 订阅 SHALL NOT 自动恢复
    And 需要客户端重新发送 subscribe 消息

  Scenario: 心跳机制
    Given heartbeat_interval=30.0, heartbeat_timeout=60.0
    When 连接建立
    Then SHALL 启动心跳循环
    And 每 30 秒 SHALL 发送 ping
    And ping 超时 60 秒 SHALL 触发重连
```

## Feature: Exception Hierarchy

```gherkin
Feature: 分层异常结构
  系统定义分层异常，调用方 SHALL 可精确 catch 特定异常。

  Scenario: AgentForgeError 是所有框架异常的基类
    Given 所有框架异常继承自 AgentForgeError
    Then 调用方 SHALL 通过 catch AgentForgeError 捕获所有框架异常

  Scenario: Agent 异常层次
    Given AgentError 继承自 AgentForgeError
    Then 以下异常 SHALL 继承自 AgentError:
      | 异常类                    | 说明                        |
      | InvalidStateTransition   | 非法状态转换，含 from_state/to_state 属性 |
      | AgentInitFailed          | 初始化失败（不可重试）       |

  Scenario: Bus 异常层次
    Given BusError 继承自 AgentForgeError
    Then 以下异常 SHALL 继承自 BusError:
      | 异常类                 | 说明                    |
      | SubscriptionNotFound  | 取消订阅时 ID 不存在     |
      | RpcTimeout            | RPC 请求超时            |

  Scenario: Config 异常
    Given ConfigError 继承自 AgentForgeError
    Then ConfigError SHALL 用于配置相关错误
```
