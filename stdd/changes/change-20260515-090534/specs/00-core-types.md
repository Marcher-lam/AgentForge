# Spec: Core Types & Interfaces

> Phase: 1 (Core Skeleton) | Priority: P0 | Depends on: none
> Type: ADDED
> Module: `agentforge/types/`

---

## Overview

定义框架全局共享的类型、Protocol 接口和枚举。所有子系统依赖此模块，不含业务逻辑。

---

## Feature: Agent State Enum

```gherkin
Feature: Agent 状态枚举
  作为框架开发者
  我需要定义 Agent 的合法状态和转换规则
  以确保所有子系统对状态的理解一致

  Scenario: 定义 4 种合法状态
    Given AgentState 枚举已定义
    Then 它包含以下值
      | state    | description         |
      | INIT     | 初始化中            |
      | RUNNING  | 运行中              |
      | STOPPED  | 已停止              |
      | DESTROYED| 已销毁              |

  Scenario: 状态转换规则验证
    Given AgentState 定义了合法转换表
    Then 以下转换是合法的
      | from      | to        |
      | INIT      | RUNNING   |
      | RUNNING   | STOPPED   |
      | STOPPED   | RUNNING   |
      | STOPPED   | DESTROYED |
    And 以下转换是非法的
      | from      | to        |
      | INIT      | DESTROYED |
      | DESTROYED | RUNNING   |
      | DESTROYED | STOPPED   |
```

## Feature: Message Types

```gherkin
Feature: 消息类型定义
  作为框架开发者
  我需要定义 Agent 间通信的消息结构
  以确保通信总线的数据格式统一

  Scenario: Message 数据结构
    Given Message 数据类型已定义
    Then 它包含以下必填字段
      | field      | type                | description          |
      | id         | UUID                | 消息唯一标识          |
      | sender     | str                 | 发送者 Agent ID       |
      | topic      | str                 | 消息主题              |
      | payload    | dict[str, Any]      | 消息负载              |
      | timestamp  | datetime            | 发送时间              |
    And 它包含以下可选字段
      | field      | type                | description          |
      | reply_to   | UUID | None         | 回复目标消息 ID       |
      | metadata   | dict[str, Any]      | 扩展元数据            |

  Scenario: MessageType 枚举
    Given MessageType 枚举已定义
    Then 它包含以下值
      | type       | description         |
      | COMMAND    | 命令消息             |
      | EVENT      | 事件消息             |
      | QUERY      | 查询消息             |
      | RESPONSE   | 响应消息             |
      | ERROR      | 错误消息             |
```

## Feature: MCP Protocol Types

```gherkin
Feature: MCP 协议类型
  作为框架开发者
  我需要定义 MCP 协议相关的数据结构
  以确保工具注册和调用的类型安全

  Scenario: ToolDescriptor 数据结构
    Given ToolDescriptor 数据类型已定义
    Then 它包含以下字段
      | field        | type               | description          |
      | name         | str                | 工具名称              |
      | description  | str                | 工具描述              |
      | input_schema | dict[str, Any]     | JSON Schema 输入定义  |
      | output_schema| dict[str, Any]     | JSON Schema 输出定义  |
      | annotations  | dict[str, Any]     | MCP annotations      |

  Scenario: ToolCallRequest 数据结构
    Given ToolCallRequest 数据类型已定义
    Then 它包含以下字段
      | field      | type               | description          |
      | id         | str                | 请求 ID               |
      | method     | str                | 方法名 "tools/call"   |
      | params     | dict[str, Any]     | 调用参数              |

  Scenario: ToolCallResult 数据结构
    Given ToolCallResult 数据类型已定义
    Then 它包含以下字段
      | field      | type               | description          |
      | id         | str                | 对应请求 ID           |
      | result     | Any                | 调用结果              |
      | is_error   | bool               | 是否为错误            |
      | error      | dict | None        | 错误详情              |
```

