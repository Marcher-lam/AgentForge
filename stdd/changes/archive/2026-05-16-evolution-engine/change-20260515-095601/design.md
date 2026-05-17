# Technical Design: Evolution Engine (evoforge)

> Change: change-20260515-095601 | No upstream dependency

---

## 1. Architecture Overview

```
┌────────────────────────────────────────────────────────────┐
│                      evoforge                               │
│                                                             │
│  ┌───────────────┐  ┌───────────────┐  ┌────────────────┐  │
│  │ Genome Layer  │  │ Fitness Layer │  │ Operator Layer │  │
│  │ ┌───────────┐ │  │ ┌───────────┐ │  │ ┌────────────┐ │  │
│  │ │RealGenome │ │  │ │Protocol   │ │  │ │Selection   │ │  │
│  │ │BinaryGen  │ │  │ │Weighted   │ │  │ │(4 types)   │ │  │
│  │ │TreeGenome │ │  │ │Constraints│ │  │ ├────────────┤ │  │
│  │ │(GP+ADF)   │ │  │ │(3 layers) │ │  │ │Crossover   │ │  │
│  │ └───────────┘ │  │ └───────────┘ │  │ │(4 types)   │ │  │
│  │ Genome        │  │               │  │ ├────────────┤ │  │
│  │ Protocol      │  │               │  │ │Mutation    │ │  │
│  └───────────────┘  └───────────────┘  │ │(4 types)   │ │  │
│         │                   │           │ └────────────┘ │  │
│         └───────────────────┼───────────┴────────────────┘  │
│                             │                                │
│  ┌──────────────────────────┴────────────────────────────┐  │
│  │                  Evolution Engine                      │  │
│  │ ┌────────────┐ ┌────────────┐ ┌────────────────────┐  │  │
│  │ │Population  │ │Main Loop   │ │Termination Criteria│  │  │
│  │ │(100 indiv) │ │select→x→mut│ │max_gen | thresh | │  │  │
│  │ │elite opt.  │ │→eval→replace│ │convergence (OR)   │  │  │
│  │ └────────────┘ └────────────┘ └────────────────────┘  │  │
│  │ ┌────────────┐ ┌────────────┐                          │  │
│  │ │Callbacks   │ │Statistics  │                          │  │
│  │ │on_gen/eval │ │best/mean/  │                          │  │
│  │ │on_terminat │ │std/diverse │                          │  │
│  │ └────────────┘ └────────────┘                          │  │
│  └───────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

---

## 2. Architecture Decision Records

### ADR-1: Genome Protocol 统一接口

**Context**: 三种编码（实数/二进制/树）需要统一操作接口。

**Decision**: `Genome` Protocol 定义 `crossover(other) -> tuple[Genome, Genome]`, `mutate(rate) -> Genome`, `clone() -> Genome`，内部按类型 dispatch。

**Rationale**: 算法层无需关心编码细节；新增编码类型只需实现 Protocol。

**Consequences**: crossover/mutate 内部需 isinstance 分发；Protocol 无法约束返回类型协变。

### ADR-2: 三层约束叠加

**Context**: 约束满足有多种策略，需灵活组合。

**Decision**: 边界裁剪（hard clip）→ 惩罚函数（fitness penalty）→ 修复算子（repair），顺序执行。

**Rationale**: 层层过滤，先简单后复杂；用户可按需启用任意层。

**Consequences**: 性能开销随层数增加；repair 可能引入偏差。

### ADR-3: 组合终止 OR 语义

**Context**: 用户可能希望"达到阈值或收敛就停"。

**Decision**: 三个条件（max_gen / fitness_threshold / convergence）以 OR 组合，任一满足即终止。

**Rationale**: 灵活性高；默认 max_gen 保底防止无限运行。

**Consequences**: 无法表达 AND 语义；需文档说明 OR 逻辑。

### ADR-4: numpy Generator + seed

**Context**: 进化算法需严格可复现。

**Decision**: 使用 `numpy.random.Generator` + 显式 seed，贯穿所有随机操作。

**Rationale**: Generator 是 numpy 推荐方式；seed 隔离不影响全局状态。

**Consequences**: 所有随机调用需传入 Generator 参数。

---

## 3. Data Model

```python
class Genome(Protocol):
    def crossover(self, other: Genome, rng: Generator) -> tuple[Genome, Genome]: ...
    def mutate(self, rate: float, rng: Generator) -> Genome: ...
    def clone(self) -> Genome: ...
    @property
    def fitness(self) -> float | None: ...
    @fitness.setter
    def fitness(self, value: float) -> None: ...

@dataclass
class Individual:
    id: UUID
    genome: Genome
    generation: int
    parents: list[UUID]
    fitness: float | None = None

class FitnessFunction(Protocol):
    def evaluate(self, population: list[Individual]) -> list[float]: ...
```

---

## 4. File Structure

```
agentforge/evoforge/         # submodule under agentforge
├── __init__.py
├── genomes/
│   ├── __init__.py
│   ├── protocol.py          # Genome Protocol
│   ├── real.py              # RealGenome (float vector)
│   ├── binary.py            # BinaryGenome (bitstring)
│   └── tree.py              # TreeGenome (GP + ADF)
├── fitness/
│   ├── __init__.py
│   ├── protocol.py          # FitnessFunction Protocol
│   ├── weighted.py          # WeightedMultiObjective
│   └── constraints.py       # BoundaryClip + Penalty + Repair
├── operators/
│   ├── __init__.py
│   ├── selection.py         # Roulette/Tournament/Elite/Rank
│   ├── crossover.py         # SinglePoint/MultiPoint/Uniform/SBX
│   └── mutation.py          # Gaussian/Uniform/BitFlip/Polynomial
├── engine/
│   ├── __init__.py
│   ├── population.py        # Population (default 100)
│   ├── evolution.py         # EvolutionEngine (main loop)
│   ├── termination.py       # Combined criteria (OR)
│   ├── convergence.py       # Stagnation + diversity detection
│   └── callbacks.py         # Callback hooks + Statistics
└── config.py                # Default configuration
```

---

## 5. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| TreeGenome GP 交叉产生非法树 | Medium | Medium | 深度限制 + 类型检查 |
| 收敛检测误判（早停） | Medium | High | 双重检测（stagnation + diversity OR） |
| 大种群 fitness evaluate 瓶颈 | Medium | Medium | 批量评估 + 可选并行 |
| numpy Generator 跨线程不安全 | Low | High | 每个 worker 独立 Generator (spawn) |

---

## 6. Testing Strategy

| Layer | Type | Key Scenarios |
|-------|------|---------------|
| Genomes | Unit | crossover output legality, mutate bounds, clone identity |
| Fitness | Unit | evaluate batch, weighted sum, constraint layers |
| Selection | Unit | probability distribution (chi-squared), elite preservation |
| Crossover | Unit | output within bounds, parents unchanged |
| Mutation | Unit | rate control, boundary compliance |
| Population | Unit | init, sort, stats, elite strategy |
| Engine | Integration | OneMax (binary), Sphere (real), Symbolic (tree) full run |
| Reproducibility | Integration | same seed → identical results |
| Convergence | Integration | stagnation detection triggers termination |
| **Coverage Target** | | **≥ 80%** |
