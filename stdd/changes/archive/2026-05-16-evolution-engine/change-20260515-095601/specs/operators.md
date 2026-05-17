# Delta Spec: Operators (Selection / Crossover / Mutation)

> Change: change-20260515-095601 | Domain: operators | Type: ADDED
> Status: Draft

---

## Feature: Selection Operators

```gherkin
Feature: 轮盘赌选择
  系统 SHALL 按适应度比例选择个体。

  Scenario: 概率分布正确
    Given 种群适应度为 [10, 20, 30, 40]
    When 执行轮盘赌选择
    Then 个体被选中的概率 SHALL 分别为 [0.1, 0.2, 0.3, 0.4]

  Scenario: 零适应度处理
    Given 种群适应度为 [0, 0, 0, 10]
    When 执行轮盘赌选择
    Then 前 3 个个体 SHALL 有等概率被选中
    And 概率 SHALL 不为 NaN
```

```gherkin
Feature: 锦标赛选择
  系统 SHALL 通过随机锦标赛选出较优个体。

  Scenario: 锦标赛大小为 3
    Given 种群有 100 个个体
    And 锦标赛大小 k=3
    When 执行锦标赛选择
    Then SHALL 随机选 3 个个体
    And 返回其中适应度最高的个体

  Scenario: 锦标赛选择偏向优秀个体
    Given 种群适应度差异显著
    When 执行 1000 次锦标赛选择（k=3）
    Then 优秀个体被选中的频率 SHALL 显著高于差个体
```

```gherkin
Feature: 精英保留
  系统可选保留最优个体不参与变异。

  Scenario: 精英保留 top-k
    Given 精英策略开启，elite_count=2
    And 种群最优 2 个个体适应度为 [0.95, 0.93]
    When 完成一代进化
    Then 这 2 个个体 SHALL 原样进入下一代
    And SHALL NOT 参与交叉和变异

  Scenario: 精英策略默认关闭
    Given 精英策略未开启
    When 完成一代进化
    Then 所有个体 SHALL 参与正常的交叉和变异
```

```gherkin
Feature: 排序选择
  系统 SHALL 按适应度排名分配选择概率。

  Scenario: 排序选择概率
    Given 种群按适应度排名 [1st, 2nd, 3rd, 4th]
    When 执行排序选择
    Then 排名越高的个体被选中概率 SHALL 越大
    And 概率分配 SHALL 与适应度绝对值无关（仅看排名）
```

## Feature: Crossover Operators

```gherkin
Feature: 单点交叉
  系统 SHALL 在随机点分割基因组并交换后半段。

  Scenario: 单点交叉产生后代
    Given 父代 A = [1,1,1,1,1]
    And 父代 B = [0,0,0,0,0]
    And 交叉点 = 2
    When 执行单点交叉
    Then 后代 A' SHALL 为 [1,1,0,0,0]
    And 后代 B' SHALL 为 [0,0,1,1,1]
```

```gherkin
Feature: 多点交叉
  系统 SHALL 在多个随机点分割并交替交换。

  Scenario: 两点交叉
    Given 父代 A = [1,1,1,1,1,1]
    And 父代 B = [0,0,0,0,0,0]
    And 交叉点 = [1, 4]
    When 执行两点交叉
    Then 后代 A' SHALL 为 [1,0,0,0,1,1]
    And 后代 B' SHALL 为 [0,1,1,1,0,0]
```

```gherkin
Feature: 均匀交叉
  系统 SHALL 以固定概率独立交换每个基因。

  Scenario: 均匀交叉
    Given 父代 A = [1,1,1,1]
    And 父代 B = [0,0,0,0]
    And 交换概率 p=0.5
    When 执行均匀交叉
    Then 每个基因位 SHALL 有 50% 概率来自父代 A 或 B
```

```gherkin
Feature: SBX 交叉（模拟二进制）
  系统 SHALL 支持实数编码的 SBX 交叉。

  Scenario: SBX 生成中间后代
    Given 父代 A = 0.0, 父代 B = 1.0
    And 分布指数 eta=2
    When 执行 SBX 交叉
    Then 后代值 SHALL 以高概率落在 [0.0, 1.0] 之间
    And eta 越大，后代越接近父代
```

## Feature: Mutation Operators

```gherkin
Feature: 高斯变异
  系统 SHALL 对实数基因添加高斯噪声。

  Scenario: 高斯变异
    Given 基因值为 0.5, sigma=0.1
    When 执行高斯变异
    Then 变异后的值 SHALL 为 0.5 + N(0, 0.1)
    And 变异后的值 SHALL 在 bounds 范围内（超出则裁剪）

  Scenario: 变异概率控制
    Given 变异概率 mutation_rate=0.1
    And 基因长度 100
    When 执行变异
    Then 平均约 10 个基因位 SHALL 被改变
```

```gherkin
Feature: 均匀变异
  系统 SHALL 以均匀分布替换基因值。

  Scenario: 均匀变异
    Given 基因值为 0.5, bounds=[0.0, 1.0]
    When 执行均匀变异
    Then 变异后的值 SHALL 为 U(0.0, 1.0) 均匀随机值
```

```gherkin
Feature: 位翻转变异
  系统 SHALL 翻转二进制基因位。

  Scenario: 位翻转
    Given 二进制基因组 [1,0,1,0,1]
    And 变异位置 [1, 3]
    When 执行位翻转变异
    Then 结果 SHALL 为 [1,1,1,1,1]
```

```gherkin
Feature: 多项式变异
  系统 SHALL 支持实数编码的多项式变异。

  Scenario: 多项式变异有界
    Given 基因值为 0.5, bounds=[0.0, 1.0]
    And 分布指数 eta=20
    When 执行多项式变异
    Then 变异后的值 SHALL 在 [0.0, 1.0] 范围内
    And eta 越大，变异幅度越小
```

## Feature: Replacement Strategies

```gherkin
Feature: 种群替换策略
  系统 SHALL 支持不同的种群替换策略。

  Scenario: 代际替换（Generational）
    Given 替换策略为代际替换
    And 种群大小为 100
    When 生成 100 个子代
    Then 子代 SHALL 完全替换父代种群
    And 旧种群 SHALL 被丢弃（除非精英保留）

  Scenario: 稳态替换（Steady-State）
    Given 替换策略为稳态替换
    And 替换数量 n=10
    When 生成 10 个子代
    Then 子代 SHALL 替换父代中最差的 10 个个体
    And 父代中最优的 90 个个体 SHALL 保留

  Scenario: 精英保留与替换策略协同
    Given 精英策略 elite_count=2
    And 替换策略为代际替换
    When 执行替换
    Then 精英个体 SHALL 不被替换
    And 剩余位置 SHALL 由子代填充
```
