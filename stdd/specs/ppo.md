# Delta Spec: Simplified Policy Gradient (rlforge)

> Change: change-20260515-092930-single-agent | Domain: algorithms/policy_gradient | Type: ADDED
> Status: Draft

> **NOTE**: This spec describes the ACTUAL implementation in `agentforge/rlforge/`. The codebase
> implements a simplified policy gradient algorithm with GAE-like advantages and a value baseline,
> NOT full PPO with clipping. All computation is NumPy-based with no PyTorch dependency.

---

## Feature: PolicyNetwork

```gherkin
Feature: 2-layer MLP Policy Network
  PolicyNetwork 是一个基于 NumPy 的前馈策略网络，输出动作概率分布。

  Scenario: 网络架构
    Given PolicyNetwork(obs_dim=4, act_dim=2, hidden=32)
    Then 网络 SHALL 有 2 层权重:
      | 层  | 形状           | 初始化方式          |
      | w1  | (4, 32)       | Xavier (sqrt(2/(in+out))) |
      | b1  | (32,)         | zeros              |
      | w2  | (32, 2)       | Xavier             |
      | b2  | (2,)          | zeros              |
    And 激活函数 SHALL 为 ReLU（隐藏层）+ Softmax（输出层）

  Scenario: forward 前向传播
    Given PolicyNetwork(obs_dim=4, act_dim=2)
    When 调用 forward(obs) 输入观测向量
    Then SHALL 返回 (probs, cache)
    And probs SHALL 为 softmax 归一化的动作概率，和为 1.0
    And cache SHALL 包含 obs, h, h_act, logits, probs（用于反向传播）

  Scenario: select_action 动作选择
    Given PolicyNetwork(obs_dim=4, act_dim=2)
    And 观测值 obs
    When 调用 select_action(obs)
    Then SHALL 返回 (action, cache)
    And action SHALL 为根据概率分布随机采样的整数

  Scenario: compute_loss 策略梯度损失
    Given PolicyNetwork 和前向传播 cache
    When 调用 compute_loss(cache, action=1, advantage=0.5)
    Then 损失 SHALL 为 -log(prob[action]) * advantage（策略梯度）
    And SHALL 返回梯度字典 {"w1", "b1", "w2", "b2"}
    And 梯度 SHALL 通过手动反向传播计算（obs -> h -> h_act -> logits）
```

## Feature: Adam Optimizer

```gherkin
Feature: 内置 Adam 优化器
  PolicyNetwork 使用 Adam 优化器更新权重。

  Scenario: Adam 更新
    Given PolicyNetwork(lr=0.001)
    When 调用 update(grads) 传入梯度字典
    Then SHALL 使用 Adam 公式更新权重:
      | 参数 | 值                          |
      | beta1 | 0.9                        |
      | beta2 | 0.999                      |
      | eps   | 1e-8                       |
    And 一阶矩 m 和二阶矩 v SHALL 被维护
    And 偏差校正 SHALL 被应用

  Scenario: 首次更新初始化
    Given 新创建的 PolicyNetwork
    When 首次调用 update(grads)
    Then _m 和 _v SHALL 被初始化为与梯度相同形状的零数组
    And 时间步 _t SHALL 从 0 增加到 1
```

## Feature: Simplified Policy Gradient Training

```gherkin
Feature: RLTrainer 策略梯度训练
  RLTrainer 实现简化的策略梯度训练，使用 GAE-like 优势估计和线性 value baseline。
  注意: 这不是完整 PPO，没有 clipping，没有多 epoch mini-batch 更新。

  Scenario: GAE 优势计算
    Given RLTrainer(gamma=0.99, gae_lambda=0.95)
    And rewards=[1.0, 1.0, -1.0], values=[0.5, 0.5, 0.3], dones=[False, False, True]
    When 调用 _compute_returns(rewards, values, dones)
    Then SHALL 从后向前计算 GAE:
      delta[t] = r[t] + gamma * V(t+1) - V(t)
      A[t] = delta[t] + gamma * lambda * A[t+1]
    And done=True 时 SHALL 重置 next_value=0 和 gae=0
    And SHALL 返回 (advantages, returns) 元组

  Scenario: 线性 value baseline
    Given RLTrainer(obs_dim=4)
    Then value_w SHALL 为形状 (4,) 的零向量
    When 调用 _estimate_value(obs)
    Then SHALL 返回 float(obs @ value_w)（线性回归）
    When 调用 _update_value(obs, target)
    Then SHALL 通过梯度下降更新 value_w

  Scenario: 单步训练流程
    Given RLTrainer 创建完成
    When 调用 train(callback=None)
    Then 每个 step SHALL:
      1. 选择动作 action
      2. 估计当前状态价值 value
      3. 执行 env.step(action) 获得 StepResult
      4. 计算即时优势 advantage
      5. 计算策略梯度损失并更新 PolicyNetwork
      6. 更新线性 value baseline
      7. 生成 StepMetric

  Scenario: Episode 结束处理
    Given 训练进行中且 env.step 返回 done=True
    When episode 结束
    Then SHALL 清空 episode 累积数据（rewards, values, obs, actions, dones）
    And SHALL 重置 episode_reward=0
    And SHALL 调用 env.reset() 开始新 episode

  Scenario: 回调通知
    Given 注册了 callback 函数
    When 每个 step 完成
    Then callback SHALL 被调用
    And 参数 SHALL 为 StepMetric(step, reward, loss, episode_reward, value_estimate)
```

## Feature: TrainingConfig

```gherkin
Feature: 训练配置
  TrainingConfig 定义训练超参数。

  Scenario: 默认配置
    Given TrainingConfig()
    Then 以下参数 SHALL 有默认值:
      | 参数          | 默认值  |
      | algorithm    | "PPO"  |
      | total_steps  | 200    |
      | gamma        | 0.99   |
      | gae_lambda   | 0.95   |
      | clip_eps     | 0.2    |
      | entropy_coef | 0.01   |
      | value_coef   | 0.5    |
      | seed         | 42     |
      | obs_dim      | 4      |
      | act_dim      | 2      |
      | hidden       | 32     |
      | lr           | 0.001  |

  Scenario: 自定义配置
    When 创建 TrainingConfig(total_steps=500, lr=0.01, hidden=64)
    Then 指定参数 SHALL 被覆盖
    And 未指定参数 SHALL 保持默认值
```

## Feature: NOT IMPLEMENTED (Future Enhancements)

```gherkin
Feature: 以下功能尚未实现
  以下为可能的未来扩展，当前代码中未实现:

  Scenario: PPO Clipping Loss — NOT IMPLEMENTED
    Given 当前实现使用简单策略梯度
    Then 没有 ratio clipping 机制
    And clip_eps 配置项存在但未在训练循环中使用

  Scenario: Mini-batch 多 Epoch 更新 — NOT IMPLEMENTED
    Given 当前实现为单步更新
    Then 没有 mini-batch 划分
    And 没有多 epoch 重复利用同一批数据

  Scenario: Entropy Bonus — NOT IMPLEMENTED
    Given 当前实现为纯策略梯度损失
    Then entropy_coef 配置项存在但未在损失计算中使用
    And 没有策略熵正则化项

  Scenario: 连续动作空间 — NOT IMPLEMENTED
    Given PolicyNetwork 仅输出离散动作 softmax 概率
    Then 没有高斯策略输出
    And 不支持连续动作空间环境

  Scenario: Checkpoint 保存/恢复 — NOT IMPLEMENTED
    Given RLTrainer 没有 save/load 方法
    Then 训练状态无法持久化
```
