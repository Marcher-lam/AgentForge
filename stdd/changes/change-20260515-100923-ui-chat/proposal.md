# Change Proposal: Agent Chat UI

> Type: feature | Priority: P0 | Status: Confirmed
> Created: 2026-05-15 | Confirmed: 2026-05-15

---

## 1. Intent

实现 Agent 对话交互前端，包括消息面板、多 Agent 网格布局、1v1 和群组会话模式。

## 2. Scope

### In Scope
- **对话面板**：消息列表（区分用户/Agent）、输入框、发送按钮、Markdown + 代码高亮
- **多 Agent 网格视图**：自研自由拖拽布局（可重叠）、分屏、Agent 信息丰富卡片（头像+名称+状态+消息预览+操作）
- **1v1 会话**：用户 → 单个 Agent 私聊，独立消息流
- **群组会话**：广播（全部 Agent）+ 多播（指定 Agent 子集）

### Out of Scope
- Agent 间通信监视（Change-2）
- 进化/RL 训练可视化（Change-3）
- 用户认证和权限

## 3. Clarified Decisions

| # | 问题 | 决策 |
|---|------|------|
| 1 | 前端框架 | **React** |
| 2 | UI 组件库 | **shadcn/ui**（Tailwind CSS） |
| 3 | 实时通信 | **WebSocket 主 + SSE 降级** |
| 4 | 布局引擎 | **自研 CSS Grid + 拖拽** |
| 5 | 状态管理 | **Jotai**（原子化状态） |
| 6 | 消息渲染 | **Markdown + 代码高亮**（react-markdown + prism） |
| 7 | 构建工具 | **Vite** |
| 8 | 消息类型 | **多类型**：文本 + Markdown + 代码 + 图片 + 文件 + 系统消息 |
| 9 | 输入模式 | **类 ChatGPT**：Enter 发送，Shift+Enter 换行，自动扩展 |
| 10 | 历史加载 | **分页 + 虚拟滚动**（向上滚动加载更多） |
| 11 | 布局精度 | **自由拖拽**（可重叠，非网格约束） |
| 12 | Agent 卡片 | **信息丰富**：头像+名称+状态+消息预览+操作按钮 |
| 13 | 响应式 | **响应式**：桌面 3+列、平板 2 列、手机 1 列 |

## 4. Success Criteria

- [ ] 消息列表区分用户/Agent，Markdown 正确渲染
- [ ] 多 Agent 网格支持拖拽调整和分屏
- [ ] 1v1 会话独立消息流
- [ ] 群组广播消息所有成员可见
- [ ] WebSocket 实时通信延迟 < 200ms，SSE 降级自动切换
