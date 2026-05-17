# Delta Spec: Evolution Engine

> Change: change-20260515-095601 | Domain: engine | Type: ADDED
> Status: Updated to reflect actual implementation

---

## Feature: Population Management

```gherkin
Feature: 种群管理
  Population 类管理种群的创建、统计和排序。

  Scenario: 初始化随机种群
    Given 种群大小=100, genome_factory 函数, rng
    When 调用 Population.random(genome_factory, size=100, rng)
    Then SHALL 生成 100 个 Individual 对象
    And 每个 Individual.generation SHALL 为 0
    And 每个 Individual.parents SHALL 为空列表

  Scenario: Individual 数据结构
    Given Individual 数据类
    Then SHALL 包含以下字段：
      | 字段       | 类型             | 描述             |
      | id         | UUID            | 自动生成唯一标识 |
      | genome     | Any             | 基因组对象       |
      | generation | int             | 当前代数         |
      | parents    | list[UUID]      | 父代 UUID 列表（lineage tracking） |
      | fitness    | float | None    | 适应度值         |

  Scenario: 种群统计
    Given 种群已评估（所有 individual.fitness 有值）
    When 调用 population.stats()
    Then SHALL 返回:
      | metric   | description          |
      | best     | 最优个体适应度        |
      | mean     | 平均适应度            |
      | worst    | 最差适应度            |
      | std      | 适应度标准差          |
      | diversity| 与 std 相同（简化实现）|

  Scenario: 种群排序
    Given 种群已评估
    When 调用 population.sort_by_fitness(reverse=True)
    Then 最优个体 SHALL 排在首位
```

## Feature: Evolution Loop

```gherkin
Feature: 进化主循环
  EvolutionEngine 执行完整的进化循环。

  Scenario: 标准进化流程
    Given 种群已初始化
    When 调用 engine.evolve(population)
    Then SHALL 循环执行直到终止条件满足：
      | step     | operation                     |
      | 1        | 评估适应度（调用 fitness_fn）  |
      | 2        | 触发 on_evaluation 回调        |
      | 3        | 计算种群统计                   |
      | 4        | 触发 on_generation_end 回调    |
      | 5        | 检查终止条件                   |
      | 6        | 创建下一代（选择+交叉+变异+精英保留）|

  Scenario: 精英保留
    Given elite_size=2
    When 创建下一代
    Then 最优的 2 个个体 SHALL 通过 genome.clone() 复制到下一代
    And 精英个体的 parents 列表 SHALL 为 [自身 id]
    And 精英个体 SHALL NOT 参与交叉和变异

  Scenario: 选择+交叉+变异流程
    Given 种群需要补充新个体
    When 生成每个子代
    Then SHALL 先通过 tournament_selection 选择 2 个父代
    And 如果 crossover_fn 存在且随机数 < crossover_rate 则交叉
    And SHALL 对子代基因组应用 mutation_fn
    And 子代的 parents SHALL 记录两个父代 id

  Scenario: 种子控制可复现
    Given seed=42
    When 运行进化引擎 50 代
    And 使用相同 seed=42 再次运行
    Then 每代的 best_fitness 序列 SHALL 完全一致
```

## Feature: Agent Personality Optimization Mode

```gherkin
Feature: 智能体人格优化模式
  app.py 中 EvolutionRun 支持两种优化模式。

  Scenario: agent 模式（人格参数优化）
    Given config.mode = "agent"
    When 创建进化运行
    Then 基因组维度 SHALL 默认 10 维
    And 每个基因 SHALL 通过 sigmoid 映射到 [0,1] 区间
    And 基因语义 SHALL 为 10 个人格维度：
      [temperature_scale, creativity, conciseness, formality,
       technical_depth, empathy, assertiveness, humor, detail_level, brevity]
    And 适应度函数 SHALL 包含：
      | 组件      | 计算                                        |
      | balance   | -|mean(traits) - 0.5| * 2（奖励均值接近 0.5）|
      | diversity | std(traits) * 2（奖励多样性）                |
      | extremes  | -sum(max(0, t-0.9) + max(0, 0.1-t)) * 3（惩罚极端值）|
      | coherence | -|conciseness - (1-detail_level)| * 0.5（一致性约束）|

  Scenario: sphere 模式（经典基准）
    Given config.mode = "sphere"
    When 创建进化运行
    Then 适应度函数 SHALL 为负球面函数：-sum(gene^2)
    And 全局最优 SHALL 在全零向量处
```

