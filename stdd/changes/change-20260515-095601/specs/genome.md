# Delta Spec: Genome Encoding

> Change: change-20260515-095601 | Domain: genome | Type: ADDED
> Status: Draft

---

## Feature: Real Genome (实数向量)

```gherkin
Feature: 实数向量基因组编码
  系统 SHALL 支持实数向量编码，至少支持 100 维。

  Scenario: 创建实数基因组
    Given 一个维度为 50 的实数向量
    When 创建实数基因组(genes=[0.1, 0.2, 0.3, 0.4, 0.5])
    Then genome.genes SHALL 为长度 50 的数值数组
    And genome.size SHALL 为 50

  Scenario: 100 维基因组
    Given 一个维度为 100 的实数向量
    When 创建 RealGenome(genes=random_vector(100))
    Then SHALL 成功创建
    And genome.size SHALL 为 100

  Scenario: 基因值边界约束
    Given RealGenome 设置了 bounds=[(0.0, 1.0)] * 10
    When 创建基因组时某个基因值为 1.5
    Then 该基因值 SHALL 被裁剪到 1.0（边界裁剪）

  Scenario: 编码/解码 Agent 参数
    Given Agent 参数 {"lr": 0.001, "hidden": 256, "dropout": 0.1}
    When 通过 GenomeCodec 编码为基因组
    Then SHALL 产生一个实数向量
    When 通过 GenomeCodec 解码回来
    Then SHALL 还原为 {"lr": 0.001, "hidden": 256, "dropout": 0.1}
```

## Feature: Binary Genome (二进制位串)

```gherkin
Feature: 二进制位串基因组编码
  系统 SHALL 支持二进制位串编码。

  Scenario: 创建二进制基因组
    Given 一个长度为 32 的位串
    When 创建 BinaryGenome(bits=[1,0,1,1,0,1,0,1])
    Then genome.bits SHALL 为长度 32 的布尔数组
    And genome.size SHALL 为 32

  Scenario: 位翻转约束
    Given BinaryGenome bits=[1,0,1,0]
    When 对 bit[1] 翻转
    Then bits SHALL 变为 [1,1,1,0]
```

## Feature: Tree Genome (树形编码)

```gherkin
Feature: 树形基因组编码（遗传编程）
  系统 SHALL 支持树形编码，用于遗传编程场景。

  Scenario: 创建树形基因组
    Given 一个表达式树 (+ (* x 2) y)
    When 创建 TreeGenome(root=Node("+", [Node("*", [Var("x"), Const(2)]), Var("y")]))
    Then genome.depth SHALL 为 2
    And genome.size SHALL 为 5（节点数）

  Scenario: 子树交换
    Given 父代 A 的树为 (+ x y)
    And 父代 B 的树为 (* x 2)
    When 交换 A 的右子树 "y" 和 B 的左子树 "x"
    Then 后代 A' SHALL 为 (+ x x)
    And 后代 B' SHALL 为 (* y 2)

  Scenario: 子树变异
    Given 树 (+ x y)
    When 对右子树 "y" 进行变异，替换为随机子树
    Then 变异后的树 SHALL 保持合法结构
```

## Feature: Genome Protocol

```gherkin
Feature: 基因组统一接口
  所有编码 SHALL 满足 Genome Protocol，算子通过统一接口操作。

  Scenario: Genome Protocol 方法
    Given Genome Protocol 定义
    Then 每个 Genome SHALL 实现:
      | method     | return type     |
      | size       | int            |
      | copy       | Genome         |
      | crossover  | Genome, Genome -> tuple[Genome, Genome] |
      | mutate     | Genome -> Genome |
```
