# Task Breakdown: Frontend - Chat UI

> Change: change-20260515-100923-ui-chat | Priority: P0 | Depends on: none

---

## Task 1: 项目骨架 + 路由 + 状态管理
- [x] 初始化 Vite + React + TypeScript 项目
- [x] 配置 Tailwind CSS + shadcn/ui
- [x] 实现 Jotai atom 定义（消息/会话/Agent 状态）
- [x] 实现路由结构（ChatPanel / Grid / Monitor / Dashboard）
- [x] 配置 WebSocket + SSE 连接层
- **预估**: 30min | **依赖**: 无

## Task 2: 消息面板 + 输入框
- [x] 实现 MessageList（虚拟滚动 + 分页加载）
- [x] 实现多类型消息渲染（text/markdown/code/image/file/system）
- [x] 实现代码高亮（Prism/highlight.js）
- [x] 实现 ChatInput（Enter 发送 / Shift+Enter 换行 / 自动扩高）
- [x] 单元/组件测试：消息渲染 + 输入交互
- **预估**: 40min | **依赖**: Task 1

## Task 3: 多 Agent 网格视图
- [x] 实现 AgentCard 组件（状态指示 + 摘要）
- [x] 实现自由拖拽布局（非网格约束，支持重叠）
- [x] 实现 Framer Motion 拖拽动画
- [x] 实现响应式断点（桌面 3+ 列 / 平板 2 列 / 手机 1 列）
- [x] 组件测试：拖拽 + 响应式布局
- **预估**: 40min | **依赖**: Task 1

## Task 4: 一对一 + 群组会话模式
- [x] 实现 1v1 会话（用户 → Agent 私聊，独立消息流）
- [x] 实现群组会话（一对多广播/多播）
- [x] 实现会话切换（侧边栏列表 + Jotai 状态切换）
- [x] 实现消息来源标识（Agent 头像 + 名称着色）
- [x] 组件测试：会话切换 + 消息路由
- **预估**: 35min | **依赖**: Task 2

## Task 5: WebSocket 实时通信集成
- [x] 实现 WS 连接管理（connect/reconnect/heartbeat）
- [x] 实现 SSE fallback 连接
- [x] 实现消息收发与 Jotai state 同步
- [x] 实现断线提示 + 重连状态 UI
- [x] 集成测试：消息收发 + 重连恢复
- **预估**: 35min | **依赖**: Task 4

## Task 6: 集成测试 + 构建验证
- [x] ChatPanel 完整交互集成测试
- [x] 多会话并行消息收发测试
- [x] 响应式布局跨分辨率测试
- [x] Vite build 无错误 + 无 console error
- **预估**: 25min | **依赖**: Task 5
