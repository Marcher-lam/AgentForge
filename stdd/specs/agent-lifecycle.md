# Delta Spec: Agent Lifecycle

> Change: change-20260515-091942-core | Domain: agent | Type: ADDED
> Status: Draft

---

## Feature: Agent 创建

```gherkin
Feature: Agent 实例创建
  开发者创建 Agent 实例，初始状态 MUST 为 CREATED。

  Scenario: 指定 ID 和 name 创建
    When 使用 agent_id=<UUID> 和 name="测试" 创建 AgentBase 子类实例
    Then Agent.agent_id SHALL 为指定的 UUID
    And Agent.name SHALL 为 "测试"
    And Agent.state SHALL 为 AgentState.CREATED

  Scenario: 自动生成 ID
    When 仅指定 name 创建 Agent（省略 agent_id）
    Then Agent.agent_id SHALL 为自动生成的 UUID
    And Agent.name SHALL 为给定值
    And Agent.state SHALL 为 AgentState.CREATED

  Scenario: AgentBase 是抽象类
    Given AgentBase 定义了 4 个抽象方法: _on_init, _on_run, _on_stop, _on_destroy
    When 尝试直接实例化 AgentBase
    Then SHALL 抛出 TypeError（无法实例化抽象类）
```

## Feature: Agent 状态模型

```gherkin
Feature: 5 状态生命周期
  Agent 具有 5 种状态: CREATED, INITIALIZED, RUNNING, STOPPED, DESTROYED。

  Scenario: 合法状态转换表
    Given AgentState 定义了 VALID_TRANSITIONS 转换表
    Then 以下转换 SHALL 合法:
      | from        | to          |
      | CREATED     | INITIALIZED |
      | CREATED     | DESTROYED   |
      | INITIALIZED | RUNNING     |
      | INITIALIZED | DESTROYED   |
      | RUNNING     | STOPPED     |
      | RUNNING     | DESTROYED   |
      | STOPPED     | RUNNING     |
      | STOPPED     | DESTROYED   |
    And 以下转换 SHALL 非法:
      | from        | to          |
      | CREATED     | RUNNING     |
      | CREATED     | STOPPED     |
      | INITIALIZED | STOPPED     |
      | DESTROYED   | CREATED     |
      | DESTROYED   | INITIALIZED |
      | DESTROYED   | RUNNING     |
      | DESTROYED   | STOPPED     |

  Scenario: DESTROYED 是终态
    Given Agent 处于 DESTROYED 状态
    Then VALID_TRANSITIONS[DESTROYED] SHALL 为空集合
    And 任何状态转换 MUST 抛出 InvalidStateTransition
```

## Feature: Agent 初始化

```gherkin
Feature: Agent init()
  Agent 从 CREATED 转换到 INITIALIZED，调用子类 _on_init 钩子。

  Scenario: 成功初始化
    Given Agent 处于 CREATED 状态
    When 调用 agent.init()
    Then Agent.state SHALL 变为 AgentState.INITIALIZED
    And _on_init 钩子 SHALL 被调用
    And SHALL 触发 "state_changed" 事件（old=CREATED, new=INITIALIZED）

  Scenario: init 失败进入 DESTROYED
    Given Agent 处于 CREATED 状态
    And _on_init 抛出 RuntimeError("连接失败")
    When 调用 agent.init()
    Then SHALL 抛出 AgentInitFailed，包含原始异常信息
    And Agent.state SHALL 被强制设置为 AgentState.DESTROYED
    And 后续调用 agent.init() SHALL 抛出 InvalidStateTransition（不可重试）

  Scenario: 非 CREATED 状态调用 init
    Given Agent 已成功完成 init，处于 INITIALIZED 状态
    When 再次调用 agent.init()
    Then SHALL 抛出 InvalidStateTransition
```

## Feature: Agent 运行

```gherkin
Feature: Agent run()
  Agent 从 INITIALIZED 或 STOPPED 转换到 RUNNING。

  Scenario: 从 INITIALIZED 启动
    Given Agent 处于 INITIALIZED 状态
    When 调用 agent.run()
    Then Agent.state SHALL 变为 AgentState.RUNNING
    And _on_run 钩子 SHALL 被调用
    And SHALL 触发 "state_changed" 事件（old=INITIALIZED, new=RUNNING）

  Scenario: 从 STOPPED 恢复运行
    Given Agent 处于 STOPPED 状态
    When 调用 agent.run()
    Then Agent.state SHALL 变为 AgentState.RUNNING
    And _on_run 钩子 SHALL 被调用

  Scenario: 并发状态转换互斥
    Given Agent 处于 INITIALIZED 状态
    When 协程 A 调用 agent.run()
    And 协程 B 同时调用 agent.stop()
    Then 由于 anyio.Lock 保护，先到达的操作 SHALL 成功
    And 后到达的操作 SHALL 抛出 InvalidStateTransition
```

