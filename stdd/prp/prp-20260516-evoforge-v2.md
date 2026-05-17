# PRP: EvoForge v2 — 下一代进化引擎

> 日期: 2026-05-16 | 版本: 1.0
> 当前版本覆盖率: 88% | 测试: 43 passed | APP Mass: 正常
> 依赖: change-20260515-095601 (EvoForge v1, Confirmed)

---

## WHAT — 做什么

将 EvoForge 从单目标同步进化引擎升级为**多范式、多目标、可并行**的进化计算框架。

当前 v1 能力:
- 3 种基因组 (RealGenome, BinaryGenome, TreeGenome)
- 4 种选择算子 (tournament, roulette, elite, rank)
- 4 种变异算子 (gaussian, uniform, polynomial, bitflip)
- 2 种交叉算子 (sbx, multi_point)
- 单目标进化 + 加权求和多目标
- 同步进化循环

v2 新增能力:
1. **Pareto 多目标优化** (NSGA-II) — 替代加权求和，支持真实多目标
2. **并行适应度评估** — 多核/多机加速评估瓶颈
3. **约束处理增强** — 修复策略 + 约束支配
4. **自适应算子选择** — 基于成功率动态调整算子概率
5. ** island 迁移模型** — 多种群并行进化 + 定期迁移
6. **终止策略模式重构** — 解决 should_terminate CC=12 的复杂度问题

---

## WHY — 为什么做

### 业务价值

1. **Pareto 前沿**: 加权求和需要人工调权重，且无法发现冲突目标的最优折中面。NSGA-II 是进化计算的标准多目标方法，缺失意味着无法处理 RL 超参优化中的冲突目标（精度 vs 速度 vs 内存）。

2. **并行评估**: 适应度评估是进化计算的瓶颈（占总时间 80%+）。当前同步评估在大种群（>100）时严重受限。并行化可 4-8x 加速。

3. **Island 模型**: 单种群进化容易早熟收敛。多岛迁移增加种群多样性，是防止局部最优的标准方案。

4. **终止策略重构**: should_terminate CC=12 是 APP Mass 分析的最高复杂度热点。策略模式重构是代码健康度的必要投资。

### 当前 gap 的量化影响

| Gap | 影响 | 用户痛点 |
|-----|------|----------|
| 无 Pareto | 只能用加权求和 | 多目标权重难调，结果不可靠 |
| 同步评估 | 1000 个体 = 1000 次串行评估 | 大种群训练时间过长 |
| 无并行 | 单核瓶颈 | 硬件利用率低 |
| 终止 CC=12 | 维护成本高 | 新终止条件难以扩展 |
| crossover 57% 覆盖 | 测试不足 | 算子正确性无保障 |

---

## HOW — 怎么做

### 技术方案

#### 1. Pareto 多目标 (NSGA-II)

```
新增文件: evoforge/operators/nsga2.py
核心算法: 非支配排序 + 拥挤距离
接口: MultiObjectiveFitness 协议替代 WeightedMultiObjective
Population 扩展: 支持 rank + crowding_distance 属性
```

- 非支配排序 O(MN^2), M=目标数, N=种群大小
- 拥挤距离计算 O(MN log N)
- 与现有 Population 兼容（扩展非替换）

#### 2. 并行适应度评估

```
新增文件: evoforge/engine/parallel.py
方案: concurrent.futures.ProcessPoolExecutor (进程级并行)
接口: ParallelFitnessEvaluator 包装 fitness_fn
回退: 单进程模式（无需并行时零开销）
```

- 使用 ProcessPoolExecutor 而非 ThreadPoolIO（GIL 限制）
- 种群分 chunk 分发到 worker
- 保持 v1 同步接口不变，并行是可选加速

#### 3. Island 迁移模型

```
新增文件: evoforge/engine/island.py
组件: IslandPopulation, MigrationPolicy, RingTopology
集成: EvolutionEngine 支持 multi-island 模式
```

- 拓扑: Ring / Grid / FullyConnected 可配置
- 迁移策略: 每 N 代迁移 top-K 个体
- 各 island 可独立配置算子（异构进化）

