# Spec: Skill System

> Phase: 2 (Capability Layer) | Priority: P0 | Depends on: 00-core-types, 01-agent-lifecycle
> Type: ADDED
> Module: `agentforge/skill/`

---

## Overview

Skill 系统支持能力的动态注册、发现、依赖解析和执行。Skill 是 Agent 可执行的最小能力单元，支持声明依赖关系并通过 DAG 拓扑排序确定执行顺序。

---

## Feature: Skill 注册

```gherkin
Feature: Skill 注册
  作为 Skill 开发者
  我需要将 Skill 注册到 SkillRegistry
  以便 Agent 可以发现和使用

  Background:
    Given 一个 SkillRegistry 实例

  Scenario: 注册新 Skill
    Given 一个 SkillDescriptor:
      | field        | value                        |
      | name         | "web_search"                 |
      | version      | "1.0.0"                      |
      | description  | "搜索互联网信息"              |
      | dependencies | []                           |
      | tags         | ["search", "web"]            |
      | entry_point  | "skills.web_search:execute"  |
    And 一个 async execute 函数
    When 我调用 registry.register(descriptor, execute_fn)
    Then Skill "web_search" 应在 registry 中可用

  Scenario: 注册带依赖的 Skill
    Given 一个 SkillDescriptor dependencies=["http_client", "html_parser"]
    When 我调用 registry.register(descriptor, execute_fn)
    Then 注册应成功
    And 依赖关系应被记录

  Scenario: 注册同名同版本 Skill
    Given Skill "web_search" v1.0.0 已注册
    When 我再次注册 "web_search" v1.0.0
    Then 应抛出 SkillAlreadyRegisteredError

  Scenario: 注册同名不同版本 Skill
    Given Skill "web_search" v1.0.0 已注册
    When 我注册 "web_search" v2.0.0
    Then 应允许注册，两个版本共存
    And registry.get("web_search") 应返回最新版本 (v2.0.0)
```

---

## Feature: Skill 发现

```gherkin
Feature: Skill 发现
  作为 Agent
  我需要搜索和发现可用的 Skill
  以找到适合当前任务的能力

  Background:
    Given registry 中有以下 Skill:
      | name          | tags                    |
      | web_search    | ["search", "web"]       |
      | file_search   | ["search", "file"]      |
      | code_review   | ["code", "review"]      |
      | code_format   | ["code", "format"]      |

  Scenario: 按 tag 发现 Skill
    When 我调用 registry.discover(tags=["search"])
    Then 应返回 ["web_search", "file_search"]

  Scenario: 按多个 tag 发现（AND 语义）
    When 我调用 registry.discover(tags=["search", "web"])
    Then 应返回 ["web_search"]
    And 不应包含 "file_search"（缺少 "web" tag）

  Scenario: 按 name 精确查找
    When 我调用 registry.get("web_search")
    Then 应返回 "web_search" 的 SkillDescriptor

  Scenario: 查找不存在的 Skill
    When 我调用 registry.get("nonexistent")
    Then 应返回 None

  Scenario: 无参数列出所有 Skill
    When 我调用 registry.discover()
    Then 应返回所有已注册的 Skill
```

---

## Feature: Skill 依赖解析

```gherkin
Feature: Skill 依赖解析
  作为 SkillRegistry
  我需要解析 Skill 的依赖关系
  以确定正确的执行顺序

  Scenario: 线性依赖链
    Given Skill 依赖关系:
      | skill       | depends on     |
      | C           | B              |
      | B           | A              |
      | A           | (none)         |
    When 我调用 registry.resolve_dependencies("C")
    Then 应返回 ["A", "B", "C"]（拓扑排序结果）

  Scenario: 菱形依赖
    Given Skill 依赖关系:
      | skill       | depends on     |
      | D           | B, C          |
      | B           | A              |
      | C           | A              |
      | A           | (none)         |
    When 我调用 registry.resolve_dependencies("D")
    Then 应返回 ["A", "B", "C", "D"] 或 ["A", "C", "B", "D"]
    And A 必须在 B 和 C 之前
    And B 和 C 必须在 D 之前

  Scenario: 循环依赖检测
    Given Skill 依赖关系:
      | skill       | depends on     |
      | A           | B              |
      | B           | C              |
      | C           | A              |
    When 我调用 registry.resolve_dependencies("A")
    Then 应抛出 CyclicDependencyError
    And 错误信息应包含循环路径 "A → B → C → A"

  Scenario: 缺失依赖检测
    Given Skill "A" 依赖 "nonexistent_skill"
    When 我调用 registry.resolve_dependencies("A")
    Then 应抛出 SkillDependencyNotFoundError
    And 错误信息应提及缺失的 "nonexistent_skill"
```

