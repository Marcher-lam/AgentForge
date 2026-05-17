# Delta Spec: DQN Algorithm

> Change: change-20260515-092930-single-agent | Domain: algorithms/dqn | Type: ADDED
> Status: **NOT IMPLEMENTED**

> **IMPORTANT**: DQN is NOT implemented in the current codebase. The `rlforge/algorithms/dqn/`
> directory exists with config and trainer stubs but contains no functional implementation.
> All RL training uses the simplified policy gradient approach described in `ppo.md`.
> This spec is retained as a placeholder for future development.

---

## Feature: DQN — NOT IMPLEMENTED

```gherkin
Feature: DQN 未实现
  DQN 算法当前仅有目录结构占位，无实际功能代码。

  Scenario: 目录存在但无实现
    Given rlforge/algorithms/dqn/ 目录存在
    And 包含 __init__.py, config.py, trainer.py
    Then 这些文件 SHALL 仅包含类/配置的骨架定义
    And 不 SHALL 包含可运行的 DQN 训练逻辑

  Scenario: 训练入口映射
    Given app.py 中 RLTrainingRun 的 algo_map
    Then 请求 algorithm="DQN" 时 SHALL 映射到 "REINFORCE"（降级处理）
    And 不使用任何 DQN 特定逻辑
```

## Feature: Future DQN Specification (Placeholder)

```gherkin
Feature: Q-Network（未来实现）
  以下为 DQN 实现时应满足的规范。

  Scenario: 离散动作空间输出
    Given 状态空间维度 4, 动作空间维度 2
    And Q-Network 配置 hidden_layers=[256, 256]
    When 输入状态 [1.0, 0.5, -0.3, 0.8]
    Then SHALL 输出 2 个 Q 值
    And 输出值 SHALL 为浮点数

  Scenario: Experience Replay Buffer
    Given ReplayBuffer 容量 10000
    When 存储 100 条 transition
    And 采样 batch_size=64
    Then SHALL 返回 64 条随机 transition
    And 容量溢出时最早 transition SHALL 被丢弃

  Scenario: Target Network
    Given target_update_freq=1000
    When 训练到第 1000 步
    Then 目标网络权重 SHALL 复制在线网络

  Scenario: Epsilon-Greedy 探索
    Given epsilon_start=1.0, epsilon_end=0.01, epsilon_decay=50000
    When 训练逐步进行
    Then epsilon SHALL 从 1.0 线性衰减到 0.01

  Scenario: CartPole 收敛目标
    Given DQN 完整实现
    And seed=42
    When 在 CartPole 上训练
    Then 100 episode 均值目标 SHALL >= 475
```

## Feature: NOT IMPLEMENTED Items

```gherkin
Feature: 以下 DQN 特性均未实现
  当前代码库不包含以下任何功能:

  Scenario: Dueling DQN — NOT IMPLEMENTED
  Scenario: Double DQN — NOT IMPLEMENTED
  Scenario: Prioritized Experience Replay — NOT IMPLEMENTED
  Scenario: Soft/Hard Target Network Update — NOT IMPLEMENTED
  Scenario: ReplayBuffer (线程安全) — NOT IMPLEMENTED
  Scenario: PyTorch 依赖 — NOT IMPLEMENTED（当前仅使用 NumPy）
```
