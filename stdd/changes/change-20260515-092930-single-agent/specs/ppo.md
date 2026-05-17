# Delta Spec: PPO Algorithm

> Change: change-20260515-092930-single-agent | Domain: algorithms/ppo | Type: ADDED
> Status: Draft

---

## Feature: Actor-Critic Network

```gherkin
Feature: Actor-Critic 网络架构
  PPO SHALL 使用 Actor-Critic 架构。

  Scenario: 离散动作空间输出
    Given 离散动作空间维度 2
    When Actor 前向传播
    Then SHALL 输出动作概率分布 [p1, p2]，p1+p2=1
    And Critic SHALL 输出单一值函数估计 V(s)

  Scenario: 连续动作空间输出
    Given 连续动作空间维度 1
    When Actor 前向传播
    Then SHALL 输出均值 mu 和标准差 sigma
    And 动作 SHALL 通过 N(mu, sigma) 采样

  Scenario: 共享特征提取层
    Given Actor 和 Critic 共享 hidden_layers=[256, 256]
    When 前向传播
    Then 共享层 SHALL 只计算一次
    And Actor 头和 Critic 头 SHALL 分别输出
```

## Feature: GAE Computation

```gherkin
Feature: 广义优势估计 (GAE)
  PPO SHALL 使用 GAE 计算优势函数。

  Scenario: GAE 计算
    Given 一条 trajectory 的 rewards=[1.0, 1.0, 1.0, 1.0]
    And values=[0.5, 0.5, 0.5, 0.5]
    And gamma=0.99, lambda=0.95
    When 计算 GAE
    Then SHALL 返回每个时间步的优势估计

  Scenario: lambda=0 退化为 TD(0)
    Given lambda=0
    When 计算 GAE
    Then 优势 SHALL 等于 r + γ*V(s') - V(s)

  Scenario: lambda=1 退化为 Monte Carlo
    Given lambda=1
    When 计算 GAE
    Then 优势 SHALL 等于折扣累积奖励 - V(s)
```

## Feature: PPO Clipping Loss

```gherkin
Feature: PPO-Clip 损失函数
  PPO SHALL 使用 clipped surrogate objective。

  Scenario: ratio 在 clip 范围内
    Given ratio = 0.8, advantage = 1.0, clip_range = 0.2
    When 计算 PPO loss
    Then clipped_ratio SHALL 为 clamp(0.8, 0.8, 1.2) = 0.8
    And loss SHALL 为 -min(0.8 * 1.0, 0.8 * 1.0) = -0.8

  Scenario: ratio 超出 clip 范围
    Given ratio = 1.5, advantage = 1.0, clip_range = 0.2
    When 计算 PPO loss
    Then clipped_ratio SHALL 为 clamp(1.5, 0.8, 1.2) = 1.2
    And loss SHALL 为 -min(1.5, 1.2) = -1.2（被 clip 截断）

  Scenario: clip_range 可配置
    Given clip_range = 0.1
    When 计算 PPO loss
    Then SHALL 在 [0.9, 1.1] 范围内 clip
```

## Feature: Mini-batch Updates

```gherkin
Feature: Mini-batch 更新
  PPO SHALL 使用 mini-batch 多轮更新。

  Scenario: 多 epoch 更新
    Given n_steps=2048, batch_size=64, epochs=10
    When 执行一次更新
    Then SHALL 将 2048 步数据分成 32 个 mini-batch
    And 每个 mini-batch 更新 10 轮（epoch）

  Scenario: epoch 数可配置
    Given epochs=5
    When 执行更新
    Then SHALL 更新 5 轮

  Scenario: 数据打乱
    Given 每个 epoch 开始
    When 准备 mini-batch
    Then SHALL 随机打乱数据顺序
```

## Feature: Entropy Bonus

```gherkin
Feature: 熵正则化
  PPO SHALL 加入策略熵 bonus 鼓励探索。

  Scenario: 熵 bonus 计算
    Given entropy_coef=0.01
    And 当前策略熵 H = 0.5
    When 计算总 loss
    Then 总 loss SHALL 为 policy_loss - 0.01 * 0.5 + value_loss

  Scenario: 熵 bonus 可配置
    Given entropy_coef=0.0
    When 计算 loss
    Then SHALL 不包含熵项
```

## Feature: PPO Training Convergence

```gherkin
Feature: PPO 在 CartPole 上收敛
  PPO SHALL 在 CartPole-v1 上达到 100 episode 均值 ≥ 475。

  Scenario: CartPole 收敛验收
    Given PPOConfig 默认超参数
    And seed=42（可复现）
    When 训练 ≤ 200000 步
    Then 最后 100 episode 均值 SHALL ≥ 475

  Scenario: 连续动作空间支持
    Given Pendulum-v1 环境（连续动作空间）
    When 训练 PPO
    Then SHALL 使用高斯策略
    And 训练 SHALL 正常收敛（reward 上升）

  Scenario: 收敛预算上限
    Given 训练已达 200000 步
    And 100 episode 均值 < 475
    Then 训练 SHALL 终止（预算耗尽）
```
