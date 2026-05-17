# Delta Spec: Skill System

> Change: change-20260515-091942-capability | Domain: skill | Type: ADDED
> Status: Draft

---

## Feature: Skill Registration

```gherkin
Feature: Skill 注册与发现
  开发者 SHALL 可注册 Skill 并通过多种方式发现。

  Scenario: 注册新 Skill
    Given SkillDescriptor(name="code_review", version="1.0", dependencies=["format"])
    When 调用 registry.register(descriptor, execute_fn)
    Then Skill "code_review" SHALL 可被 discover 找到

  Scenario: 装饰器注册 Skill
    When 使用 @skill_registry.skill 装饰器注册函数
    Then Skill SHALL 自动注册，descriptor 从函数签名推断

  Scenario: 多版本共存
    Given "code_review" v1.0.0 已注册
    When 注册 "code_review" v2.0.0
    Then 两个版本 SHALL 共存
    And registry.get("code_review") SHALL 返回 v2.0.0

  Scenario: 按 tag 发现 Skill
    Given registry 有 Skill tags: ["search","web"], ["search","file"], ["code","review"]
    When 调用 registry.discover(tags=["search"])
    Then SHALL 返回前 2 个 Skill
```

## Feature: Dependency Resolution

```gherkin
Feature: Skill 依赖解析 DAG
  系统 SHALL 解析 Skill 间的依赖关系并拓扑排序。

  Scenario: 线性依赖链
    Given C→B→A 依赖链
    When 调用 registry.resolve_dependencies("C")
    Then SHALL 返回 ["A","B","C"]

  Scenario: 菱形依赖
    Given D→B,A; B→A; C→A
    When 解析 D 的依赖
    Then A SHALL 在 B 和 C 之前

  Scenario: 循环依赖检测
    Given A→B→C→A 循环
    When 解析依赖
    Then SHALL 抛出 CyclicDependencyError
    And 错误信息 SHALL 包含循环路径

  Scenario: 可选依赖
    Given Skill A 依赖 B(required) 和 C(optional)
    And C 未注册
    When 解析依赖
    Then SHALL 正常执行，C 被跳过
    When C 已注册
    Then 解析结果 SHALL 包含 C

  Scenario: 缺失必需依赖
    Given Skill A 依赖 "nonexistent"
    When 解析依赖
    Then SHALL 抛出 SkillDependencyNotFoundError
```

## Feature: Skill Execution

```gherkin
Feature: Skill 执行
  Agent SHALL 可执行 Skill 并获得结果。

  Scenario: 成功执行
    Given "web_search" 已注册
    When 调用 registry.execute("web_search", {"query":"test"})
    Then SHALL 返回 execute_fn 的结果

  Scenario: 依赖自动先执行
    Given "code_review" 依赖 "code_format"
    When 执行 "code_review"
    Then "code_format" SHALL 先执行
    And "code_format" 的输出 SHALL 注入 context.dependencies

  Scenario: mutable context 注入
    Given Skill "A" 修改 context["key"] = "modified"
    And Skill "B" 依赖 "A"
    When 执行链完成
    Then Skill "B" SHALL 读到 context["key"] = "modified"

  Scenario: 执行超时
    Given "slow_skill" 需要 10 秒，超时 5 秒
    When 执行
    Then SHALL 抛出 SkillTimeoutError

  Scenario: 执行不存在 Skill
    When 执行 "nonexistent"
    Then SHALL 抛出 SkillNotFoundError
```
