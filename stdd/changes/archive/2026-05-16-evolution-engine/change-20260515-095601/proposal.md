# Change Proposal: Agent Genetic Evolution Engine

> Type: feature | Priority: high | Status: Confirmed
> Created: 2026-05-15 | Confirmed: 2026-05-15

---

## 1. Intent (意图)

实现一个遗传算法（GA）进化引擎，用于 Agent 参数空间的自动化搜索和优化。通过基因组编码、适应度评估、选择/交叉/变异算子实现 Agent 种群的世代进化。

**核心价值**：
- 将 Agent 参数序列化为可操作的基因组
- 提供可扩展的适应度函数框架
- 多种经典选择/交叉/变异算子开箱即用
- 完整的进化循环管理（种群初始化 → 评估 → 选择 → 繁殖 → 终止）

---

## 2. Scope (范围)

### In Scope (本期实现)

| # | 子系统 | 核心能力 | 技术选型 |
|---|--------|---------|---------|
| 1 | 基因组编码 | Agent 参数序列化/反序列化、实数/二进制/树形编码 | Python dataclass + numpy |
| 2 | 适应度函数 | 自定义评估指标、多目标加权、约束处理 | Callable Protocol |
| 3 | 选择算子 | 轮盘赌、锦标赛、精英保留、排序选择 | numpy |
| 4 | 交叉算子 | 单点、多点、均匀、SBX（模拟二进制） | numpy |
| 5 | 变异算子 | 高斯、均匀、位翻转、多项式 | numpy |
| 6 | 进化循环 | 种群管理、世代交替、终止条件、精英策略 | async pipeline |

### Out of Scope (不在本期)

- 多目标进化算法（NSGA-II、MOEA/D）
- 约束优化（罚函数法外）
- 并行/分布式适应度评估
- 协同进化（竞争/合作物种）
- 基因组可视化
- 与 agentforge Agent 的自动参数绑定（本期手动编解码）

---

## 3. Approach (方案)

### 3.1 架构分层

```
┌───────────────────────────────────────────┐
│        Evolution Pipeline                  │
│  (EvolutionEngine / TerminationCriteria)  │
├───────────────────────────────────────────┤
│  Selection  │  Crossover  │  Mutation     │
│  Operators  │  Operators  │  Operators    │
├───────────────────────────────────────────┤
│        Fitness Framework                   │
│  (FitnessFunction / MultiObjective)       │
├───────────────────────────────────────────┤
│        Genome Encoding                     │
│  (RealEncoder / BinaryEncoder / Tree)     │
├───────────────────────────────────────────┤
│        Population Management               │
│  (Population / Individual / Statistics)   │
└───────────────────────────────────────────┘
```

### 3.2 分期建议

**Epic 检测**：6 个子系统，但耦合度较高（算子共享基因组接口），建议分 2 期：

- **Phase 1（核心管线）**：基因组编码 + 适应度框架 + 进化循环 + 种群管理
- **Phase 2（算子库）**：选择/交叉/变异全部算子实现

### 3.3 关键设计决策（已确认）

| # | 问题 | 决策 |
|---|------|------|
| 1 | 基因组编码 | **全部实现**：实数向量 + 二进制位串 + 树形 |
| 2 | 适应度评估 | **支持异步**（anyio） |
| 3 | 种群规模 | **默认 100，可配置** |
| 4 | 终止条件 | **组合**：最大世代数 + 适应度阈值 + 收敛检测（OR 语义） |
| 5 | 精英策略 | **可选，默认关闭**，用户手动启用 |
| 6 | 随机数控制 | numpy Generator + 可 seed |
| 7 | 日志方案 | structlog |
| 8 | 包名 | **evoforge**（agentforge 子模块） |
| 9 | 项目关系 | **agentforge 子模块**，共享依赖 |
| 11 | 算子接口 | **统一接口 + 内部分发**（基于 Genome Protocol） |
| 12 | 树形编码 | **完整 GP**（含自动函数发现、ADF） |
| 13 | 约束处理 | **多层**：边界裁剪 + 罚函数 + 修复算子 |
| 14 | batch 评估 | **支持**（适应度函数接受整个种群） |
| 15 | 回调系统 | **支持**（on_generation_end / on_evaluation / on_termination） |
| 16 | 收敛检测 | **两者都支持**（best 停滞 + 种群多样性，OR 组合） |
| 17 | 项目位置 | **agentforge/evoforge/ 子包** |

---

## 4. Success Criteria (验收标准)

### 功能验收

- [ ] 基因组可编码/解码 Agent 参数（实数向量至少 100 维）
- [ ] 自定义适应度函数可注册并正确评估
- [ ] 轮盘赌选择概率分布正确
- [ ] 锦标赛选择返回最优个体
- [ ] 精英保留确保最优个体不丢失
- [ ] 单点/多点/均匀交叉正确产生后代
- [ ] 高斯变异改变基因值且在范围内
- [ ] 进化循环正确执行 世代初始化 → 评估 → 选择 → 交叉 → 变异 → 替换
- [ ] 种群统计（best/mean/std）每代可查询

### 质量验收

- [ ] 核心模块测试覆盖率 ≥ 85%
- [ ] 所有算子有独立单元测试
- [ ] 种子控制确保进化可复现
- [ ] 进化过程可通过回调/log追踪

---

## 5. Risks & Open Questions (风险与待确认)

### 风险

| # | 风险 | 影响 | 缓解措施 |
|---|------|------|---------|
| 1 | 算子与基因组编码耦合 | 新编码需重写所有算子 | 算子基于 Genome Protocol 抽象 |
| 2 | 大种群评估性能 | 适应度计算成为瓶颈 | 支持 batch 评估 |
| 3 | 早熟收敛 | 种群多样性丧失太快 | 提供多样性监控指标 |

### 已确认

| # | 问题 | 决策 |
|---|------|------|
| 1 | 基因组编码 | **全部实现**：实数向量 + 二进制位串 + 树形 |
| 2 | 适应度异步 | **支持 anyio 异步**评估 |
| 3 | 包名 | **evoforge** |
| 4 | 项目关系 | **agentforge 子模块** |
| 5 | 种群规模 | **默认 100，可配置** |
| 6 | 终止条件 | **组合**（最大世代 / 阈值 / 收敛，OR 语义） |
| 7 | 精英策略 | **可选，默认关闭** |
| 8 | 日志 | structlog |

---

## 6. References (参考)

- Holland, J.H. (1975) "Adaptation in Natural and Artificial Systems"
- DEAP: https://deap.readthedocs.io/
- PyGAD: https://pygad.readthedocs.io/
