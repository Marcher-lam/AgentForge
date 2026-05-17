# Delta Spec: Core Types & Interfaces

> Change: change-20260515-091942-core | Domain: types | Type: ADDED
> Status: Draft

---

## Feature: Agent State Enum

```gherkin
Feature: Agent 状态枚举定义
  系统定义 4 种合法 Agent 状态及其转换规则，所有子系统 MUST 使用此枚举。

  Scenario: 定义 4 种合法状态
    Given AgentState 枚举已定义
    Then 它 SHALL 包含 INIT, RUNNING, STOPPED, DESTROYED

  Scenario: 合法状态转换表
    Given AgentState 定义了合法转换表
    Then 以下转换 SHALL 合法:
      | from      | to        |
      | INIT      | RUNNING   |
      | RUNNING   | STOPPED   |
      | STOPPED   | RUNNING   |
      | STOPPED   | DESTROYED |
    And 以下转换 SHALL 非法:
      | from      | to        |
      | INIT      | DESTROYED |
      | DESTROYED | RUNNING   |
      | DESTROYED | STOPPED   |

  Scenario: DESTROYED 是终态
    Given Agent 处于 DESTROYED 状态
    Then 任何状态转换 MUST 抛出 AgentStateError
```

## Feature: Message Types

```gherkin
Feature: 消息数据结构
  系统定义 Agent 间通信的消息格式，所有消息 MUST 包含完整元数据。

  Scenario: Message 数据结构
    Given Message 数据类型已定义
    Then 它 SHALL 包含以下必填字段:
      | field     | type           |
      | id        | uuid.UUID      |
      | sender    | str            |
      | topic     | str            |
      | payload   | dict[str, Any] |
      | timestamp | datetime       |
    And 它 MAY 包含以下可选字段:
      | field    | type            |
      | reply_to | uuid.UUID | None |
      | metadata | dict[str, Any]  |

  Scenario: MessageType 枚举
    Given MessageType 枚举已定义
    Then 它 SHALL 包含 COMMAND, EVENT, QUERY, RESPONSE, ERROR

  Scenario: Message 不可变性
    Given Message 定义为不可变类型（frozen=True, slots=True）
    When 尝试修改 Message 实例的字段
    Then SHALL 抛出 FrozenInstanceError
```

## Feature: Protocol Interfaces

```gherkin
Feature: MessageBus Protocol 接口
  系统定义通信总线的抽象接口，具体实现 MUST 满足此契约。

  Scenario: MessageBus 异步方法签名
    Given MessageBus Protocol 使用 @runtime_checkable 定义
    Then 它 SHALL 声明以下异步方法:
      | method       | signature                                       |
      | publish      | async (topic: str, message: Message) -> None    |
      | subscribe    | async (topic: str, handler: Callable) -> str     |
      | unsubscribe  | async (subscription_id: str) -> None             |

  Scenario: 通配符 topic 匹配规则
    Given MessageBus 支持通配符订阅
    When 使用 topic "agent.*" 订阅
    Then SHALL 匹配 "agent.task", "agent.result"（单层）
    And SHALL NOT 匹配 "agent.task.sub"（多层）
    When 使用 topic "agent.**" 订阅
    Then SHALL 匹配 "agent.task", "agent.task.sub"（递归）
```

```gherkin
Feature: 异常层次结构
  系统定义分层异常，调用方 SHALL 可精确 catch 特定异常。

  Scenario: AgentForgeError 是所有框架异常的基类
    Given 所有框架异常继承自 AgentForgeError
    Then 调用方 SHALL 通过 catch AgentForgeError 捕获所有框架异常

  Scenario: Agent 异常层次
    Given AgentError 继承自 AgentForgeError
    Then AgentStateError, AgentInitError, AgentStopTimeoutError SHALL 继承自 AgentError

  Scenario: Bus 异常层次
    Given BusError 继承自 AgentForgeError
    Then BusConnectionError, MessageTimeoutError, MessageDecodeError, DeliveryError SHALL 继承自 BusError
```
