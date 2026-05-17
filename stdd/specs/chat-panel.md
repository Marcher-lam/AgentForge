# Delta Spec: Agent Chat UI

> Change: change-20260515-100923-ui-chat | Domain: chat | Type: ADDED
> Status: Updated to reflect actual implementation

---

## Feature: MessagePanel

```gherkin
Feature: 消息列表展示
  用户在 MessagePanel 组件中看到区分用户和 Agent 的消息，支持多类型内容渲染。

  Scenario: 区分用户和 Agent 消息
    Given 用户发送 "你好" 和 Agent 回复 "我是 Agent"
    When 消息列表渲染
    Then 用户消息 SHALL 使用 `justify-end` 显示在右侧，蓝色背景 (bg-blue-600)
    And Agent 消息 SHALL 使用 `justify-start` 显示在左侧，灰色背景 (bg-gray-100)
    And Agent 消息 SHALL 显示 sender_name 标签（蓝色加粗小字）

  Scenario: 多类型内容渲染
    Given 消息的 content_type 字段
    When content_type 为 "CODE"
    Then SHALL 渲染为 <pre> 代码块（深色背景 bg-gray-900，绿色文字 text-green-400）
    When content_type 为 "MARKDOWN"
    Then SHALL 渲染为 prose 样式的 div
    When content_type 为 "IMAGE"
    Then SHALL 渲染为 <img> 标签（max-w-xs 圆角）
    When content_type 为 "SYSTEM"
    Then SHALL 渲染为居中灰色斜体文本
    When content_type 为其他（如 "TEXT"）
    Then SHALL 渲染为 whitespace-pre-wrap 段落

  Scenario: 向上滚动加载更多
    Given hasMore=true 且 onLoadMore 回调已传入
    When 消息列表渲染
    Then 顶部 SHALL 显示 "加载更多..." 占位 div
    And SHALL 使用 IntersectionObserver（threshold=0.1）监测顶部元素
    When 顶部元素进入视口
    Then SHALL 调用 onLoadMore 回调

  Scenario: 消息唯一标识
    Given 消息列表中的消息
    Then 每条消息 SHALL 使用 message_id 作为 React key
```

## Feature: ChatInput

```gherkin
Feature: 类 ChatGPT 输入框
  用户使用 ChatInput 组件发送消息。

  Scenario: Enter 发送消息
    Given 输入框有文本 "测试消息"
    When 用户按 Enter 键（无 Shift）
    Then SHALL 调用 onSend(content.trim())
    And 输入框内容 SHALL 清空
    And textarea 高度 SHALL 重置为 auto

  Scenario: Shift+Enter 换行
    Given 输入框有文本
    When 用户按 Shift+Enter
    Then SHALL 插入换行符（浏览器默认行为）
    And SHALL NOT 发送消息

  Scenario: 自动扩展高度
    Given 输入框为单行高度（rows=1）
    When 用户输入多行文本
    Then 输入框高度 SHALL 自动扩展至 scrollHeight
    And 最大高度 SHALL 为 160px（max-h-40 CSS 类）

  Scenario: 禁用状态
    Given disabled=true
    Then textarea SHALL 禁用
    And Send 按钮 SHALL 禁用（opacity-50）
    And 空内容时 Send 按钮 SHALL 也禁用

  Scenario: 空内容不发送
    Given 输入框只有空白字符
    When 用户按 Enter 或点击 Send
    Then SHALL NOT 调用 onSend
```

## Feature: Session Management (App-level)

