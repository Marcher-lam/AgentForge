# Technical Design: Frontend - Agent Communication Monitor

> Change: change-20260515-100923-ui-monitor | Depends on: change-20260515-100923-ui-chat

---

## 1. Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                  Communication Monitor                        │
│                                                               │
│  ┌──────────────────────┐  ┌──────────────────────────────┐  │
│  │   Topology Graph     │  │   Timeline Panel (right)     │  │
│  │   ┌──────────────┐   │  │   ┌────────────────────────┐ │  │
│  │   │ React Flow   │   │  │   │ Message timeline list   │ │  │
│  │   │ Nodes+Edges  │   │  │   │ (scrollable, zoomable)  │ │  │
│  │   │ + Particle   │   │  │   └────────────────────────┘ │  │
│  │   │ Animation    │   │  └──────────────────────────────┘  │
│  │   └──────────────┘   │                                     │
│  └──────────────────────┘                                     │
│                                                               │
│  ┌──────────────────────┐  ┌──────────────────────────────┐  │
│  │   Filter Panel       │  │   Statistics + Controls       │  │
│  │   Agent/Topic/Type/  │  │   Total/TPS/Latency/          │  │
│  │   Time/Keyword       │  │   Per-Agent/Topic dist        │  │
│  │                      │  │   [Pause] [Resume]            │  │
│  └──────────────────────┘  └──────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

---

## 2. Architecture Decision Records

### ADR-1: React Flow 拓扑图

**Context**: 需要可视化 Agent 间通信拓扑。

**Decision**: 使用 React Flow 库渲染节点图。

**Rationale**: 内置拖拽、缩放、自定义节点；活跃社区；TypeScript 支持。

**Consequences**: 需自定义边渲染（粒子动画）；大量节点（>100）需虚拟化。

### ADR-2: Framer Motion 粒子动画

**Context**: 消息流动需要动画效果。

**Decision**: Framer Motion `animate` 沿 SVG path 做粒子运动。

**Rationale**: 声明式动画 API；自动批处理动画帧。

**Consequences**: 高频消息时粒子过多需限制并发数。

### ADR-3: 暂停时缓冲消息

**Context**: 用户暂停监视后，恢复时需回放积累的消息。

**Decision**: 暂停时消息入队（bounded buffer, max 1000），恢复时批量推送。

**Rationale**: 不丢失暂停期间数据；bounded 防止内存溢出。

**Consequences**: 长时间暂停后恢复可能短暂卡顿。

---

## 3. Data Model

```typescript
interface MonitorState {
  nodes: TopologyNode[];
  edges: TopologyEdge[];
  messages: MonitorMessage[];
  filters: MonitorFilters;
  stats: MonitorStatistics | null;
  isPaused: boolean;
  pausedBuffer: MonitorMessage[];
}

interface MonitorFilters {
  agentId: string | null;
  topic: string | null;
  type: string | null;
  timeRange: { start: Date; end: Date } | null;
  keyword: string | null;
}
```

---

## 4. File Structure

```
src/
├── components/
│   ├── monitor/
│   │   ├── MonitorPage.tsx      # Page layout
│   │   ├── TopologyGraph.tsx    # React Flow container
│   │   ├── AgentNode.tsx        # Custom React Flow node
│   │   ├── MessageEdge.tsx      # Custom edge + particle animation
│   │   ├── Timeline.tsx         # Message timeline
│   │   ├── MessageDetail.tsx    # Message detail panel
│   │   ├── FilterPanel.tsx      # Multi-dimension filters
│   │   ├── StatsPanel.tsx       # Statistics dashboard
│   │   └── PauseControl.tsx     # Pause/Resume button
├── hooks/
│   ├── useMonitorMessages.ts    # Message stream + buffer
│   ├── useTopology.ts           # Node/edge data management
│   └── useFilters.ts            # Filter state + apply
├── atoms/
│   └── monitor.ts               # Monitor state atoms
```

---

## 5. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| React Flow 大量节点卡顿 | Medium | Medium | 节点虚拟化 + 聚合显示 |
| 粒子动画内存泄漏 | Medium | High | 动画完成后 cleanup + React.memo |
| 暂停 buffer 溢出 | Low | Medium | Bounded buffer (1000) + 溢出丢弃最旧 |
| 过滤维度组合性能 | Low | Low | debounce filter input + useMemo |

---

## 6. Testing Strategy

| Layer | Type | Key Scenarios |
|-------|------|---------------|
| TopologyGraph | Vitest | 节点渲染, 边渲染, 拖拽 |
| Timeline | Vitest | 消息列表, 点击联动 |
| FilterPanel | Vitest | 各维度过滤组合 |
| StatsPanel | Vitest | 统计数据更新 |
| PauseControl | Vitest | 暂停/恢复 + buffer 管理 |
| Integration | RTL | 实时消息流 → 图更新 → 过滤 → 统计 |
| **Coverage Target** | | **≥ 80%** |