---

## Feature: Skill 执行

```gherkin
Feature: Skill 执行
  作为 Agent
  我需要执行一个 Skill
  以完成特定任务

  Background:
    Given Skill "web_search" 已注册
    And 其 execute_fn 接受 context: dict 参数

  Scenario: 成功执行 Skill
    When 我调用 registry.execute("web_search", {"query": "Python"})
    Then execute_fn 应被调用，参数为 {"query": "Python"}
    And 应返回 execute_fn 的结果

  Scenario: 执行带依赖的 Skill
    Given Skill "code_review" 依赖 "code_format"
    When 我调用 registry.execute("code_review", {"file": "main.py"})
    Then 应先执行 "code_format"
    And "code_format" 的输出应作为 "code_review" context 的一部分
    And 最终返回 "code_review" 的结果

  Scenario: 执行不存在的 Skill
    When 我调用 registry.execute("nonexistent", {})
    Then 应抛出 SkillNotFoundError

  Scenario: Skill 执行异常
    Given Skill "bad_skill" 的 execute_fn 抛出 RuntimeError
    When 我调用 registry.execute("bad_skill", {})
    Then 应抛出 SkillExecutionError
    And 原始异常应链式保留 (__cause__)

  Scenario: Skill 执行超时
    Given Skill "slow_skill" 的 execute_fn 需要 10 秒
    And 默认超时为 5 秒
    When 我调用 registry.execute("slow_skill", {}, timeout=5.0)
    Then 应抛出 SkillTimeoutError
```

```gherkin
Feature: Skill 执行上下文
  作为 Skill
  我需要接收执行上下文
  以获取必要的信息完成任务

  Scenario: 上下文注入依赖结果
    Given Skill "code_review" 依赖 "code_format"
    And "code_format" 返回 {"formatted_code": "def foo(): pass"}
    When 执行 "code_review"
    Then "code_review" 的 context 应包含:
      | key              | value                   |
      | dependencies     | {"code_format": {"formatted_code": "def foo(): pass"}} |
      | agent_id         | 调用 Agent 的 ID         |
      | timestamp        | 执行时间                 |

  Scenario: 上下文传递给 Skill
    When 我调用 registry.execute("web_search", {"query": "test", "limit": 5})
    Then execute_fn 收到的 context 应包含 query 和 limit
```

---

## Feature: Skill 版本管理

```gherkin
Feature: Skill 版本
  作为 Skill 开发者
  我需要管理 Skill 的多版本
  以支持平滑升级和兼容性

  Scenario: 获取特定版本
    Given "web_search" 有 v1.0.0 和 v2.0.0
    When 我调用 registry.get("web_search", version="1.0.0")
    Then 应返回 v1.0.0 的 descriptor

  Scenario: 默认获取最新版本
    Given "web_search" 有 v1.0.0 和 v2.0.0
    When 我调用 registry.get("web_search")
    Then 应返回 v2.0.0 的 descriptor

  Scenario: 版本范围依赖
    Given Skill "A" 声明依赖 "web_search>=1.0.0"
    And "web_search" v2.0.0 已注册
    When 我调用 registry.resolve_dependencies("A")
    Then 应解析为 "web_search" v2.0.0
```

---

## Acceptance Criteria

- [ ] DAG 依赖解析使用 Kahn 算法或 DFS 拓扑排序
- [ ] 循环依赖在注册阶段即检测（不等到执行）
- [ ] execute 方法为 async，使用 异步框架
- [ ] 超时使用 `异步框架.move_on_after`
- [ ] Skill 执行上下文自动注入依赖结果
- [ ] 版本比较遵循 semver 规范
