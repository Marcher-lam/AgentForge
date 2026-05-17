# Delta Spec: Agent Communication Monitor

> Change: change-20260515-100923-ui-monitor | Domain: monitor | Type: ADDED
> Status: Updated to reflect actual implementation

---

## Feature: Message List View

```gherkin
Feature: 消息列表视图
  MonitorPage 组件以列表形式显示所有通信消息。

  Scenario: 消息列表渲染
    Given 监控页面有消息数据
    When 渲染消息列表
    Then 每条消息 SHALL 显示为一行：
      | 字段       | 样式                        |
      | sender_id  | 蓝色等宽字体（前 8 位截断）  |
      | 箭头       | 灰色 "→"                    |
      | receiver_id| 紫色等宽字体（前 8 位截断，无则显示 "*"）|
      | topic      | 灰色，flex-1 截断            |
      | timestamp  | 灰色小字，toLocaleTimeString |

  Scenario: 点击消息查看详情
    Given 消息列表中有一条消息
    When 用户点击该消息行
    Then 右侧 SHALL 打开详情面板（w-80）
    And 详情面板 SHALL 显示：
      | 字段   | 样式                    |
      | 发送者 | font-mono，完整 UUID    |
      | 接收者 | font-mono，无则显示 "broadcast" |
      | 主题   | topic 文本              |
      | 类型   | message_type 文本       |
      | 时间戳 | ISO 格式                |
      | 载荷   | JSON.stringify 格式化，pre 包裹 |
    And 详情面板 SHALL 有 "关闭" 按钮
```

## Feature: Keyword Filter

```gherkin
Feature: 关键词过滤
  监控页面支持按关键词过滤消息。

  Scenario: 关键词搜索
    Given 过滤输入框
    When 用户输入关键词 "error"
    Then SHALL 过滤消息列表
    And 过滤条件 SHALL 匹配 payload 的 JSON 字符串或 topic 字段
    And 匹配使用 String.includes（不区分大小写的子串匹配）

  Scenario: 清空过滤
    Given 过滤关键词已输入
    When 用户清空输入框
    Then SHALL 显示全部消息
```

## Feature: Pause/Resume

```gherkin
Feature: 暂停/恢复监视
  用户可暂停监视画面。

  Scenario: 暂停监视
    Given 监控页面正在显示消息
    When 用户点击 "Pause" 按钮
    Then isPaused 状态 SHALL 切换为 true
    And 按钮样式 SHALL 变为红色背景 (bg-red-100 text-red-700)
    And 按钮文字 SHALL 变为 "Resume"

  Scenario: 恢复监视
    Given 监控已暂停
    When 用户点击 "Resume" 按钮
    Then isPaused 状态 SHALL 切换为 false
    And 按钮样式 SHALL 变为绿色背景 (bg-green-100 text-green-700)
    And 按钮文字 SHALL 变为 "Pause"

  Note: 暂停功能通过 monitorPausedAtom 控制，但 MonitorPage 组件本身不管理消息队列。
  暂停期间的消息是否积累取决于 App 层如何响应 monitorPaused 状态。
```

## Feature: Topology Graph

```gherkin
Feature: Agent 节点图可视化
  NOT_IMPLEMENTED — 节点图、力导向布局、消息流动画均未实现。

  MonitorPage 的 props 接受 nodes 和 edges 参数，但 App.tsx 传入空数组 (nodes=[], edges=[])。
  以下原 spec 功能均未实现：
  - 自动布局 Agent 节点（力导向布局）
  - 手动拖拽调整节点
  - 消息流动画（Framer Motion 粒子）
  - 消息频率视觉映射（连线粗细/亮度）
```

## Feature: Timeline

```gherkin
Feature: 时间轴联动视图
  NOT_IMPLEMENTED — 时间轴联动未实现。

  当前只有简单的消息列表，没有节点图+时间轴的联动布局。
```

## Feature: Statistics

```gherkin
Feature: 统计面板
  NOT_IMPLEMENTED — 实时通信统计面板未实现。

  以下统计指标均未实现：
  - total_messages
  - messages_per_sec
  - avg_latency
  - per_agent_send / per_agent_recv
  - topic_distribution
```
