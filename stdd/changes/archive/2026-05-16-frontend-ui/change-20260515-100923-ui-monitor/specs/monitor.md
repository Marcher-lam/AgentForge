# Delta Spec: Agent Communication Monitor

> Change: change-20260515-100923-ui-monitor | Domain: monitor | Type: ADDED
> Status: Draft

---

## Feature: Agent Node Graph

```gherkin
Feature: Agent 节点图可视化
  用户 SHALL 在节点图中看到 Agent 间消息流转。

  Scenario: 自动布局 Agent 节点
    Given 5 个 Agent 在线
    When 节点图首次渲染
    Then SHALL 自动计算节点位置（力导向布局）
    And 每个 Agent SHALL 为一个节点，显示名称和状态

  Scenario: 手动拖拽调整节点
    Given 节点图已渲染
    When 用户拖拽 Agent-A 节点到新位置
    Then Agent-A SHALL 移动到新位置
    And 连接线 SHALL 自动跟随

  Scenario: 消息流动画
    Given Agent-A 向 Agent-B 发送消息
    When 消息流转中
    Then SHALL 显示从 Agent-A 到 Agent-B 的有向箭头
    And 沿箭头方向 SHALL 有动画粒子流动
    And 粒子 SHALL 使用 Framer Motion 动画

  Scenario: 消息频率视觉映射
    Given Agent-A 和 Agent-B 之间消息频繁
    When 节点图渲染
    Then A-B 之间的连线 SHALL 更粗或更亮
    And 低频连线 SHALL 更细或更暗
```

## Feature: Timeline

```gherkin
Feature: 时间轴联动视图
  节点图 SHALL 与时间轴联动。

  Scenario: 节点图 + 时间轴布局
    Given 监视器页面
    Then 左侧 SHALL 为节点图，右侧 SHALL 为时间轴
    And 时间轴 SHALL 按时间顺序列出所有消息

  Scenario: 点击时间轴跳转
    Given 时间轴显示消息列表
    When 用户点击时间轴中某条消息
    Then 节点图 SHALL 高亮该消息的发送者和接收者
    And 消息详情面板 SHALL 显示该消息
```

## Feature: Message Details

```gherkin
Feature: 消息详情面板
  用户 SHALL 可点击消息查看完整内容。

  Scenario: 查看消息详情
    Given 节点图上有一条消息
    When 用户点击该消息
    Then SHALL 打开详情面板，显示：
      | field     |
      | payload   |
      | timestamp |
      | topic     |
      | sender    |
      | receiver  |
      | message type |
```

## Feature: Filtering

```gherkin
Feature: 多维度消息过滤
  用户 SHALL 可按多个维度过滤消息。

  Scenario: 按 Agent 过滤
    Given 过滤器选择 Agent-A
    When 应用过滤
    Then 仅显示 Agent-A 发送或接收的消息

  Scenario: 按 topic 过滤
    Given 过滤器输入 topic "task.result"
    When 应用过滤
    Then 仅显示该 topic 的消息

  Scenario: 按时间范围过滤
    Given 过滤器设置时间范围 10:00 - 11:00
    When 应用过滤
    Then 仅显示该时间段内的消息

  Scenario: 按 payload 关键字搜索
    Given 搜索框输入 "error"
    When 执行搜索
    Then 仅显示 payload 包含 "error" 的消息
```

## Feature: Statistics

```gherkin
Feature: 统计面板
  监视器 SHALL 实时展示通信统计。

  Scenario: 多维度统计
    Given 统计面板渲染
    Then SHALL 实时显示：
      | 指标               | 描述              |
      | total_messages     | 总消息量          |
      | messages_per_sec   | 每秒消息数        |
      | avg_latency        | 平均延迟          |
      | per_agent_send     | 每个 Agent 发送量 |
      | per_agent_recv     | 每个 Agent 接收量 |
      | topic_distribution | topic 分布图      |
```

## Feature: Pause/Resume

```gherkin
Feature: 暂停/恢复监视
  用户 SHALL 可暂停监视画面。

  Scenario: 暂停监视
    Given 监视器正在实时更新
    When 用户点击"暂停"按钮
    Then 画面 SHALL 冻结，不更新新消息
    And 后台 SHALL 继续接收消息但不渲染

  Scenario: 恢复监视
    Given 监视器已暂停
    When 用户点击"恢复"按钮
    Then SHALL 显示暂停期间积累的消息
    And 画面 SHALL 恢复实时更新
```
