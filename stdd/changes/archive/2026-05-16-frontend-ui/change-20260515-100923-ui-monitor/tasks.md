# Task Breakdown: Frontend - Agent Communication Monitor

> Change: change-20260515-100923-ui-monitor | Priority: P1 | Depends on: change-20260515-100923-ui-chat

---

## Task 1: 拓扑图可视化引擎
- [x] 实现 React Flow 节点图（Agent 节点 + 连接边）
- [x] 实现有向箭头 + 动画粒子流（消息流向可视化）
- [x] 实现自动布局 + 手动拖拽节点
- [x] 实现节点状态着色（RUNNING/STOPPED/ERROR）
- [x] 组件测试：节点渲染 + 拖拽
- **预估**: 40min | **依赖**: change-20260515-100923-ui-chat Task 1

## Task 2: 时间轴 + 消息详情面板
- [x] 实现时间轴组件（消息事件流，可缩放）
- [x] 实现时间轴-拓扑图联动（点击时间轴 → 高亮对应边）
- [x] 实现消息详情面板（header/body/payload/timestamp）
- [x] 实现点击节点/边 → 展示该连接消息列表
- [x] 组件测试：时间轴交互 + 联动
- **预估**: 40min | **依赖**: Task 1

## Task 3: 多维度过滤器
- [x] 实现 Agent 过滤（选择特定 Agent）
- [x] 实现 topic 过滤（消息主题筛选）
- [x] 实现类型过滤（text/tool_call/system 等）
- [x] 实现时间范围过滤（起始/结束时间）
- [x] 实现 payload 关键字搜索
- [x] 组件测试：各过滤维度组合
- **预估**: 35min | **依赖**: Task 2

## Task 4: 统计面板 + 暂停/恢复
- [x] 实现消息统计面板（消息量/延迟/吞吐量）
- [x] 实现暂停/恢复按钮（暂停时缓冲消息，恢复时批量回放）
- [x] 实现缓冲区大小指示器
- [x] 组件测试：暂停恢复 + 统计更新
- **预估**: 25min | **依赖**: Task 2

## Task 5: 实时数据集成 + 构建验证
- [x] 接入 WebSocket 实时消息流
- [x] 实现消息 → 粒子动画映射
- [x] 集成测试：实时流 + 过滤 + 暂停恢复
- [x] Vite build 无错误
- **预估**: 30min | **依赖**: Task 3, Task 4
