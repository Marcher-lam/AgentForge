# Spec: Agent Base & Lifecycle

> Phase: 1 (Core Skeleton) | Priority: P0 | Depends on: 00-core-types
> Type: ADDED
> Module: `agentforge/agent/`

---

## Overview

Agent 基类提供标准化的生命周期管理，通过状态机控制 init → run → stop → destroy 流程，并基于事件通知外部观察者。

---

## Feature: Agent 创建与初始化

```gherkin
Feature: Agent 创建
  作为框架使用者
  我需要创建一个 Agent 实例并完成初始化
  以便它准备好接收和处理任务

  Background:
    Given 一个继承自 AgentBase 的 TestAgent 类

  Scenario: 成功创建 Agent 实例
    When 我使用 agent_id="agent-001" 和 name="测试Agent" 创建 TestAgent
    Then Agent 的 id 应为 "agent-001"
    And Agent 的 name 应为 "测试Agent"
    And Agent 的 state 应为 AgentState.INIT

  Scenario: Agent ID 自动生成
    When 我仅指定 name="测试Agent" 创建 TestAgent
    Then Agent 的 id 应为自动生成的 UUID 字符串
    And Agent 的 state 应为 AgentState.INIT

  Scenario: 拒绝重复 ID
    Given 一个 agent_id="agent-001" 的 Agent 已存在
    When 我再次使用 agent_id="agent-001" 创建 Agent
    Then 应抛出 AgentIdConflictError
```

```gherkin
Feature: Agent 初始化 (init)
  作为框架使用者
  我需要调用 init 完成资源准备
  以便 Agent 可以进入运行状态

  Scenario: 成功初始化
    Given 一个处于 INIT 状态的 Agent
    When 我调用 agent.init()
    Then Agent 的 _on_init 钩子应被调用
    And Agent 的 state 应保持 AgentState.INIT
    And Agent 的资源应已准备就绪

  Scenario: init 发生异常
    Given 一个 _on_init 会抛出 RuntimeError 的 Agent
    When 我调用 agent.init()
    Then 应抛出 AgentInitError，包含原始异常信息
    And Agent 的 state 应保持 AgentState.INIT

  Scenario: 重复初始化
    Given 一个已经 init 过的 Agent
    When 我再次调用 agent.init()
    Then 应抛出 AgentStateError，提示 "Agent already initialized"
```

---

## Feature: Agent 运行

```gherkin
Feature: Agent 运行 (run)
  作为框架使用者
  我需要启动 Agent 进入运行状态
  以便它可以处理消息和执行任务

  Scenario: 成功启动
    Given 一个已初始化且处于 INIT 状态的 Agent
    When 我调用 agent.run()
    Then Agent 的 state 应变为 AgentState.RUNNING
    And Agent 的 _on_run 钩子应被调用
    And 应触发 "agent.started" 事件

  Scenario: 从 STOPPED 恢复运行
    Given 一个处于 STOPPED 状态的 Agent
    When 我调用 agent.run()
    Then Agent 的 state 应变为 AgentState.RUNNING
    And 应触发 "agent.resumed" 事件

  Scenario: 未初始化直接运行
    Given 一个处于 INIT 状态且未调用 init 的 Agent
    When 我调用 agent.run()
    Then 应抛出 AgentStateError

  Scenario: 运行中再次运行
    Given 一个处于 RUNNING 状态的 Agent
    When 我调用 agent.run()
    Then 应抛出 AgentStateError，提示 "Agent is already running"

  Scenario: 已销毁的 Agent 运行
    Given 一个处于 DESTROYED 状态的 Agent
    When 我调用 agent.run()
    Then 应抛出 AgentStateError，提示 "Agent is destroyed"
```

---

## Feature: Agent 停止

