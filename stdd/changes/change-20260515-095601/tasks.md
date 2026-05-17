# Task Breakdown: Evolution Engine (evoforge)

> Change: change-20260515-095601 | Priority: P1 | Depends on: none

---

## Task 1: Genome 编码层
- [x] 实现 Genome Protocol（crossover/mutate/fitness/getter）
- [ ] 实现 RealGenome（实数向量，bounds 约束）
- [ ] 实现 BinaryGenome（比特串）
- [ ] 实现 TreeGenome（GP 树 + ADF 支持）
- [ ] 实现 deep_copy / clone 工具方法
- [ ] 单元测试：三种编码的 crossover/mutate 正确性
- **预估**: 45min | **依赖**: 无

## Task 2: Fitness 函数 + 约束处理
- [x] 实现 FitnessFunction Protocol（evaluate 接受整个种群）
- [ ] 实现加权多目标适配器
- [ ] 实现三层约束：边界裁剪 → 惩罚函数 → 修复算子
- [ ] 单元测试：评估 + 多目标 + 约束处理
- **预估**: 30min | **依赖**: Task 1

## Task 3: 遗传算子
- [x] 实现 4 种选择（轮盘赌/锦标赛/精英/排序）
- [ ] 实现 4 种交叉（单点/多点/均匀/SBX）
- [ ] 实现 4 种变异（高斯/均匀/位翻转/多项式）
- [ ] 实现 operator dispatch（按 genome 类型自动分发）
- [ ] 单元测试：选择分布 + 交叉合法性 + 变异范围
- **预估**: 45min | **依赖**: Task 1

## Task 4: Population + 进化引擎
- [x] 实现 Population（默认 100，可配置，elite 策略可选）
- [ ] 实现进化主循环（select → crossover → mutate → evaluate → replace）
- [ ] 实现组合终止条件（max_gen OR fitness_threshold OR 收敛，OR 语义）
- [ ] 实现收敛检测（最优适应度停滞 + 种群多样性）
- [ ] 实现 numpy Generator + seed 可复现
- [ ] 单元测试：单代进化 + 终止条件 + seed 可复现
- **预估**: 45min | **依赖**: Task 2, Task 3

## Task 5: Callback 系统 + 统计
- [x] 实现 Callback（on_generation_end / on_evaluation / on_termination）
- [ ] 实现统计收集器（best/mean/std/diversity 每代）
- [ ] 实现进度日志（structlog）
- [ ] 实现 hook 机制（用户可插入自定义逻辑）
- [ ] 单元测试：callback 触发顺序 + 统计正确性
- **预估**: 25min | **依赖**: Task 4

## Task 6: 集成测试 + 覆盖率验证
- [x] OneMax 全流程集成测试（二进制基因组）
- [ ] Sphere 函数全流程集成测试（实数基因组）
- [ ] 符号回归集成测试（树基因组）
- [ ] 验证 seed 可复现性
- [ ] 验证测试覆盖率 ≥ 80%
- **预估**: 35min | **依赖**: Task 5
