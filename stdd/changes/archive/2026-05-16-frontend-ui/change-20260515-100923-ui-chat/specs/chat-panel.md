# Delta Spec: Agent Chat UI

> Change: change-20260515-100923-ui-chat | Domain: chat | Type: ADDED
> Status: Draft

---

## Feature: Message Panel

```gherkin
Feature: 消息列表展示
  用户 SHALL 在消息列表中看到区分用户和 Agent 的消息，支持多类型渲染。

  Scenario: 区分用户和 Agent 消息
    Given 用户发送 "你好" 和 Agent 回复 "我是 Agent"
    When 消息列表渲染
    Then 用户消息 SHALL 显示在右侧，Agent 消息 SHALL 显示在左侧
    And 消息 SHALL 有不同的视觉样式区分发送者

  Scenario: Markdown 消息渲染
    Given Agent 回复包含 Markdown 格式 "# 标题\n- 列表项\n**粗体**"
    When 消息列表渲染
    Then SHALL 正确渲染为标题、列表和粗体文本

  Scenario: 代码高亮
    Given Agent 回复包含 "```python\nprint('hello')\n```"
    When 消息列表渲染
    Then SHALL 显示带语法高亮的代码块

  Scenario: 图片和文件消息
    Given Agent 回复包含图片 URL
    When 消息列表渲染
    Then SHALL 显示图片预览
    And 文件附件 SHALL 显示文件名和下载链接

  Scenario: 虚拟滚动长列表
    Given 消息列表有 10000 条消息
    When 用户滚动浏览
    Then SHALL 使用虚拟滚动，仅渲染可见区域
    And 滚动 SHALL 流畅无卡顿

  Scenario: 向上滚动加载更多
    Given 已显示最近 50 条消息
    When 用户滚动到列表顶部
    Then SHALL 加载更早的历史消息
    And 滚动位置 SHALL 保持不变
```

## Feature: Input Box

```gherkin
Feature: 类 ChatGPT 输入框
  用户 SHALL 使用类 ChatGPT 的输入交互。

  Scenario: Enter 发送消息
    Given 输入框有文本 "测试消息"
    When 用户按 Enter 键
    Then SHALL 发送消息
    And 输入框 SHALL 清空

  Scenario: Shift+Enter 换行
    Given 输入框有文本
    When 用户按 Shift+Enter
    Then SHALL 插入换行符
    And SHALL NOT 发送消息

  Scenario: 自动扩展高度
    Given 输入框为单行高度
    When 用户输入多行文本
    Then 输入框高度 SHALL 自动扩展
    And 最大高度 SHALL 有上限（超过则出现滚动条）
```

## Feature: Multi-Agent Grid View

```gherkin
Feature: 自由拖拽网格布局
  用户 SHALL 可自由拖拽 Agent 卡片布局。

  Scenario: 自由拖拽定位
    Given 多 Agent 网格视图有 4 个 Agent 卡片
    When 用户拖拽 Agent-A 到新位置
    Then Agent-A SHALL 移动到新位置
    And 其他卡片位置 SHALL 不变

  Scenario: 卡片可重叠
    Given Agent-A 和 Agent-B 的卡片
    When 用户拖拽 Agent-A 到 Agent-B 位置
    Then Agent-A SHALL 可覆盖在 Agent-B 之上
    And 被覆盖的卡片 SHALL 仍可点击选中

  Scenario: Agent 信息卡片
    Given Agent 卡片展示
    Then SHALL 包含：头像、名称、状态指示灯、最新消息预览、操作按钮
    And 状态指示灯 SHALL 实时反映 Agent 状态（在线/离线/忙碌）

  Scenario: 响应式布局
    Given 桌面端宽度（≥ 1200px）
    Then SHALL 显示 3+ 列网格
    Given 平板宽度（768px - 1199px）
    Then SHALL 显示 2 列
    Given 手机宽度（< 768px）
    Then SHALL 显示 1 列
```

## Feature: 1v1 Session

```gherkin
Feature: 一对一私聊会话
  用户 SHALL 可与单个 Agent 进行独立私聊。

  Scenario: 创建 1v1 会话
    Given 用户点击 Agent-A 的"私聊"按钮
    When 创建会话
    Then SHALL 打开独立的消息面板
    And 消息流 SHALL 仅包含用户和 Agent-A 的对话

  Scenario: 多个 1v1 会话切换
    Given 用户与 Agent-A 和 Agent-B 各有 1v1 会话
    When 用户在两个会话间切换
    Then 各会话消息流 SHALL 独立
    And 未读消息数 SHALL 正确显示
```

## Feature: Group Session

```gherkin
Feature: 群组会话
  用户 SHALL 可进行一对多广播和多播。

  Scenario: 广播模式
    Given 群组有 5 个 Agent
    When 用户发送消息
    Then 所有 5 个 Agent SHALL 收到消息
    And 每个 Agent 的回复 SHALL 在消息流中可见

  Scenario: 多播模式
    Given 群组有 5 个 Agent
    When 用户选择 Agent-A 和 Agent-B 作为接收者并发送消息
    Then 仅 Agent-A 和 Agent-B SHALL 收到消息
    And 其他 3 个 Agent SHALL NOT 收到

  Scenario: WebSocket 实时通信
    Given WebSocket 连接正常
    When Agent 发送回复
    Then 用户 SHALL 在 200ms 内看到回复
```

## Feature: Connection Resilience

```gherkin
Feature: 连接断线处理
  用户 SHALL 在网络断线时获得明确反馈和自动恢复。

  Scenario: 断线提示
    Given WebSocket 连接正常
    When 连接意外断开
    Then SHALL 显示"连接已断开"提示横幅
    And 输入框 SHALL 禁用发送按钮

  Scenario: 自动重连
    Given 连接已断开
    When 系统自动尝试重连
    Then SHALL 最多重试 3 次，间隔 2 秒
    And 重连成功后 SHALL 恢复正常消息收发
    And 提示横幅 SHALL 自动消失

  Scenario: 重连失败
    Given 连续 3 次重连均失败
    Then SHALL 显示"无法连接服务器"错误状态
    And SHALL 显示"重试"按钮供用户手动触发

  Scenario: 离线消息补发
    Given 断线期间有 5 条新消息
    When 重连成功
    Then 5 条离线消息 SHALL 按时间顺序插入消息列表
    And SHALL 标记为"离线期间消息"
```
