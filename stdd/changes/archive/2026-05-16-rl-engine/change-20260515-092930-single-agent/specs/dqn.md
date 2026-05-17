# Delta Spec: DQN Algorithm

> Change: change-20260515-092930-single-agent | Domain: algorithms/dqn | Type: ADDED
> Status: Draft

---

## Feature: Q-Network

```gherkin
Feature: Q 网络前向传播
  DQN 使用 Q 网络估计状态-动作值函数。

  Scenario: 离散动作空间输出
    Given 状态空间维度 4, 动作空间维度 2
    And Q-Network 配置 hidden_layers=[256, 256]
    When 输入状态 [1.0, 0.5, -0.3, 0.8]
    Then SHALL 输出 2 个 Q 值
    And 输出值 SHALL 为浮点数

  Scenario: Dueling DQN 架构
    Given use_dueling=True
    When 前向传播
    Then SHALL 分别计算 Value 流和 Advantage 流
    And Q(s,a) SHALL 为 V(s) + (A(s,a) - mean(A(s,a')))

  Scenario: 网络 MLP 可配置
    Given hidden_layers=[128, 128, 64]
    When 创建 Q-Network
    Then 隐藏层维度 SHALL 为 [128, 128, 64]
```

## Feature: Experience Replay

```gherkin
Feature: 经验回放缓冲区
  DQN SHALL 使用经验回放打破数据相关性。

  Scenario: 存储和采样
    Given ReplayBuffer 容量 10000
    When 存储 100 条 transition
    And 采样 batch_size=64
    Then SHALL 返回 64 条随机 transition

  Scenario: 容量溢出
    Given ReplayBuffer 容量 1000
    When 存储第 1001 条 transition
    Then 最早的 transition SHALL 被丢弃
    And buffer 大小 SHALL 保持 1000
```

## Feature: Target Network

```gherkin
Feature: 目标网络更新
  DQN SHALL 使用目标网络稳定训练。

  Scenario: 硬更新（默认）
    Given target_update_freq=1000, use_soft_update=False
    When 训练到第 1000 步
    Then 目标网络权重 SHALL 完全复制在线网络

  Scenario: 软更新
    Given use_soft_update=True, tau=0.005
    When 每步训练后
    Then 目标网络 SHALL 按 θ_target = τ*θ_online + (1-τ)*θ_target 更新

  Scenario: 更新策略可配置切换
    Given 配置 use_soft_update=False（硬更新）
    When 运行训练
    Then SHALL 使用硬更新策略
    When 运行时切换为 use_soft_update=True
    Then SHALL 切换为软更新策略
```

## Feature: Double DQN

```gherkin
Feature: Double DQN
  DQN SHALL 支持 Double DQN 减少过估计。

  Scenario: Double DQN 动作选择
    Given use_double_dqn=True
    When 计算目标 Q 值
    Then SHALL 用在线网络选择动作
    And 用目标网络评估该动作的 Q 值

  Scenario: 标准 DQN 对比
    Given use_double_dqn=False
    When 计算目标 Q 值
    Then SHALL 用目标网络同时选择和评估动作（max 操作）
```

## Feature: Epsilon-Greedy Exploration

```gherkin
Feature: ε-greedy 探索策略
  DQN SHALL 使用 ε-greedy 平衡探索与利用。

  Scenario: 初始随机探索
    Given epsilon=1.0
    When 选择动作
    Then SHALL 100% 随机选择动作

  Scenario: 衰减到最终值
    Given epsilon_start=1.0, epsilon_end=0.01, epsilon_decay=50000
    When 训练到第 50000 步
    Then epsilon SHALL 衰减到约 0.01

  Scenario: 最终利用
    Given epsilon=0.01
    When 选择动作
    Then SHALL 99% 选择最优动作，1% 随机
```

## Feature: DQN Training Convergence

```gherkin
Feature: DQN 在 CartPole 上收敛
  DQN SHALL 在 CartPole-v1 上达到 100 episode 均值 ≥ 475。

  Scenario: CartPole 收敛验收
    Given DQNConfig 默认超参数
    And seed=42（可复现）
    When 训练 ≤ 500000 步
    Then 最后 100 episode 均值 SHALL ≥ 475

  Scenario: 收敛预算上限
    Given 训练已达 500000 步
    And 100 episode 均值 < 475
    Then 训练 SHALL 终止（预算耗尽）
```
