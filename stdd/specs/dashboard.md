# Delta Spec: Dashboard — Agent Card Grid + Training Records

> Change: change-20260515-100923-ui-dashboard | Domain: dashboard | Type: MODIFIED
> Status: Updated 2026-05-16 to reflect agent card grid + left-right split training records

---

## Feature: Dashboard Agent Card Grid

```gherkin
Feature: 仪表盘 Agent 卡片网格
  仪表盘显示所有 Agent 的卡片网格，点击卡片弹出训练记录详情。

  Background:
    Given 用户在"仪表盘"Tab

  Scenario: Agent 卡片网格展示
    Given 系统中有 N 个 Agent
    When 仪表盘加载
    Then SHALL 以响应式网格显示 Agent 卡片（grid-cols-1/2/3/4）
    And 每张卡片 SHALL 显示：头像（首字母渐变）、名称、在线状态、系统提示摘要
    And 每张卡片 SHALL 有"进化引擎"和"强化学习"标签

  Scenario: 无 Agent 时空状态
    Given 系统中无 Agent
    Then SHALL 显示"暂无智能体"提示和引导文案

  Scenario: 点击卡片打开弹窗
    When 用户点击一张 Agent 卡片
    Then SHALL 弹出模态窗口（max-w-5xl）
    And 弹窗 SHALL 显示 Agent 名称、头像、在线状态
    And 弹窗 SHALL 有"进化引擎"和"强化学习"两个 Tab

  Scenario: 关闭弹窗
    When 用户点击弹窗外部或关闭按钮
    Then SHALL 关闭弹窗
```

## Feature: Training Record List

```gherkin
Feature: 训练记录列表
  每个 Tab 显示该 Agent 的历史训练记录列表。

  Scenario: 进化引擎训练记录
    Given 用户点击 Agent 弹窗的"进化引擎"Tab
    Then SHALL 调用 GET /api/agents/{id}/evolution/runs
    And SHALL 显示训练记录列表
    And 每条记录 SHALL 显示：状态徽章（已完成/运行中/已取消）、模式名称、代数进度、最优适应度

  Scenario: RL 训练记录
    Given 用户点击 Agent 弹窗的"强化学习"Tab
    Then SHALL 调用 GET /api/agents/{id}/rl/runs
    And 每条记录 SHALL 显示：状态徽章、算法名称、步数进度、最终奖励和损失

  Scenario: 无记录时空状态
    Given 该 Agent 无训练记录
    Then SHALL 显示"暂无训练记录"提示和引导文案

  Scenario: 展开训练记录
    When 用户点击一条记录
    Then SHALL 展开该记录的详情（左侧日志 + 右侧图表）
    And 再次点击 SHALL 收起
```

## Feature: Left-Right Split Layout (Logs + Charts)

```gherkin
Feature: 训练记录详情左右分栏
  展开训练记录后，左侧显示可滚动日志表格，右侧显示图表。

  Scenario: 进化引擎分栏布局
    Given 用户展开一条进化训练记录
    Then SHALL 调用 GET /api/evolution/{runId} 获取详情
    And 顶部 SHALL 显示 4 格配置摘要（模式/种群×代数/变异率/精英数）
    And 下方 SHALL 左右分栏：
      | 区域 | 宽度 | 内容 |
      | 左侧 | 45% | 可滚动日志表格（代数/最优/均值/标准差/多样性） |
      | 右侧 | 55% | 图表区（适应度曲线 + 面积图 + 进化树） |

  Scenario: RL 训练分栏布局
    Given 用户展开一条 RL 训练记录
    Then SHALL 调用 GET /api/rl/{runId} 获取详情
    And 顶部 SHALL 显示 4 格配置摘要（算法/步数/学习率/状态）
    And 下方 SHALL 左右分栏：
      | 区域 | 宽度 | 内容 |
      | 左侧 | 45% | 可滚动日志表格（步数/奖励/损失） |
      | 右侧 | 55% | 图表区（奖励曲线 + 损失曲线 + 奖励vs损失对比） |

  Scenario: 日志表格样式
    Given 日志数据加载完成
    Then 表头 SHALL 为 sticky 固定
    And 偶数行 SHALL 有交替背景色
    And 数值 SHALL 使用等宽字体（font-mono）
    And 各列 SHALL 有颜色区分（最优=蓝、均值=绿、标准差=橙）

  Scenario: 运行中自动刷新
    Given 展开的训练记录状态为 running
    Then SHALL 每 1.5 秒自动轮询更新数据
    And 记录完成后 SHALL 停止轮询
```

## Feature: Chart Zoom (放大功能)

```gherkin
Feature: 图表放大按钮
  每个图表卡片都有放大按钮，点击后弹出全屏 Overlay。

  Scenario: 放大按钮
    Given 任意图表卡片渲染
    Then 右上角 SHALL 有"⤢ 放大"按钮

  Scenario: 全屏 ZoomOverlay
    When 用户点击放大按钮
    Then SHALL 弹出全屏黑色半透明遮罩
    And 遮罩内 SHALL 显示白色卡片（max-w-5xl）
    And 图表 SHALL 以更大高度渲染（500px vs 内联 200-320px）

  Scenario: 关闭 ZoomOverlay
    When 用户点击遮罩区域或关闭按钮
    Then SHALL 关闭全屏视图

  Scenario: 降采样标记
    Given 数据点超过 LTTB_MAX (2000)
    When 图表渲染
    Then SHALL 显示"已降采样"橙色标签
```

## Feature: Fitness Curves (Recharts)

```gherkin
Feature: 适应度曲线
  进化训练详情右侧显示 Recharts LineChart。

  Scenario: best/mean/std 三线图
    Then SHALL 渲染 LineChart 包含：
      | 曲线  | 颜色   | 样式       |
      | 最优  | #3b82f6 | 实线 strokeWidth=2 |
      | 均值  | #22c55e | 实线 strokeWidth=2 |
      | 标准差 | #f97316 | 虚线 strokeDasharray="5 5" |

  Scenario: 面积图
    Then SHALL 渲染 AreaChart（best 蓝色填充 + mean 绿色填充）
```

## Feature: Gene Tree (SVG)

```gherkin
Feature: 进化树 SVG 可视化
  GeneTreeView 组件渲染种群谱系树。

  Scenario: 节点颜色映射
    Given 每个个体有适应度值
    Then 低适应度 SHALL 为红色，高适应度 SHALL 为绿色

  Scenario: 上限
    Then 节点 SHALL 上限 100 个，边上限 200 条
```

## Feature: RL Metrics (Recharts)

```gherkin
Feature: RL 训练曲线
  RL 训练详情右侧显示 Recharts LineChart。

  Scenario: 奖励曲线
    Then SHALL 渲染紫色 (#8b5cf6) 奖励折线图

  Scenario: 损失曲线
    Then SHALL 渲染红色 (#ef4444) 损失折线图

  Scenario: 奖励 vs 损失对比
    Given 两个指标都存在
    Then SHALL 渲染双 Y 轴对比 LineChart（左=奖励，右=损失）
```

## Feature: Performance Protection (LTTB)

```gherkin
Feature: LTTB 降采样
  数据点超过 2000 时自动降采样。

  Scenario: 降采样触发
    Given 任一曲线数据点 > 2000
    When 渲染图表
    Then SHALL 使用 LTTB 算法降采样至 2000 点
    And 图表卡片 SHALL 显示"已降采样"标记

  Scenario: 无需降采样
    Given 数据点 <= 2000
    Then SHALL 直接渲染原始数据
```
