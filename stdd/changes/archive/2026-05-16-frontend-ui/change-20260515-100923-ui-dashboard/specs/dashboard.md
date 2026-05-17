# Delta Spec: Evolution & RL Training Dashboard

> Change: change-20260515-100923-ui-dashboard | Domain: dashboard | Type: ADDED
> Status: Draft

---

## Feature: Dashboard Layout

```gherkin
Feature: Tab 切换布局
  仪表板 SHALL 通过 Tab 切换进化/RL 两个监控模式。

  Scenario: 进化模式 Tab
    Given 仪表板加载
    When 用户选择"进化"Tab
    Then SHALL 显示进化仪表板组件：适应度曲线 + 基因树 + 热力图 + 进度条

  Scenario: RL 模式 Tab
    Given 仪表板加载
    When 用户选择"RL 训练"Tab
    Then SHALL 显示 RL 监控组件：reward 曲线 + loss 曲线 + 超参数面板

  Scenario: Tab 切换保持状态
    Given 用户在"进化"Tab 查看数据
    When 切换到"RL"Tab 再切回
    Then 进化 Tab 的图表状态 SHALL 保持（不重新加载）
```

## Feature: Fitness Curve (Evolution)

```gherkin
Feature: 适应度曲线实时绘制
  仪表板 SHALL 实时绘制每代的适应度曲线。

  Scenario: best/mean/std 曲线
    Given 进化引擎在运行
    When 每代完成
    Then SHALL 在 ECharts 图表中追加数据点：
      | 曲线         | 数据源              |
      | best_fitness | 当代最优个体适应度    |
      | mean_fitness | 当代平均适应度        |
      | std_fitness  | 当代适应度标准差      |

  Scenario: 实时更新
    Given 更新频率配置为 1s
    When 后端推送新一代数据
    Then 图表 SHALL 在 1s 内更新
    And 端到端延迟 SHALL < 1s
```

## Feature: Gene Tree (Evolution)

```gherkin
Feature: 基因世代树
  仪表板 SHALL 渲染进化世代树。

  Scenario: 世代树渲染
    Given 进化引擎有 10 代数据
    When 渲染基因树
    Then SHALL 使用 ECharts tree 图表
    And 根节点为初代，叶子为当代个体

  Scenario: 适应度颜色映射
    Given 树中每个个体有适应度值
    When 渲染节点
    Then 节点颜色 SHALL 映射适应度（高→绿/亮，低→红/暗）

  Scenario: 点击个体查看基因
    Given 树中一个个体节点
    When 用户点击该节点
    Then SHALL 弹出详情面板，显示该个体的基因值
    And 图表交互 SHALL 支持缩放和展开/折叠
```

## Feature: Population Heatmap

```gherkin
Feature: 种群分布热力图
  仪表板 SHALL 显示基因×个体热力图。

  Scenario: 热力图渲染
    Given 种群有 100 个个体，每个基因 50 维
    When 渲染热力图
    Then X 轴 SHALL 为基因维度，Y 轴为个体
    And 颜色 SHALL 映射基因值（低→蓝，高→红）

  Scenario: 种群多样性可视化
    Given 种群多样性高
    When 查看热力图
    Then 颜色分布 SHALL 较分散
    Given 种群早熟收敛
    When 查看热力图
    Then 颜色分布 SHALL 高度一致
```

## Feature: RL Training Curves

```gherkin
Feature: RL 训练指标曲线
  仪表板 SHALL 实时显示 RL 训练全量指标。

  Scenario: 全量指标曲线
    Given RL 训练在运行
    When 数据推送
    Then SHALL 绘制以下曲线：
      | 指标            | 描述              |
      | episode_reward  | 每个 episode 总奖励 |
      | loss            | 训练损失           |
      | episode_length  | episode 步数       |
      | exploration_rate| 探索率             |
      | learning_rate   | 学习率             |
      | grad_norm       | 梯度范数           |

  Scenario: 多 run 对比
    Given 有 3 条训练 run 数据
    When 在 RL 模式下查看
    Then SHALL 同时显示 3 条 reward 曲线
    And 每条曲线 SHALL 用不同颜色区分
    And 图例 SHALL 标注 run 名称和超参数
```

## Feature: Chart Interactions

```gherkin
Feature: 图表丰富交互
  所有图表 SHALL 支持丰富的交互操作。

  Scenario: 悬停 tooltip
    Given 适应度曲线图
    When 鼠标悬停在数据点上
    Then SHALL 显示 tooltip，包含世代号、适应度值

  Scenario: 缩放
    Given 图表已渲染
    When 用户滚动鼠标滚轮
    Then SHALL 缩放图表视图

  Scenario: 拖拽选区
    Given 图表已渲染
    When 用户拖拽选择一个区域
    Then SHALL 放大该区域

  Scenario: 数据导出
    Given 图表有数据
    When 用户点击"导出"按钮
    Then SHALL 导出为 CSV 或 PNG
```

## Feature: Performance Protection

```gherkin
Feature: 数据点降采样保护
  图表 SHALL 使用 LTTB 算法保护渲染性能。

  Scenario: 10k 数据点以内正常显示
    Given 图表数据点 ≤ 10000
    When 渲染图表
    Then SHALL 显示全部数据点

  Scenario: 超过 10k 自动降采样
    Given 图表数据点 = 50000
    When 渲染图表
    Then SHALL 使用 LTTB 算法降采样到 10000 点
    And 降采样后 SHALL 保持视觉保真度

  Scenario: 更新频率可配置
    Given 更新频率配置为 5s
    When 数据推送
    Then SHALL 每 5s 更新一次图表
```