## Feature: Skill Types

```gherkin
Feature: Skill 类型定义
  作为框架开发者
  我需要定义 Skill 相关的数据结构
  以支持 Skill 的注册、发现和依赖解析

  Scenario: SkillDescriptor 数据结构
    Given SkillDescriptor 数据类型已定义
    Then 它包含以下字段
      | field         | type             | description          |
      | name          | str              | Skill 名称            |
      | version       | str              | 版本号                |
      | description   | str              | 描述                  |
      | dependencies  | list[str]        | 依赖的其他 Skill      |
      | tags          | list[str]        | 分类标签              |
      | entry_point   | str              | 入口函数路径          |
```

## Feature: Memory Types

```gherkin
Feature: 记忆类型定义
  作为框架开发者
  我需要定义记忆条目的数据结构
  以支持短期、长期和向量检索

  Scenario: MemoryEntry 数据结构
    Given MemoryEntry 数据类型已定义
    Then 它包含以下字段
      | field       | type              | description          |
      | id          | UUID              | 条目唯一标识          |
      | content     | str               | 记忆内容              |
      | metadata    | dict[str, Any]    | 元数据                |
      | embedding   | list[float] | None| 向量嵌入              |
      | created_at  | datetime          | 创建时间              |
      | accessed_at | datetime          | 最后访问时间          |

  Scenario: MemoryType 枚举
    Given MemoryType 枚举已定义
    Then 它包含以下值
      | type       | description         |
      | SHORT_TERM | 短期记忆（会话级）    |
      | LONG_TERM  | 长期记忆（跨会话）    |
      | VECTOR     | 向量记忆（嵌入检索）  |
```

## Feature: Protocol Interfaces

```gherkin
Feature: 核心协议接口
  作为框架开发者
  我需要定义各子系统的 Protocol 接口
  以实现依赖反转和松耦合

  Scenario: MessageBus Protocol
    Given MessageBus Protocol 已定义
    Then 它声明以下异步方法
      | method                    | signature                                    |
      | publish                   | async (topic: str, message: Message) -> None |
      | subscribe                 | async (topic: str, handler: Callable) -> str  |
      | unsubscribe               | async (subscription_id: str) -> None          |

  Scenario: ToolRegistry Protocol
    Given ToolRegistry Protocol 已定义
    Then 它声明以下异步方法
      | method                    | signature                                    |
      | register                  | async (descriptor: ToolDescriptor) -> None    |
      | unregister                | async (name: str) -> None                     |
      | list_tools                | async () -> list[ToolDescriptor]              |
      | call_tool                 | async (name: str, params: dict) -> ToolCallResult |

  Scenario: SkillRegistry Protocol
    Given SkillRegistry Protocol 已定义
    Then 它声明以下异步方法
      | method                    | signature                                    |
      | register                  | async (descriptor: SkillDescriptor) -> None   |
      | discover                  | async (tags: list[str] | None) -> list[SkillDescriptor] |
      | resolve_dependencies       | async (name: str) -> list[str]               |
      | execute                   | async (name: str, context: dict) -> Any       |

  Scenario: MemoryStore Protocol
    Given MemoryStore Protocol 已定义
    Then 它声明以下异步方法
      | method                    | signature                                    |
      | store                     | async (entry: MemoryEntry) -> UUID            |
      | retrieve                  | async (id: UUID) -> MemoryEntry | None        |
      | search                    | async (query: str, top_k: int) -> list[MemoryEntry] |
      | delete                    | async (id: UUID) -> None                      |
```

---

## Acceptance Criteria

- [ ] 所有数据类型使用不可变定义（frozen, slots）确保不可变
- [ ] 所有 Protocol 使用 `@runtime_checkable`
- [ ] 所有公共类型导出自 `agentforge.types.__all__`
- [ ] UUID 字段使用 `uuid.UUID` 类型
- [ ] datetime 字段使用 UTC 时区，类型为 `datetime`