## Feature: Gene Tree Data Collection

```gherkin
Feature: 基因树数据收集
  StreamCallback 在每代结束时收集基因树数据。

  Scenario: 节点数据
    Given 每代结束
    When StreamCallback.on_generation_end 被调用
    Then SHALL 遍历 population.individuals
    And 收集每个个体的 {id, generation, fitness}
    And fitness SHALL 保留 4 位小数

  Scenario: 边数据（父子关系）
    Given 每个个体有 parents 列表
    When 收集边数据
    Then SHALL 为每个 parent_id → individual.id 创建一条边 {source, target}

  Scenario: 数据上限
    Given 种群较大
    When 收集树数据
    Then 节点 SHALL 上限 100 个
    And 边 SHALL 上限 200 条
    And SHALL 取最新的数据（slice 从末尾取）
```

## Feature: Termination Criteria

```gherkin
Feature: 终止条件
  TerminationCriteria 支持组合终止条件（OR 语义）。

  Scenario: 最大世代数终止
    Given 终止条件 max_generations=100
    When 进化到第 100 代
    Then 引擎 SHALL 终止，reason="MAX_GENERATIONS"

  Scenario: 适应度阈值终止
    Given 终止条件 fitness_threshold=0.99
    When 最优适应度 >= 0.99
    Then 引擎 SHALL 终止，reason="FITNESS_THRESHOLD"

  Scenario: 收敛检测
    Given 终止条件 convergence_generations=20, convergence_threshold=1e-6
    When 最优适应度连续 20 代变化幅度 < 1e-6
    Then 引擎 SHALL 终止，reason="CONVERGENCE"

  Scenario: 组合条件 OR 语义
    Given 终止条件为 max_gen=200, fitness_threshold=0.99, convergence_generations=30
    When 任一条件满足
    Then 引擎 SHALL 终止

  Note: 种群多样性终止条件 NOT_IMPLEMENTED — TerminationCriteria 无 diversity_threshold 参数。
```

## Feature: Callbacks

```gherkin
Feature: 进化回调
  系统支持通过 Callback 基类注入自定义逻辑。

  Scenario: on_generation_end 回调
    Given 注册了 Callback 子类
    When 每代进化完成
    Then on_generation_end SHALL 被调用
    And 参数 SHALL 包含 GenerationStats 和 Population

  Scenario: on_evaluation 回调
    Given 注册了 Callback 子类
    When 种群评估完成
    Then on_evaluation SHALL 被调用
    And 参数 SHALL 包含 population.individuals 和 fitnesses 列表

  Scenario: on_termination 回调
    Given 注册了 Callback 子类
    When 引擎终止
    Then on_termination SHALL 被调用
    And 参数 SHALL 包含 reason 字符串和 GenerationStats

  Scenario: CompositeCallback 组合回调
    Given 注册了多个 Callback
    When 事件触发
    Then CompositeCallback SHALL 依次调用所有回调

  Scenario: GenerationStats 数据结构
    Given GenerationStats 数据类
    Then SHALL 包含：
      | 字段               | 类型   |
      | generation         | int    |
      | best_fitness       | float  |
      | mean_fitness       | float  |
      | std_fitness        | float  |
      | diversity          | float  |
      | best_individual_id | str    |
      | timestamp          | str    |
```
