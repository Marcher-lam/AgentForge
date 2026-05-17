# Technical Design: Frontend - Chat UI

> Change: change-20260515-100923-ui-chat | No upstream dependency

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                     Chat UI (React)                      │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ MessagePanel │  │  ChatInput   │  │  AgentGrid   │  │
│  │ ┌──────────┐ │  │ ┌──────────┐ │  │ ┌──────────┐ │  │
│  │ │VirtualScr│ │  │ │AutoGrow  │ │  │ │AgentCard │ │  │
│  │ │+Paginate │ │  │ │Enter/    │ │  │ │(drag+    │ │  │
│  │ └──────────┘ │  │ │Shift+Enter│ │  │ │overlap)  │ │  │
│  │ ┌──────────┐ │  │ └──────────┘ │  │ └──────────┘ │  │
│  │ │MultiType │ │  └──────────────┘  │ ┌──────────┐ │  │
│  │ │Renderer  │ │                    │ │Responsive│ │  │
│  │ │(md/code/ │ │                    │ │(3/2/1col)│ │  │
│  │ │img/file) │ │                    │ └──────────┘ │  │
│  │ └──────────┘ │                    └──────────────┘  │
│  └──────────────┘                                       │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ SessionMgr   │  │  Jotai Atoms │  │  WS/SSE      │  │
│  │ (1v1/Group)  │  │  (state)     │  │  Connection  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Architecture Decision Records

### ADR-1: Jotai 原子化状态管理

**Context**: 多组件共享会话/消息/Agent 状态。

**Decision**: Jotai (atomic state)，每个状态域独立 atom（messagesAtom, sessionsAtom, agentsAtom）。

**Rationale**: 细粒度更新，未变更的组件不重渲染；API 简洁（无 reducer boilerplate）。

**Consequences**: atom 间依赖需手动管理（derived atoms）；调试不如 Redux DevTools 直观。

### ADR-2: 自研自由拖拽布局（非 react-grid-layout）

**Context**: Agent 卡片需支持自由定位、可重叠。

**Decision**: 基于 CSS `transform: translate()` + Framer Motion `drag` 实现自由拖拽，非网格约束。

**Rationale**: react-grid-layout 强制网格对齐，不支持重叠；自研仅需 ~100 行。

**Consequences**: 需自行处理 z-index 管理、碰撞检测（可选）。

### ADR-3: WebSocket 主 + SSE 降级

**Context**: 实时消息推送需要可靠连接。

**Decision**: 优先 WebSocket，连接失败时自动降级 SSE。

**Rationale**: WebSocket 双向通信支持发送+接收；SSE 为单向但兼容性好（HTTP/1.1）。

**Consequences**: SSE 模式下发送消息仍需 HTTP POST；需维护两套连接逻辑。

### ADR-4: 虚拟滚动 + 向上分页

**Context**: 消息可能上万条，全量渲染卡顿。

**Decision**: `@tanstack/react-virtual` 虚拟滚动，向上滚动触发分页加载。

**Rationale**: 仅渲染可见区域 DOM；向上加载保持滚动位置不跳动。

**Consequences**: 快速滚动时可能闪白；需预渲染 buffer 区域。

---

## 3. Data Model

```typescript
// Jotai Atoms
export const sessionsAtom = atom<SessionResponse[]>([]);
export const activeSessionAtom = atom<string | null>(null);
export const messagesAtom = atom<Map<string, FrontendMessage[]>>(new Map());
export const agentsAtom = atom<AgentSummary[]>([]);
export const connectionStatusAtom = atom<"connected" | "disconnected" | "reconnecting">("disconnected");

// Component State
interface ChatInputState {
  content: string;
  contentType: FrontendMessageType;
  isSending: boolean;
}

interface GridState {
  cards: Map<string, { x: number; y: number; z: number }>;
}
```

---

## 4. File Structure

```
src/
├── App.tsx
├── main.tsx
├── atoms/
│   ├── sessions.ts          # Session atoms
│   ├── messages.ts          # Message atoms
│   ├── agents.ts            # Agent atoms
│   └── connection.ts        # WS/SSE status atom
├── components/
│   ├── chat/
│   │   ├── MessagePanel.tsx  # Virtual scroll message list
│   │   ├── MessageItem.tsx   # Multi-type renderer
│   │   ├── ChatInput.tsx     # Auto-grow input box
│   │   └── SessionList.tsx   # Session sidebar
│   ├── grid/
│   │   ├── AgentGrid.tsx     # Free drag layout container
│   │   ├── AgentCard.tsx     # Agent info card
│   │   └── GridControls.tsx  # Layout controls
│   └── session/
│       ├── SessionManager.tsx # 1v1/Group switch
│       ├── GroupSend.tsx      # Broadcast/multicast controls
│       └── UnreadBadge.tsx    # Unread count
├── hooks/
│   ├── useWebSocket.ts       # WS connection + auto-reconnect
│   ├── useSSE.ts             # SSE fallback
│   ├── useMessages.ts        # Message CRUD
│   └── useDrag.ts            # Free drag hook
├── services/
│   ├── api.ts                # REST API client
│   └── ws.ts                 # WebSocket client
└── types/
    └── api.ts                # Generated types (already exists)
```

---

## 5. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Framer Motion 拖拽与虚拟滚动冲突 | Medium | Medium | 事件冒泡控制 + pointer-events 管理 |
| WebSocket 断连丢失消息 | Medium | High | 重连时请求 missed messages API |
| Markdown XSS 注入 | Low | High | DOMPurify sanitize + react-markdown 安全配置 |
| 大量 Agent 卡片渲染卡顿 | Low | Medium | React.memo + 虚拟化 AgentGrid |

---

## 6. Testing Strategy

| Layer | Type | Key Scenarios |
|-------|------|---------------|
| Components | Vitest + RTL | MessageItem 渲染各类型, ChatInput Enter/Shift+Enter |
| Hooks | Vitest | useWebSocket connect/reconnect, useMessages CRUD |
| Integration | RTL | 完整聊天流程 (发送→接收→渲染) |
| Visual | Playwright (optional) | 拖拽布局, 响应式断点 |
| **Coverage Target** | | **≥ 80%** |