```gherkin
Feature: Agent 停止 (stop)
  作为框架使用者
  我需要优雅地停止 Agent
  以便它可以保留状态但暂停处理

  Scenario: 成功停止
    Given 一个处于 RUNNING 状态的 Agent
    When 我调用 agent.stop()
    Then Agent 的 state 应变为 AgentState.STOPPED
    And Agent 的 _on_stop 钩子应被调用
    And 应触发 "agent.stopped" 事件
    And 正在处理的任务应收到取消信号

  Scenario: 停止超时
    Given 一个 _on_stop 需要 10 秒的 Agent
    And stop 超时设置为 5 秒
    When 我调用 agent.stop()
    Then 应抛出 AgentStopTimeoutError
    And Agent 的 state 应强制变为 AgentState.STOPPED

  Scenario: 停止非运行状态的 Agent
    Given 一个处于 INIT 状态的 Agent
    When 我调用 agent.stop()
    Then 应抛出 AgentStateError
```

---

## Feature: Agent 销毁

```gherkin
Feature: Agent 销毁 (destroy)
  作为框架使用者
  我需要彻底销毁 Agent 并释放所有资源
  以确保没有资源泄漏

  Scenario: 成功销毁已停止的 Agent
    Given 一个处于 STOPPED 状态的 Agent
    When 我调用 agent.destroy()
    Then Agent 的 state 应变为 AgentState.DESTROYED
    And Agent 的 _on_destroy 钩子应被调用
    And 应触发 "agent.destroyed" 事件
    And Agent 持有的所有资源应被释放

  Scenario: 销毁运行中的 Agent（先停止再销毁）
    Given 一个处于 RUNNING 状态的 Agent
    When 我调用 agent.destroy()
    Then 应先自动调用 stop
    And 然后 Agent 的 state 应变为 AgentState.DESTROYED

  Scenario: 已销毁的 Agent 操作
    Given 一个处于 DESTROYED 状态的 Agent
    When 我调用 agent.run()
    Then 应抛出 AgentStateError

  Scenario: 重复销毁
    Given 一个处于 DESTROYED 状态的 Agent
    When 我调用 agent.destroy()
    Then 应为幂等操作，不抛异常
```

---

## Feature: Agent 生命周期事件

```gherkin
Feature: 生命周期事件通知
  作为外部观察者
  我需要订阅 Agent 的状态变更事件
  以便在 Agent 状态变化时执行相应操作

  Scenario: 订阅状态变更
    Given 一个 Agent 实例
    When 我注册一个回调到 agent.on("state_changed", callback)
    And 我调用 agent.run()
    Then callback 应被调用，参数包含:
      | field       | value                |
      | agent_id    | agent 的 ID          |
      | old_state   | INIT                 |
      | new_state   | RUNNING              |
      | timestamp   | 变更时间             |

  Scenario: 完整生命周期事件序列
    Given 一个新的 Agent
    When 我依次执行 init → run → stop → destroy
    Then 应按顺序触发以下事件
      | event            |
      | agent.initialized |
      | agent.started    |
      | agent.stopped    |
      | agent.destroyed  |
```

---

## Feature: Agent 钩子方法

```gherkin
Feature: 可覆写的钩子方法
  作为 Agent 开发者
  我需要覆写基类的钩子方法
  以实现自定义的初始化、运行、停止和销毁逻辑

  Scenario: 钩子方法签名
    Given AgentBase 定义了以下抽象方法
    Then 每个方法签名应为
      | method      | signature                        |
      | _on_init    | async (self) -> None             |
      | _on_run     | async (self) -> None             |
      | _on_stop    | async (self) -> None             |
      | _on_destroy | async (self) -> None             |

  Scenario: 子类未实现钩子
    Given 一个直接实例化 AgentBase 的尝试
    Then 应抛出 TypeError，提示无法实例化抽象类
```

---

## Acceptance Criteria

- [ ] 状态机实现使用 `AgentState` 枚举和合法转换表
- [ ] 非法状态转换抛出 `AgentStateError`
- [ ] 所有生命周期方法为 `async`，使用 `异步框架` 兼容 API
- [ ] 事件系统基于回调列表，非 asyncio.Event
- [ ] 超时控制使用 `异步框架.move_on_after`
- [ ] destroy 操作幂等
