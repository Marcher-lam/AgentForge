# Delta Spec: Operators (Selection / Crossover / Mutation)

> Change: change-20260515-095601 | Domain: operators | Type: ADDED
> Status: Updated to reflect actual implementation

---

## Feature: Selection Operators

```gherkin
Feature: 轮盘赌选择
  roulette_selection 按适应度比例选择个体。

  Scenario: 概率分布正确
    Given 种群适应度为 [10, 20, 30, 40]
    When 执行轮盘赌选择
    Then 个体被选中的概率 SHALL 分别为 [0.1, 0.2, 0.3, 0.4]
    And SHALL 使用 fitness - min + 1e-10 确保非负

  Scenario: 零适应度处理
    Given 种群适应度为 [0, 0, 0, 10]
    When 执行轮盘赌选择
    Then SHALL 通过 +1e-10 确保概率不为 NaN
    And 所有个体 SHALL 有非零概率被选中
```

```gherkin
Feature: 锦标赛选择
  tournament_selection 通过随机锦标赛选出较优个体。

  Scenario: 锦标赛大小为 3
    Given 种群有 100 个个体，锦标赛大小 k=3
    When 执行锦标赛选择
    Then SHALL 随机选 3 个个体（replace=False）
    And 返回其中适应度最高的个体

  Scenario: 默认锦标赛大小
    Given 调用 tournament_selection 未指定 k
    Then k SHALL 默认为 3

  Scenario: 锦标赛选择偏向优秀个体
    Given 种群适应度差异显著
    When 执行 1000 次锦标赛选择（k=3）
    Then 优秀个体被选中的频率 SHALL 显著高于差个体
```

```gherkin
Feature: 精英选择
  elite_selection 返回适应度最高的 top-n 个体。

  Scenario: 精英选择 top-n
    Given 种群有 100 个个体
    When 调用 elite_selection(population, n=5)
    Then SHALL 返回适应度最高的 5 个个体
```

```gherkin
Feature: 排序选择
  rank_selection 按适应度排名分配选择概率。

  Scenario: 排序选择概率
    Given 种群按适应度排名
    When 执行排序选择
    Then 排名越高的个体被选中概率 SHALL 越大
    And 概率分配 SHALL 与适应度绝对值无关（仅看排名）
    And 概率 SHALL 正比于排名值（非指数）
```

## Feature: Crossover Operators

```gherkin
Feature: 单点交叉
  single_point_crossover 委托给基因组的 crossover 方法。

  Scenario: 单点交叉
    Given 父代 A 和 B 有 RealGenome 类型
    When 调用 single_point_crossover(A, B, rng)
    Then SHALL 委托给 A.crossover(B, rng)
    And RealGenome.crossover 实现为均匀交叉（非传统单点交叉）

  Note: single_point_crossover 函数名暗示单点交叉，但对 RealGenome 实际执行的是
  基因组自身的 crossover 方法（均匀交叉）。函数本身只是委托。
```

```gherkin
Feature: 多点交叉
  multi_point_crossover 在多个随机点分割并交替交换。

  Scenario: 两点交叉
    Given 父代 A = [1,1,1,1,1,1] 和 B = [0,0,0,0,0,0]
    And 交叉点 = [1, 4]
    When 执行两点交叉
    Then SHALL 在两个点之间交换片段
    And 结果取决于交换的起始奇偶性
```

```gherkin
Feature: 均匀交叉
  uniform_crossover 委托给基因组的 crossover 方法。

  Scenario: 均匀交叉
    Given 父代 A 和 B 有 RealGenome 类型
    When 调用 uniform_crossover(A, B, rng)
    Then SHALL 委托给 A.crossover(B, rng)
    And 每个基因位 SHALL 有 50% 概率来自父代 A 或 B
```

```gherkin
Feature: SBX 交叉（模拟二进制）
  sbx_crossover 对实数编码执行模拟二进制交叉。

  Scenario: SBX 生成中间后代
    Given 父代 A.genes 和 B.genes 为实数向量
    And 分布指数 eta=2
    When 执行 SBX 交叉
    Then 每个基因位 SHALL 有 50% 概率执行交叉
    And 交叉值 SHALL 通过 beta 系数计算
    And eta 越大，后代越接近父代
    And 后代 SHALL 继承父代的 bounds
```

## Feature: Mutation Operators

```gherkin
Feature: 高斯变异
  gaussian_mutation 对实数基因添加高斯噪声。

  Scenario: 高斯变异
    Given 基因值为 0.5, sigma=1.0
    When 执行高斯变异 (rate=1.0)
    Then 变异后的值 SHALL 为 0.5 + N(0, 1.0)
    And 变异后的值 SHALL 在 bounds 范围内（np.clip）
    And 默认 sigma SHALL 为 1.0

  Scenario: 变异概率控制
    Given 变异概率 mutation_rate=0.1，基因长度 100
    When 执行变异
    Then 每个基因位独立地有 10% 概率被改变

  Scenario: 降级到基因组方法
    Given 基因组没有 genes 属性（非 ndarray）
    When 执行高斯变异
    Then SHALL 委托给 genome.mutate(rate, rng)
```

```gherkin
Feature: 均匀变异
  uniform_mutation 以均匀分布替换基因值。

  Scenario: 均匀变异
    Given 基因值为 0.5, bounds=[0.0, 1.0]
    When 执行均匀变异
    Then 被选中的基因值 SHALL 替换为 U(lo, hi) 均匀随机值

  Scenario: 需要 bounds 属性
    Given 基因组没有 bounds 属性
    When 执行均匀变异
    Then SHALL 委托给 genome.mutate(rate, rng)
```

```gherkin
Feature: 位翻转变异
  bitflip_mutation 翻转二进制基因位。

  Scenario: 位翻转
    Given 二进制基因组 genes = np.array([True, False, True, False, True])
    And 变异位置由 rate 随机决定
    When 执行位翻转变异
    Then 被选中的位 SHALL 取反 (~)
    And 仅对 dtype == bool 的基因组生效
```

```gherkin
Feature: 多项式变异
  polynomial_mutation 执行有界多项式变异。

  Scenario: 多项式变异有界
    Given 基因值为 0.5, bounds=[0.0, 1.0]
    And 分布指数 eta=20
    When 执行多项式变异
    Then 变异后的值 SHALL 在 [0.0, 1.0] 范围内
    And eta 越大，变异幅度越小
    And delta SHALL 通过多项式分布计算
```

## Feature: Replacement Strategies

```gherkin
Feature: 种群替换策略
  EvolutionEngine 使用代际替换策略。

  Scenario: 代际替换（Generational）
    Given 替换策略为代际替换（默认行为）
    And 种群大小为 N
    When 生成下一代
    Then 子代 SHALL 完全替换父代种群
    And 旧种群 SHALL 被丢弃（除非精英保留）

  Scenario: 精英保留与替换策略协同
    Given 精英策略 elite_size=2
    And 替换策略为代际替换
    When 执行替换
    Then 精英个体 SHALL 通过 clone() 复制到下一代
    And 精英的 parents SHALL 为 [自身 id]
    And 剩余位置 SHALL 由选择+交叉+变异产生的子代填充

  Note: 稳态替换（Steady-State）NOT_IMPLEMENTED —
  EvolutionEngine 仅支持代际替换。
  没有稳态替换策略选项（保留父代最优 N 个，仅替换最差的 K 个）。
```