## Feature: Agent 停止

```gherkin
Feature: Agent stop()
  Agent 从 RUNNING 转换到 STOPPED。

  Scenario: 成功停止
    Given Agent 处于 RUNNING 状态
    When 调用 agent.stop()
    Then Agent.state SHALL 变为 AgentState.STOPPED
    And _on_stop 钩子 SHALL 被调用
    And SHALL 触发 "state_changed" 事件（old=RUNNING, new=STOPPED）
```

## Feature: Agent 销毁

```gherkin
Feature: Agent destroy()
  Agent 从任意状态转换到 DESTROYED，destroy MUST 幂等。

  Scenario: 销毁 RUNNING 的 Agent
    Given Agent 处于 RUNNING 状态
    When 调用 agent.destroy()
    Then Agent.state SHALL 变为 AgentState.DESTROYED
    And _on_destroy 钩子 SHALL 被调用

  Scenario: 销毁 CREATED 的 Agent
    Given Agent 处于 CREATED 状态
    When 调用 agent.destroy()
    Then Agent.state SHALL 变为 AgentState.DESTROYED
    And _on_destroy 钩子 SHALL 被调用

  Scenario: destroy 幂等
    Given Agent 处于 DESTROYED 状态
    When 调用 agent.destroy()
    Then SHALL NOT 抛出异常（幂等操作，直接 return）

  Scenario: DESTROYED 后任何操作均失败
    Given Agent 处于 DESTROYED 状态
    When 调用 agent.run()
    Then SHALL 抛出 InvalidStateTransition
    When 调用 agent.stop()
    Then SHALL 抛出 InvalidStateTransition
    When 调用 agent.init()
    Then SHALL 抛出 InvalidStateTransition
```

## Feature: 生命周期事件

```gherkin
Feature: EventEmitter 状态变更通知
  Agent 内置 EventEmitter，外部观察者 SHALL 可订阅状态变更事件。

  Scenario: 订阅 state_changed 事件
    Given Agent 实例
    When 注册回调到 agent.events.on("state_changed", callback)
    And 调用 agent.init()
    Then callback SHALL 被调用
    And 参数 SHALL 为 (old_state=CREATED, new_state=INITIALIZED)

  Scenario: 完整生命周期事件序列
    Given 新 Agent
    When 依次执行 init -> run -> stop -> destroy
    Then SHALL 按顺序触发 4 次 "state_changed" 事件:
      | old_state   | new_state   |
      | CREATED     | INITIALIZED |
      | INITIALIZED | RUNNING     |
      | RUNNING     | STOPPED     |
      | STOPPED     | DESTROYED   |
```

## Feature: LLMAgent 子类

```gherkin
Feature: LLMAgent 继承 AgentBase
  LLMAgent 扩展 AgentBase，集成 LLM 后端、工具注册表、短期记忆和消息总线。

  Scenario: LLMAgent 创建
    Given InProcessMessageBus、LLMBackend 实例
    When 创建 LLMAgent(bus=bus, llm=llm, name="assistant", system_prompt="You are helpful")
    Then LLMAgent SHALL 持有 bus、llm、tools（SimpleToolRegistry）、memory（ShortTermMemory）
    And LLMAgent.state SHALL 为 AgentState.CREATED

  Scenario: LLMAgent init 订阅消息
    Given LLMAgent 处于 CREATED 状态
    When 调用 agent.init()
    Then SHALL 订阅 topic "agent.{name}.incoming"
    And 订阅 ID SHALL 被保存到 _sub_ids 列表

  Scenario: LLMAgent destroy 清理订阅
    Given LLMAgent 已订阅 topic
    When 调用 agent.destroy()
    Then 所有订阅 SHALL 被取消（bus.unsubscribe）
    And _sub_ids SHALL 被清空

  Scenario: LLMAgent chat() 直接调用
    Given LLMAgent 处于 RUNNING 状态
    When 调用 agent.chat("Hello")
    Then SHALL 调用 LLM 后端完成请求
    And 返回 LLM 响应文本
    And 消息 SHALL 被存入 memory 和 _history

  Scenario: LLMAgent 工具调用循环
    Given LLMAgent 注册了工具 "calculator"
    And LLM 返回包含 tool_call 的响应
    When 处理用户输入
    Then SHALL 执行工具调用
    And 将工具结果追加到 _history
    And 再次调用 LLM，最多循环 5 轮（max_tool_rounds=5）

  Scenario: LLMAgent 历史窗口
    Given LLMAgent 的 _history 包含 30 条消息
    When 调用 LLM 时
    Then SHALL 仅发送最近 20 条消息（_history[-20:]）
```
