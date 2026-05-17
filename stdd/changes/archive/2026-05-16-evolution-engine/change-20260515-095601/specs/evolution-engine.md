# Delta Spec: Evolution Engine

> Change: change-20260515-095601 | Domain: engine | Type: ADDED
> Status: Draft

---

## Feature: Population Management

```gherkin
Feature: 种群管理
  系统 SHALL 管理种群的创建、统计和排序。

  Scenario: 初始化随机种群
    Given 种群大小=100, 基因组类型=实数向量, 维度=50
    When 创建种群
    Then SHALL 生成 100 个随机基因组
    And 每个基因值 SHALL 在 bounds 范围内

  Scenario: 种群统计
    Given 种群已评估
    When 查询种群统计
    Then SHALL 返回:
      | metric       | description          |
      | best_fitness | 最优个体适应度        |
      | mean_fitness | 平均适应度            |
      | std_fitness  | 适应度标准差          |
      | diversity    | 种群多样性指标        |

  Scenario: 种群排序
    Given 种群已评估
    When 按适应度排序
    Then 最优个体 SHALL 排在首位
```

## Feature: Evolution Loop

```gherkin
Feature: 进化主循环
  引擎 SHALL 执行完整的进化循环。

  Scenario: 标准进化流程
    Given 种群已初始化并评估
    When 执行一代进化
    Then SHALL 按顺序执行:
      | step     | operation         |
      | 1        | 评估适应度         |
      | 2        | 选择              |
      | 3        | 交叉              |
      | 4        | 变异              |
      | 5        | （可选）精英保留    |
      | 6        | 替换种群           |
      | 7        | 更新统计           |

  Scenario: 异步评估
    Given 适应度函数为 async
    When 评估种群
    Then SHALL 使用异步执行
    And batch 模式 SHALL 优先于逐个评估

  Scenario: 种子控制可复现
    Given seed=42
    When 运行进化引擎 50 代
    And 使用相同 seed=42 再次运行
    Then 每代的 best_fitness 序列 SHALL 完全一致
```

## Feature: Termination Criteria

```gherkin
Feature: 终止条件
  引擎 SHALL 支持组合终止条件（OR 语义）。

  Scenario: 最大世代数终止
    Given 终止条件 max_generations=100
    When 进化到第 100 代
    Then 引擎 SHALL 终止

  Scenario: 适应度阈值终止
    Given 终止条件 fitness_threshold=0.99
    When 最优适应度达到 0.99
    Then 引擎 SHALL 终止

  Scenario: 收敛检测 - best 停滞
    Given 终止条件 convergence_patience=20
    When 最优适应度连续 20 代无改善
    Then 引擎 SHALL 终止

  Scenario: 收敛检测 - 种群多样性
    Given 终止条件 diversity_threshold=0.01
    When 种群多样性低于 0.01
    Then 引擎 SHALL 终止

  Scenario: 组合条件 OR 语义
    Given 终止条件为 max_gen=200 OR threshold=0.99 OR convergence_patience=30
    When 任一条件满足
    Then 引擎 SHALL 终止
```

## Feature: Callbacks

```gherkin
Feature: 进化回调
  系统 SHALL 支持回调注入自定义逻辑。

  Scenario: on_generation_end 回调
    Given 注册了 on_generation_end 回调
    When 每代进化完成
    Then 回调 SHALL 被调用
    And 参数 SHALL 包含 generation, population_stats, best_individual

  Scenario: on_evaluation 回调
    Given 注册了 on_evaluation 回调
    When 种群评估完成
    Then 回调 SHALL 被调用
    And 参数 SHALL 包含 fitness_values, evaluation_time

  Scenario: on_termination 回调
    Given 注册了 on_termination 回调
    When 引擎终止
    Then 回调 SHALL 被调用
    And 参数 SHALL 包含 termination_reason, total_generations, best_individual
```