```gherkin
Feature: 会话列表管理
  用户在左侧边栏管理会话列表，支持单聊、群聊创建、删除和导出。

  Scenario: 创建新会话（单聊/群聊切换）
    Given 用户点击 "+ 新建" 按钮
    When 创建面板显示 "单聊" 和 "群聊" 两个切换按钮
    Then 默认选中 "单聊" 模式
    When 用户选择 "群聊" 模式
    Then 可选择多个智能体
    And 提示 "群聊模式：N 个智能体将多轮讨论"
    When 用户选择 "单聊" 模式并选择多个
    Then 提示 "单聊模式只取第一个智能体"
    When 点击 "创建会话"/"创建群聊"
    Then SHALL POST /api/sessions（群聊 type=GROUP_BROADCAST）
    And 新会话 SHALL 添加到 sessionsAtom
    And activeSessionAtom SHALL 切换到新会话

  Scenario: 删除会话
    Given 会话列表中有会话
    When 鼠标悬停在会话项上
    Then 删除按钮 SHALL 显示（opacity-0 → group-hover:opacity-100）
    When 点击删除按钮
    Then SHALL 显示 "确认" 和 "取消" 两个按钮
    When 点击 "确认"
    Then SHALL DELETE /api/sessions/{id}
    And 会话 SHALL 从 sessionsAtom 移除
    And 对应消息 SHALL 从 messagesAtom 移除
    And 若删除的是当前活跃会话，activeSessionAtom SHALL 设为 null

  Scenario: 删除单条消息
    Given 会话中有消息
    When DELETE /api/sessions/{id}/messages/{mid}
    Then 对应消息 SHALL 从消息列表中移除

  Scenario: 导出聊天记录
    Given 有活跃会话
    When 用户点击导出按钮（侧边栏 hover 或聊天顶部工具栏）
    Then SHALL GET /api/sessions/{id}/export
    And SHALL 下载 JSON 文件（文件名格式：chat-{会话名}-{日期}.json）
    And JSON SHALL 包含 session、agents、messages、exported_at、total_messages

  Scenario: 群聊模式提示
    Given 用户选择了 2 个或更多智能体
    When 创建会话面板显示
    Then SHALL 显示 "群聊模式：N 个智能体将同时回复" 提示
    And 会话列表中群聊会话 SHALL 显示紫色 "群聊" 标签

  Scenario: 聊天顶部工具栏
    Given 有活跃会话
    When 聊天区域渲染
    Then 顶部 SHALL 显示会话名称和群聊标签（如果是群聊）
    And 顶部 SHALL 显示 "导出记录" 按钮

  Scenario: 点击 Agent 卡片跳转聊天
    Given AgentGrid 中用户点击某 Agent 卡片
    When 存在该 Agent 的已有会话
    Then SHALL 切换到该会话并跳转到 Chat 标签页

  Scenario: 消息轮询
    Given 有活跃会话 activeSession
    Then SHALL 每 2 秒 GET /api/sessions/{id}/messages 轮询消息
    And 消息 SHALL 存入 messagesAtom Map
```

## Feature: Agent Grid View

```gherkin
Feature: 智能体卡片网格布局
  用户在 AgentGrid 组件中查看和管理所有智能体。

  Scenario: 卡片网格展示
    Given 有 N 个智能体
    When AgentGrid 渲染
    Then SHALL 使用响应式网格布局
    And 小屏 SHALL 1 列 (grid-cols-1)
    And 中屏 SHALL 2 列 (sm:grid-cols-2)
    And 大屏 SHALL 3 列 (lg:grid-cols-3)
    And 超大屏 SHALL 4 列 (xl:grid-cols-4)

  Scenario: 智能体信息卡片
    Given Agent 卡片展示
    Then SHALL 包含：渐变头像（from-blue-400 to-purple-500，显示名称首字母大写）
    And 名称（加粗）
    And 系统提示词预览（前 40 字符截断）
    And 状态指示灯（绿色圆点 + "在线" / 灰色 + "离线"）
    And 最近消息预览（如有）

  Scenario: 创建智能体
    Given 用户点击 "+ 创建智能体" 按钮
    When 创建面板展开
    Then SHALL 显示以下配置区域：
      | 区域 | 控件 |
      | 名称 + 提示词 | 文本输入 + 多行文本框 |
      | LLM 配置 | Provider 下拉 + 模型选择 |
      | 技能 | 复选框列表（从全局技能池加载） |
      | MCP 服务器 | 复选框列表（从全局 MCP 池加载） |
      | 进化引擎 | 开关 + 模式/种群/代数参数 |
      | RL 训练 | 开关 + 算法/步数/学习率参数 |
    When 填写名称并配置各项
    And 点击 "创建智能体"
    Then SHALL POST /api/agents { name, system_prompt, config: { skill_ids, mcp_server_ids, tool_ids, evolution?, rl?, llm? } }
    And 创建后 SHALL 调用 onAgentsChanged 刷新列表

  Scenario: 悬停删除确认
    Given Agent 卡片
    When 鼠标悬停在卡片上
    Then 删除按钮 SHALL 显示（opacity-0 → group-hover:opacity-100）
    When 点击 "删除"
    Then SHALL 显示 "确认删除" 和 "取消" 两个按钮
    When 点击 "确认删除"
    Then SHALL DELETE /api/agents/{id} 删除智能体
```

