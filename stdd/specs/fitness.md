# Delta Spec: Fitness Framework

> Change: change-20260515-095601 | Domain: fitness | Type: ADDED
> Status: Updated to reflect actual implementation

---

## Feature: Fitness Function Protocol

```gherkin
Feature: 适应度函数接口
  系统提供可扩展的适应度函数框架。

  Scenario: FitnessFunction Protocol
    Given FitnessFunction Protocol 定义
    Then 每个 FitnessFunction SHALL 实现 evaluate(population: list[Any]) -> list[float]

  Scenario: SimpleFitness 逐个评估
    Given 一个单目标函数 fn
    When 创建 SimpleFitness(fn)
    Then evaluate SHALL 对每个 individual 调用 fn(ind)
    And SHALL 返回 list[float] 适应度值

  Scenario: 批量评估（引擎直接调用）
    Given EvolutionEngine 的 fitness_fn 参数
    Then fitness_fn 签名 SHALL 为 (list[Individual]) -> list[float]
    And 引擎 SHALL 直接调用 fitness_fn 而非通过 FitnessFunction Protocol
    And fitness_fn 可以是任意 Callable，不要求实现 FitnessFunction 接口

  Note: 原 spec 提到"同步函数自动包装为异步"，实际实现中 EvolutionEngine.evolve 是同步方法，
  fitness_fn 也是同步调用。异步包装由 app.py 通过 asyncio.run_in_executor 处理。
```

## Feature: Multi-Objective Fitness

```gherkin
Feature: 多目标加权适应度
  WeightedMultiObjective 支持多目标加权聚合。

  Scenario: 加权适应度计算
    Given 目标函数 A 返回 0.8，权重 1.0
    And 目标函数 B 返回 0.5，权重 1.0
    When 计算加权适应度
    Then 结果 SHALL 为 0.8*1.0 + 0.5*1.0 = 1.3

  Scenario: 默认权重
    Given N 个目标函数，未指定权重
    When 创建 WeightedMultiObjective
    Then 权重 SHALL 默认为 [1.0] * N
```

Note: 权重归一化 NOT_IMPLEMENTED — WeightedMultiObjective 直接使用传入权重或默认 1.0，
不进行自动归一化。权重之和不需要为 1.0。

## Feature: Constraint Handling

```gherkin
Feature: 约束处理
  系统支持边界裁剪、罚函数和修复算子。

  Scenario: 边界裁剪（BoundaryClip）
    Given 基因值超出 [lower, upper] 范围
    When 调用 BoundaryClip.enforce(genome)
    Then 基因值 SHALL 被裁剪到边界内（np.clip）
    And genome SHALL 有 genes (ndarray) 和 bounds 属性

  Scenario: 罚函数（PenaltyFunction）
    Given 一个约束函数 constraint_fn 和 penalty_factor=100.0
    When 调用 penalty.apply(genome)
    Then SHALL 返回 -penalty_factor * violation
    And 返回值为负数（惩罚适应度）

  Scenario: 修复算子（RepairOperator）
    Given 一个自定义修复函数 repair_fn
    When 调用 repair_op.repair(genome)
    Then SHALL 返回修复后的合法 genome
```

## Feature: Agent Personality Fitness Function

```gherkin
Feature: 智能体人格参数适应度
  app.py 中内置了 agent 模式的适应度函数。

  Scenario: 人格参数编码
    Given 10 维基因组
    When 计算适应度
    Then 基因 SHALL 通过 sigmoid(1/(1+exp(-g))) 映射到 [0,1]
    And 每个维度代表一个人格特质

  Scenario: 多目标适应度
    Given agent 模式适应度函数
    When 评估个体
    Then SHALL 计算 4 个目标：
      | 目标      | 公式                                            | 权重 |
      | balance   | -|mean(traits) - 0.5| * 2                        | 隐式 |
      | diversity | std(traits) * 2                                 | 隐式 |
      | extremes  | -sum(max(0, t-0.9) + max(0, 0.1-t)) * 3         | 隐式 |
      | coherence | -|traits[2] - (1-traits[8])| * 0.5 (若 dim>=8)  | 隐式 |
    And 总适应度 SHALL 为各项之和（非权重归一化）
```
