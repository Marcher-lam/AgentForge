# Task Breakdown: Frontend - Evolution & RL Dashboard

> Change: change-20260515-100923-ui-dashboard | Priority: P1 | Depends on: change-20260515-100923-ui-chat

---

## Task 1: Dashboard 骨架 + Tab 切换
- [x] 实现 Tab 布局（Evolution / RL Training 两个标签页）
- [x] 实现 Dashboard 路由 + 响应式容器
- [x] 实现 Jotai dashboard state atoms
- [x] 实现 LTTB 降采样工具函数（10k 数据点上限）
- [x] 组件测试：Tab 切换 + 路由
- **预估**: 25min | **依赖**: change-20260515-100923-ui-chat Task 1

## Task 2: Evolution 仪表板
- [x] 实现 fitness 曲线图（ECharts：best/mean/std 三线）
- [x] 实现基因树可视化（React Flow + 适应度颜色映射 + 点击详情）
- [x] 实现 gene × individual 热力图（ECharts heatmap）
- [x] 实现图表交互（tooltip/zoom/drag-select/export）
- [x] 组件测试：图表渲染 + 交互
- **预估**: 45min | **依赖**: Task 1

## Task 3: RL 训练监控面板
- [x] 实现 reward 曲线（episode reward + moving average）
- [x] 实现 loss 曲线（policy_loss + value_loss）
- [x] 实现 episode 长度 + 探索率曲线
- [x] 实现 learning rate + gradient norm 曲线
- [x] 实现 multi-run 对比视图（同图多线）
- [x] 组件测试：图表渲染 + 多曲线
- **预估**: 40min | **依赖**: Task 1

## Task 4: 数据适配层 + 实时更新
- [x] 实现 WS 数据订阅（训练指标实时推送）
- [x] 实现数据缓冲 + LTTB 降采样（≤10k 点）
- [x] 实现图表增量更新（避免全量重绘）
- [x] 实现 multi-run 数据管理（run_id 分组）
- [x] 组件测试：数据流 + 降采样
- **预估**: 35min | **依赖**: Task 2, Task 3

## Task 5: 集成测试 + 构建验证
- [x] Evolution Dashboard 完整渲染集成测试
- [x] RL Dashboard 完整渲染集成测试
- [x] 实时数据更新 + 图表联动测试
- [x] LTTB 降采样正确性测试
- [x] Vite build 无错误 + 无 console warning
- **预估**: 30min | **依赖**: Task 4
