# Technical Design: Frontend - Evolution & RL Dashboard

> Change: change-20260515-100923-ui-dashboard | Depends on: change-20260515-100923-ui-chat

---

## 1. Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                    Dashboard (Tab Layout)                     │
│                                                               │
│  [Evolution Tab]  [RL Training Tab]                           │
│                                                               │
│  ┌──────────────────── Evolution ─────────────────────────┐  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │  │
│  │  │ Fitness      │  │ Gene Tree    │  │ Heatmap      │ │  │
│  │  │ Curves       │  │ (ECharts     │  │ (gene×indiv) │ │  │
│  │  │ (ECharts     │  │  tree chart) │  │              │ │  │
│  │  │  3 lines)    │  │              │  │              │ │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘ │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌──────────────────── RL Training ───────────────────────┐  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │  │
│  │  │ Reward/Loss  │  │ Exploration/ │  │ Multi-Run    │ │  │
│  │  │ Curves       │  │ LR/GradNorm  │  │ Comparison   │ │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘ │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌──────────────── Shared Services ───────────────────────┐  │
│  │ LTTB Downsample | Chart Interactions | Data Adapter     │  │
│  └───────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

---

## 2. Architecture Decision Records

### ADR-1: ECharts 替代 D3/Recharts

**Context**: 需要丰富图表类型（线图、热力图、树图）+ 高性能大数据量。

**Decision**: Apache ECharts (echarts-for-react 封装)。

**Rationale**: 内置 LTTB 降采样、热力图、树图；10k+ 数据点流畅；丰富交互（tooltip/zoom/dataZoom/export）。

**Consequences**: ECharts bundle ~800KB（tree-shakeable）；自定义主题需额外配置。

### ADR-2: LTTB 降采样算法

**Context**: 前端缓存 10k 数据点上限，超出需降采样。

**Decision**: Largest-Triangle-Three-Buckets (LTTB) 算法。

**Rationale**: 保持视觉特征（峰值、趋势）的同时减少数据量；O(n) 复杂度。

**Consequences**: 降采样后精确 tooltip 值丢失；需标注"已降采样"提示。

### ADR-3: Tab 切换保持状态

**Context**: 切换 Evolution/RL Tab 时不应丢失图表状态。

**Decision**: 使用 CSS `display: none` 隐藏非活动 Tab，而非条件渲染（unmount）。

**Rationale**: ECharts 实例保持不变，无需重新初始化和数据加载。

**Consequences**: 两个 Tab 同时占用 DOM 和内存。

---

## 3. Data Model

```typescript
interface DashboardState {
  activeTab: "evolution" | "rl";
  evolution: {
    evolutionId: string | null;
    fitnessCurves: FitnessCurves | null;
    geneTree: GeneTreeNode | null;
    heatmap: number[][] | null;
    currentGeneration: number;
  };
  rl: {
    taskId: string | null;
    metrics: Record<string, DataPoint[]>;
    algorithm: AlgorithmType | null;
    compareRuns: TrainingRunComparison[];
  };
  downsampleThreshold: number;  // default 10000
  updateIntervalMs: number;     // default 1000
}
```

---

## 4. File Structure

```
src/
├── components/
│   ├── dashboard/
│   │   ├── DashboardPage.tsx       # Tab layout + routing
│   │   ├── EvolutionTab.tsx        # Evolution dashboard
│   │   ├── RLTab.tsx               # RL training dashboard
│   │   ├── charts/
│   │   │   ├── FitnessCurves.tsx   # ECharts 3-line chart
│   │   │   ├── GeneTree.tsx        # ECharts tree chart
│   │   │   ├── Heatmap.tsx         # ECharts heatmap
│   │   │   ├── TrainingCurve.tsx   # ECharts reward/loss
│   │   │   ├── MultiRunCompare.tsx # ECharts multi-line
│   │   │   └── ChartWrapper.tsx    # Shared ECharts config
│   │   └── controls/
│   │       ├── MetricSelector.tsx  # Metric dropdown
│   │       ├── RunSelector.tsx     # Multi-run checkbox
│   │       └── ExportButton.tsx    # CSV/PNG export
├── hooks/
│   ├── useEvolutionData.ts        # Evolution data fetch + WS
│   ├── useTrainingData.ts         # RL data fetch + WS
│   └── useDownsample.ts           # LTTB downsample hook
├── utils/
│   ├── lttb.ts                    # LTTB algorithm
│   └── chart-config.ts            # Shared ECharts options
├── atoms/
│   └── dashboard.ts               # Dashboard state atoms
```

---

## 5. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| ECharts 首次加载慢 | High | Low | 按需引入 chart 类型 + lazy load tab |
| LTTB 降采样丢失关键峰值 | Low | Medium | 增加采样点数 + 可配置阈值 |
| 基因树过大渲染卡顿 | Medium | Medium | 限制展示深度 + 虚拟滚动 |
| WS 推送频率过高 | Medium | Medium | 可配置更新频率 + 前端节流 |

---

## 6. Testing Strategy

| Layer | Type | Key Scenarios |
|-------|------|---------------|
| FitnessCurves | Vitest | 3-line render, real-time update |
| GeneTree | Vitest | tree render, node click, color mapping |
| Heatmap | Vitest | matrix render, color range |
| TrainingCurve | Vitest | multi-metric render, zoom |
| MultiRunCompare | Vitest | multi-line render, legend |
| LTTB | Unit | 降采样精度, 10k threshold |
| ChartWrapper | Unit | tooltip/zoom/export config |
| Integration | RTL | Tab switch state preserve, data→chart flow |
| **Coverage Target** | | **≥ 80%** |