## Feature: WebSocket Real-time Messaging

```gherkin
Feature: WebSocket 实时通信
  前端通过 WebSocket 接收实时消息。

  Scenario: WebSocket 连接
    Given App 加载
    When 前端建立 ws://localhost:8000/ws 连接
    Then 连接成功后 SHALL 显示绿色圆点 + "已连接"

  Scenario: 接收实时消息
    Given WebSocket 连接正常
    When 收到 type="message" 的消息
    Then 消息 SHALL 添加到 messagesAtom 对应 session_id 的列表
    And 会话列表 SHALL 更新 last_message 和 updated_at

  Scenario: 连接断开自动重连
    Given WebSocket 连接意外断开
    When ws.onclose 触发
    Then SHALL 3 秒后自动重连（setTimeout(connect, 3000)）
    And 状态 SHALL 显示红色圆点 + "离线"

  Scenario: 消息去重
    Given WebSocket 推送一条消息
    When 该消息的 message_id 已存在于当前会话
    Then SHALL NOT 重复添加（通过 message_id 查重）

  Scenario: 发送消息
    Given 有活跃会话且 WebSocket 已连接
    When 用户在 ChatInput 输入并发送
    Then SHALL 通过 WebSocket 发送 JSON {type:"chat", session_id, content}
```

## Feature: Settings Page

```gherkin
Feature: 设置页面三标签布局
  SettingsPage 组件提供 LLM 配置、进化引擎、强化学习三个标签。

  Scenario: 三个子标签
    Given 设置页面加载
    Then SHALL 显示三个标签："模型配置"、"进化引擎"、"强化学习"
    And Agent 管理 SHALL NOT 在设置页面中（已移至 AgentGrid 组件）

  Scenario: 模型配置标签
    Given 用户在 "模型配置" 标签
    Then SHALL 显示 LLM 参数表单（provider, model, base_url, api_key, temperature, max_tokens）
    And provider SHALL 支持选择 openai/anthropic/ollama
    And api_key 输入框 SHALL 为 password 类型
    And 保存后 SHALL PUT /api/settings

  Scenario: 进化引擎标签
    Given 用户在 "进化引擎" 标签
    Then SHALL 显示进化配置表单
    And 优化模式 SHALL 支持 "智能体人格优化" (agent) 和 "经典基准（球面函数）" (sphere)

  Scenario: 强化学习标签
    Given 用户在 "强化学习" 标签
    Then SHALL 显示 RL 训练配置表单
    And 算法 SHALL 支持 PPO / DQN / A2C
```

## Feature: Connection Resilience (useWebSocket hook)

```gherkin
Feature: 连接断线处理
  useWebSocket hook 提供基础断线重连。

  Scenario: 自动重连
    Given WebSocket 连接断开
    When ws.onclose 触发
    Then SHALL 最多重试 3 次，间隔 2 秒
    And 重连期间 connectionStatusAtom SHALL 为 "reconnecting"

  Scenario: 重连成功
    Given 重连尝试中
    When ws.onopen 触发
    Then connectionStatusAtom SHALL 设为 "connected"
    And reconnectRef SHALL 重置为 0

  Scenario: 重连全部失败
    Given 连续 3 次重连均失败
    Then connectionStatusAtom SHALL 为 "disconnected"
    And connected 状态 SHALL 为 false

  Note: 离线消息补发 NOT_IMPLEMENTED — 重连后不会自动补发断线期间的消息。
  前端依赖 REST 轮询（2 秒间隔）来弥补可能丢失的消息。
```
