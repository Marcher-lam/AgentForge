# Change Proposal: Evolution & RL Training Dashboard

> Type: feature | Priority: P1 | Status: Confirmed
> Created: 2026-05-15 | Confirmed: 2026-05-15

---

## 1. Intent

实现进化引擎和 RL 训练的实时监控仪表板，可视化世代进度、适应度曲线、基因树和训练指标。

## 2. Scope

### In Scope
- **进化仪表板**：世代进度条、适应度曲线（best/mean/std）、世代树（节点颜色映射适应度，点击查看个体基因）、基因×个体热力图（种群多样性）
- **RL 训练监控**：全量指标（reward/loss/episode 长度/exploration rate/学习率/梯度范数）、多 run 叠加对比、超参数面板
- **仪表板布局**：Tab 切换（进化/RL 模式）+ 图表区域
- **图表交互**：悬停 tooltip、缩放、拖拽选区、数据导出
- **性能保护**：前端缓存 10k 数据点，超出 LTTB 降采样

### Out of Scope
- 对话 UI（Change-1）
- 通信监视（Change-2）
- 训练控制（暂停/恢复/停止）

## 3. Clarified Decisions

| # | 问题 | 决策 |
|---|------|------|
| 1 | 图表库 | **ECharts** |
| 2 | 基因树 | **ECharts tree 图表** |
| 3 | 数据源 | **WebSocket**（自定义数据流）+ TensorBoard REST API（可选） |
| 4 | 更新频率 | **可配置**（默认 1s） |
| 5 | 布局模式 | **Tab 切换**（进化/RL）+ 图表区 |
| 6 | 图表交互 | **丰富**：tooltip/缩放/拖拽选区/数据导出 |
| 7 | 基因树 | **世代树 + 适应度颜色映射 + 点击个体详情** |
| 8 | 热力图 | **基因维度 × 个体**，颜色映射基因值 |
| 9 | RL 指标 | **全量**：reward/loss/episode_len/exploration/lr/grad_norm |
| 10 | 多 run 对比 | **支持**，多条训练曲线叠加 |
| 11 | 数据点上限 | **10k + LTTB 降采样** |

## 4. Success Criteria

- [ ] 适应度曲线实时绘制（best/mean/std）
- [ ] 基因树正确渲染和交互（缩放/展开）
- [ ] RL reward/loss 曲线实时更新
- [ ] 数据流从后端到图表延迟 < 1s
- [ ] 更新频率可配置

## 5. Dependencies

- rlforge TensorBoardLogger 或 WebSocket 数据接口
- evoforge 回调数据接口
- Change-1 的 React + shadcn/ui 基础框架