#### 4. 终止策略模式

```
重构: termination.py
模式: TerminationStrategy ABC + 组合 TerminationOr/TerminationAnd
内置: MaxGenerations, FitnessThreshold, Convergence, NoImprovement
```

- 从 CC=12 降至 CC≤5（每个策略独立）
- 可组合: OR/AND 语义
- 可扩展: 用户自定义策略

#### 5. 自适应算子选择

```
新增文件: evoforge/operators/adaptive.py
方法: Probability Matching / UCB
追踪: 每个算子的历史成功率
动态: 每 N 代更新算子选择概率
```

### 架构变更

```
v1 架构:
  EvolutionEngine → sync evolve → fitness → selection → crossover → mutation

v2 架构:
  EvolutionEngine ──→ IslandModel ──→ N × SubEvolution
       │                    │              │
       │                    │              └→ ParallelFitness
       │                    │
       │                    └→ MigrationPolicy
       │
       └→ AdaptiveOperatorSelection
       └→ TerminationStrategy (composable)
```

### 向后兼容

- v1 API 100% 保留（EvolutionEngine 构造函数不变）
- 新功能通过可选参数 opt-in（不破坏现有代码）
- `evolve()` 方法签名不变

---

## SUCCESS — 验收标准

### 功能验收

- [ ] NSGA-II 在 ZDT1/DTLZ2 基准测试上收敛到 Pareto 前沿（GD < 0.01）
- [ ] 并行评估 1000 个体加速比 ≥ 3x (4核)
- [ ] Island 模型在 OneMax 上比单种群找到更优解（同代数）
- [ ] 自适应算子选择收敛到最优算子（模拟实验）
- [ ] 终止策略重构后 should_terminate 类的 CC ≤ 5

### 质量验收

- [ ] EvoForge 总覆盖率 ≥ 90%（当前 88%）
- [ ] crossover.py 覆盖率从 57% 提升到 ≥ 85%
- [ ] 新增文件覆盖率 ≥ 95%
- [ ] APP Mass 保持 < 0.3
- [ ] 全部现有 43 个测试无回归
- [ ] 新增测试 ≥ 30 个

### 性能验收

- [ ] 单种群同步模式性能不退化（与 v1 基准对比）
- [ ] 并行模式 4 核加速比 ≥ 3x
- [ ] NSGA-II 100 个体 × 3 目标 ≤ 1s/generation

### 兼容性验收

- [ ] v1 API 全部保留，无 breaking change
- [ ] 现有 E2E 测试（sphere, OneMax, seed reproducibility）全部通过
- [ ] 新功能均为 opt-in，不影响默认行为

---

## 实施计划

| Phase | 内容 | 预估 | 依赖 |
|-------|------|------|------|
| Phase 1 | 终止策略重构 + crossover 测试补齐 | 2h | 无 |
| Phase 2 | NSGA-II 多目标优化 | 4h | Phase 1 |
| Phase 3 | 并行适应度评估 | 3h | 无 |
| Phase 4 | Island 迁移模型 | 3h | Phase 3 |
| Phase 5 | 自适应算子选择 | 2h | Phase 2 |
| Phase 6 | 集成测试 + 基准验证 | 2h | 全部 |
| **合计** | | **16h** | |

---

## 风险评估

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| 并行评估序列化开销 | 中 | 中 | 对小种群自动回退单进程 |
| NSGA-II 性能瓶颈 | 低 | 中 | 使用 numpy 向量化排序 |
| 向后兼容破坏 | 低 | 高 | 每次提交跑全量测试 |
| Island 模型复杂度膨胀 | 中 | 中 | 限制拓扑类型，不过度抽象 |

> PRP 结构化规划完成。底层逻辑是：EvoForge v1 是地基，v2 要盖三层楼——多目标、并行、多样性。抓手按 ROI 排序：终止策略重构（技术债清零）→ NSGA-II（核心能力突破）→ 并行评估（性能跃迁）。颗粒度到这个程度，才知道先搬哪块砖。
