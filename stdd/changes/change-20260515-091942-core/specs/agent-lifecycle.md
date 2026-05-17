# Delta Spec: Agent Lifecycle

> Change: change-20260515-091942-core | Domain: agent | Type: ADDED
> Status: Draft

---

## Feature: Agent 创建

```gherkin
Feature: Agent 实例创建
  开发者创建 Agent 实例，初始状态 MUST 为 INIT。

  Scenario: 指定 ID 创建
    When 使用 agent_id="agent-001" 和 name="测试" 创建 Agent
    Then Agent.id SHALL 为 "agent-001"
    And Agent.state SHALL 为 AgentState.INIT

  Scenario: 自动生成 ID
    When 仅指定 name 创建 Agent
    Then Agent.id SHALL 为自动生成的 UUID
    And Agent.state SHALL 为 AgentState.INIT

  Scenario: 重复 ID 冲突
    Given agent_id="agent-001" 的 Agent 已存在
    When 再次使用 agent_id="agent-001" 创建 Agent
    Then SHALL 抛出 AgentStateError
```

## Feature: Agent 初始化

```gherkin
Feature: Agent init()
  Agent 完成资源初始化，init 失败 MUST 销毁重建。

  Scenario: 成功初始化
    Given Agent 处于 INIT 状态
    When 调用 agent.init()
    Then _on_init 钩子 SHALL 被调用
    And Agent.state SHALL 保持 AgentState.INIT
    And SHALL 触发 "agent.initialized" 事件

  Scenario: init 失败必须销毁重建
    Given Agent 的 _on_init 抛出 RuntimeError("连接失败")
    When 调用 agent.init()
    Then SHALL 抛出 AgentInitError，包含原始异常信息
    And Agent.state SHALL 保持 AgentState.INIT
    And 后续调用 agent.init() SHALL 抛出 AgentStateError（不可重试）
    And 开发者 MUST 先 destroy 再重建

  Scenario: 已初始化再次 init
    Given Agent 已成功完成 init
    When 再次调用 agent.init()
    Then SHALL 抛出 AgentStateError
```

## Feature: Agent 运行

```gherkin
Feature: Agent run()
  Agent 启动进入运行状态，MUST 通过 Lock 互斥保护。

  Scenario: 成功启动
    Given Agent 已完成 init，处于 INIT 状态
    When 调用 agent.run()
    Then Agent.state SHALL 变为 AgentState.RUNNING
    And SHALL 触发 "agent.started" 事件
    And _on_run 钩子 SHALL 被调用

  Scenario: 从 STOPPED 恢复运行
    Given Agent 处于 STOPPED 状态
    When 调用 agent.run()
    Then Agent.state SHALL 变为 AgentState.RUNNING
    And SHALL 触发 "agent.resumed" 事件

  Scenario: 未初始化直接运行
    Given Agent 处于 INIT 状态且未调用 init
    When 调用 agent.run()
    Then SHALL 抛出 AgentStateError

  Scenario: 运行中再次运行
    Given Agent 处于 RUNNING 状态
    When 调用 agent.run()
    Then SHALL 抛出 AgentStateError

  Scenario: 并发状态转换互斥
    Given Agent 处于 INIT 状态
    When 协程 A 调用 agent.run()
    And 协程 B 同时调用 agent.stop()
    Then 先到达的操作 SHALL 成功
    And 后到达的操作 SHALL 抛出 AgentStateError
```

## Feature: Agent 停止

```gherkin
Feature: Agent stop()
  Agent 优雅停止，停止后 MUST 丢弃新消息。

  Scenario: 成功停止
    Given Agent 处于 RUNNING 状态
    When 调用 agent.stop()
    Then Agent.state SHALL 变为 AgentState.STOPPED
    And SHALL 触发 "agent.stopped" 事件
    And _on_stop 钩子 SHALL 被调用

  Scenario: 停止后丢弃新消息
    Given Agent 处于 STOPPED 状态
    When 消息总线向该 Agent 投递消息
    Then 消息 SHALL 被静默丢弃
    And Agent 的 handler SHALL NOT 被调用

  Scenario: 停止超时
    Given Agent 的 _on_stop 需要 10 秒
    And stop 超时设置为 5 秒
    When 调用 agent.stop()
    Then SHALL 抛出 AgentStopTimeoutError
    And Agent.state SHALL 强制变为 AgentState.STOPPED
```

## Feature: Agent 销毁

```gherkin
Feature: Agent destroy()
  Agent 彻底销毁并释放资源，destroy MUST 幂等。

  Scenario: 销毁已停止的 Agent
    Given Agent 处于 STOPPED 状态
    When 调用 agent.destroy()
    Then Agent.state SHALL 变为 AgentState.DESTROYED
    And SHALL 触发 "agent.destroyed" 事件
    And _on_destroy 钩子 SHALL 被调用
    And Agent 持有的所有资源 SHALL 被释放

  Scenario: 销毁运行中的 Agent
    Given Agent 处于 RUNNING 状态
    When 调用 agent.destroy()
    Then SHALL 先自动调用 stop()
    And 然后 Agent.state SHALL 变为 AgentState.DESTROYED

  Scenario: destroy 幂等
    Given Agent 处于 DESTROYED 状态
    When 调用 agent.destroy()
    Then SHALL NOT 抛出异常（幂等操作）

  Scenario: DESTROYED 是终态
    Given Agent 处于 DESTROYED 状态
    When 调用 agent.run()
    Then SHALL 抛出 AgentStateError
    When 调用 agent.stop()
    Then SHALL 抛出 AgentStateError
    When 调用 agent.init()
    Then SHALL 抛出 AgentStateError
```

## Feature: 生命周期事件

```gherkin
Feature: 状态变更事件通知
  外部观察者 SHALL 可订阅 Agent 状态变更事件。

  Scenario: 订阅状态变更
    Given Agent 实例
    When 注册回调到 agent.on("state_changed", callback)
    And 调用 agent.run()
    Then callback SHALL 被调用
    And 参数 SHALL 包含 agent_id, old_state=INIT, new_state=RUNNING, timestamp

  Scenario: 完整生命周期事件序列
    Given 新 Agent
    When 依次执行 init → run → stop → destroy
    Then SHALL 按顺序触发: agent.initialized → agent.started → agent.stopped → agent.destroyed
```
