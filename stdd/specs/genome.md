# Delta Spec: Genome Encoding

> Change: change-20260515-095601 | Domain: genome | Type: ADDED
> Status: Updated to reflect actual implementation

---

## Feature: Real Genome (实数向量)

```gherkin
Feature: 实数向量基因组编码
  RealGenome 支持 numpy 数组编码，带边界约束。

  Scenario: 创建实数基因组
    Given 一个 numpy 数组 genes=[0.1, 0.2, 0.3]
    When 创建 RealGenome(genes=genes, bounds=[(0.0, 1.0)]*3)
    Then genome.genes SHALL 为 numpy ndarray
    And genome.bounds SHALL 为 [(0.0, 1.0)] * 3
    And genome.fitness SHALL 初始为 None

  Scenario: 默认边界
    Given 创建 RealGenome 未指定 bounds
    When __post_init__ 执行
    Then bounds SHALL 默认为 [(-10.0, 10.0)] * len(genes)

  Scenario: 基因值边界裁剪
    Given RealGenome bounds=[(0.0, 1.0)]*3
    When mutate 操作导致基因值超出边界
    Then SHALL 通过 np.clip 裁剪到边界内

  Scenario: crossover（均匀交叉）
    Given 父代 A 和父代 B
    When 调用 A.crossover(B, rng)
    Then SHALL 执行均匀交叉（每个基因 50% 概率来自任一父代）
    And SHALL 返回两个新的 RealGenome 子代
    And 子代 SHALL 继承父代的 bounds

  Scenario: mutate（高斯变异）
    Given RealGenome genes
    When 调用 genome.mutate(rate=0.1, rng)
    Then 每个基因 SHALL 有 rate 概率被添加 N(0, 1) 噪声
    And 变异后 SHALL 裁剪到 bounds 范围
    And SHALL 返回新的 RealGenome（不修改原对象）

  Scenario: clone
    Given 一个 RealGenome
    When 调用 genome.clone()
    Then SHALL 返回独立的深拷贝
    And genes SHALL 为 numpy copy
    And bounds SHALL 为新 list
    And fitness SHALL 保留

  Scenario: random 工厂方法
    Given length=50, bounds=[(0,1)]*50
    When 调用 RealGenome.random(length, bounds, rng)
    Then SHALL 在 bounds 范围内均匀随机生成基因值
```

Note: GenomeCodec（Agent 参数编解码）NOT_IMPLEMENTED — 实际实现中 app.py 的 agent 模式
直接使用 sigmoid 将基因映射到 [0,1]，没有独立的 GenomeCodec 类。

## Feature: Binary Genome (二进制位串)

```gherkin
Feature: 二进制位串基因组编码
  BinaryGenome 存在于 binary.py 模块中，支持布尔数组编码。

  Scenario: 创建二进制基因组
    Given 一个布尔数组
    When 创建 BinaryGenome
    Then genes SHALL 为 numpy bool 数组

  Scenario: 位翻转变异
    Given bitflip_mutation 操作符
    When 对 BinaryGenome 执行变异
    Then 每个位 SHALL 有 rate 概率被翻转
```

## Feature: Tree Genome (树形编码)

```gherkin
Feature: 树形基因组编码（遗传编程）
  TreeGenome 支持遗传编程的 AST 树结构。

  Scenario: 创建树形基因组
    Given 一个表达式树 (+ (* x 2) y)
    When 创建 TreeGenome(root=TreeNode("+", [TreeNode("*", [TreeNode("x"), TreeNode(2)]), TreeNode("y")]))
    Then root.depth() SHALL 返回 2
    And root.evaluate({"x": 3, "y": 1}) SHALL 返回 7.0

  Scenario: crossover（简化实现）
    Given 父代 A 和父代 B 的树
    When 执行 A.crossover(B, rng)
    Then SHALL 返回两个新的 TreeGenome
    Note: 当前实现仅做 root.copy()，未实现真正的子树交换。
    实际的子树交换 crossover NOT_IMPLEMENTED — 只返回父代的深拷贝。

  Scenario: mutate（简化实现）
    Given 树 (+ x y)
    When 执行 mutate(rate=0.1, rng)
    Then 仅对 root 节点有 rate 概率替换为随机终端值
    Note: 当前实现是 point mutation，仅替换根节点值。
    深层子树变异 NOT_IMPLEMENTED。

  Scenario: TreeNode 结构
    Given TreeNode 数据类
    Then SHALL 包含 value (str | float) 和 children (list[TreeNode])
    And 支持 depth(), copy(), evaluate(context) 方法

  Scenario: random 工厂方法
    Given variables=["x","y"], max_depth=4
    When 调用 TreeGenome.random(variables, max_depth, rng)
    Then SHALL 递归生成随机 AST 树
    And 终止条件为 depth >= max_depth 或 30% 随机概率
    And 操作符 SHALL 从 ["+", "-", "*"] 中随机选择
```

## Feature: Genome Protocol

```gherkin
Feature: 基因组统一接口
  所有编码满足 Genome Protocol (runtime_checkable)。

  Scenario: Genome Protocol 方法
    Given Genome Protocol 定义
    Then 每个 Genome SHALL 实现:
      | method     | signature                                  |
      | crossover  | (other, rng: Generator) -> tuple[Genome, Genome] |
      | mutate     | (rate: float, rng: Generator) -> Genome    |
      | clone      | () -> Genome                               |
      | fitness    | float | None 属性                           |
```
