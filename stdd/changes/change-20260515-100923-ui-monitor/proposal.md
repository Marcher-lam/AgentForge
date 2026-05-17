# Change Proposal: Agent Communication Monitor

> Type: feature | Priority: P1 | Status: Confirmed
> Created: 2026-05-15 | Confirmed: 2026-05-15

---

## 1. Intent

实现 Agent 间通信的可视化监视器，实时展示 Agent 之间的消息流转。

## 2. Scope

### In Scope
- **消息流可视化**：Agent 节点图（自动布局+手动调整）+ 有向箭头动画粒子流动 + 时间轴联动
- **消息详情面板**：点击消息查看 payload、timestamp、topic
- **过滤/搜索**：按 Agent、topic、type、时间范围、payload 关键字多维度过滤
- **统计面板**：总消息量、每秒消息数、平均延迟、per-Agent 发送/接收量、topic 分布
- **暂停/恢复**：支持暂停监视冻结画面，恢复后继续

### Out of Scope
- 用户对话 UI（Change-1）
- 训练/进化可视化（Change-3）
- 消息修改/重放

## 3. Clarified Decisions

| # | 问题 | 决策 |
|---|------|------|
| 1 | 图可视化 | **React Flow** |
| 2 | 动画 | **Framer Motion**（消息流动画） |
| 3 | 数据源 | **WebSocket 订阅**（主）+ SSE（降级） |
| 4 | 消息存储 | **前端内存**（默认 1000 条，可配置）+ 可选 IndexedDB |
| 5 | 节点布局 | **自动布局 + 手动拖拽调整** |
| 6 | 消息流动画 | **有向箭头 + 动画粒子**流动 |
| 7 | 时间轴 | **节点图 + 时间轴联动**，点击跳转 |
| 8 | 统计粒度 | **多维度**：总量/TPS/延迟/per-Agent/topic 分布 |
| 9 | 过滤维度 | **多维度**：Agent/topic/type/时间/payload 关键字 |
| 10 | 暂停/恢复 | **支持**暂停冻结画面 |

## 4. Success Criteria

- [ ] Agent 节点图实时更新，消息流动画可见
- [ ] 消息详情可点击查看完整 payload
- [ ] 过滤和搜索正常工作
- [ ] 统计面板实时刷新

## 5. Dependencies

- 后端消息总线 WebSocket 接口
- Change-1 的 React + shadcn/ui 基础框架
