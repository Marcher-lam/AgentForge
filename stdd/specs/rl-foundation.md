# Delta Spec: RL Foundation Layer (rlforge)

> Change: change-20260515-092930-foundation | Domain: foundation | Type: ADDED
> Status: Draft

> **NOTE**: This spec describes the ACTUAL implementation in `agentforge/rlforge/`. The RL foundation
> uses NumPy exclusively — no PyTorch. The Environment returns a 4-tuple (obs, reward, done, info),
> not the Gymnasium 5-tuple. There is no VectorEnv, no ReplayBuffer, no TensorBoard logger.

---

## Feature: Environment

```gherkin
Feature: Environment 类（CartPole-like）
  Environment 提供类 Gym 的 step/reset API，内置 CartPole-like 动力学模拟。

  Scenario: 4-tuple step 返回值
    Given Environment(obs_dim=4, act_dim=2) 实例
    And env 已 reset
    When 调用 env.step(action=0)（向左推）
    Then SHALL 返回 StepResult 数据类:
      | 字段        | 类型          | 说明               |
      | observation | np.ndarray    | 形状 (4,) 的状态向量 |
      | reward      | float         | 奖励值              |
      | done        | bool          | episode 是否结束     |
      | info        | dict[str,Any] | 附加信息 {"step": n} |

  Scenario: reset 初始化
    Given Environment 实例
    When 调用 env.reset()
    Then SHALL 返回形状 (obs_dim,) 的 np.ndarray
    And _state SHALL 为标准正态分布 * 0.1（小幅随机初始化）
    And _step_count SHALL 重置为 0

  Scenario: CartPole-like 动力学
    Given Environment 的 _state = [position, velocity, angle, angular_velocity]
    When action=0（向左推，force=-1.0）
    Then 动力学 SHALL 使用简化物理模型:
      position += velocity * dt
      velocity += (force + mass * gravity * sin(angle) * 0.5) * dt
      angle += angular_velocity * dt
      angular_velocity += (force * 0.5 - gravity * sin(angle) * 0.5) * dt
    And dt=0.05, gravity=9.8, mass=1.0

  Scenario: 终止条件
    Given Environment 运行中
    When |angle| > 0.5
    Then done SHALL 为 True, reward SHALL 为 -1.0
    When |position| > 2.4
    Then done SHALL 为 True, reward SHALL 为 -1.0
    When step_count >= max_steps (200)
    Then done SHALL 为 True, reward SHALL 为 10.0（存活奖励）
    When 无终止条件触发
    Then done SHALL 为 False, reward SHALL 为 1.0

  Scenario: 未 reset 直接 step
    Given Environment 新创建，未调用 reset
    When 调用 env.step(action)
    Then SHALL 抛出 RuntimeError("Call reset() before step()")

  Scenario: 随机种子控制
    Given Environment(seed=42)
    When reset 并执行相同动作序列
    Then 结果 SHALL 可复现（rng = np.random.default_rng(seed)）
    And 每步状态 SHALL 添加小幅噪声（rng.standard_normal * 0.01）
```

## Feature: PolicyNetwork

```gherkin
Feature: NumPy 策略网络
  PolicyNetwork 是纯 NumPy 实现的 2 层 MLP，输出动作概率分布。

  Scenario: 网络结构
    Given PolicyNetwork(obs_dim=4, act_dim=2, hidden=32, lr=0.001)
    Then 权重 SHALL 为:
      | 参数 | 形状     | 初始化           |
      | w1  | (4, 32) | Xavier + 标准正态 |
      | b1  | (32,)   | zeros            |
      | w2  | (32, 2) | Xavier + 标准正态 |
      | b2  | (2,)    | zeros            |
    And Adam 优化器状态 _m, _v SHALL 为空，_t=0

  Scenario: forward 前向传播
    Given PolicyNetwork 和观测 obs（形状 (4,)）
    When 调用 forward(obs)
    Then 隐藏层 SHALL 使用 ReLU 激活: h = ReLU(obs @ w1 + b1)
    And 输出层 SHALL 使用 Softmax: probs = softmax(h @ w2 + b2)
    And SHALL 返回 (probs, cache) 元组
    And cache SHALL 存储所有中间值用于反向传播

  Scenario: select_action 动作采样
    Given PolicyNetwork
    When 调用 select_action(obs)
    Then SHALL 调用 forward 获取概率分布
    And 使用 rng.choice 按概率分布采样
    And SHALL 返回 (action: int, cache: dict)

  Scenario: compute_loss 策略梯度
    Given 前向传播的 cache, action=1, advantage=0.5
    When 调用 compute_loss(cache, action, advantage)
    Then 损失 SHALL 为 -log(prob[action] + 1e-8) * advantage
    And 梯度 SHALL 通过手动反向传播计算:
      dlogits = probs.copy(); dlogits[action] -= 1.0; dlogits *= advantage
      dw2 = h_act.T @ dlogits
      dh = (dlogits @ w2.T) * (h > 0)
      dw1 = obs.T @ dh
    And SHALL 返回 {"w1": dw1, "b1": db1, "w2": dw2, "b2": db2}

  Scenario: update Adam 优化
    Given PolicyNetwork(lr=0.001)
    When 调用 update({"w1": dw1, "b1": db1, "w2": dw2, "b2": db2})
    Then SHALL 使用 Adam(beta1=0.9, beta2=0.999, eps=1e-8) 更新所有权重
    And 每个参数的 _m 和 _v SHALL 被维护
    And 偏差校正 SHALL 被应用
```

## Feature: RLTrainer

```gherkin
Feature: 同步 RL 训练器
  RLTrainer 组合 Environment + PolicyNetwork + 线性 value baseline，执行策略梯度训练。

  Scenario: 构造函数
    Given TrainingConfig(obs_dim=4, act_dim=2, hidden=32, lr=0.001, seed=42)
    When 创建 RLTrainer(config)
    Then SHALL 创建 Environment(obs_dim=4, act_dim=2, seed=42)
    And SHALL 创建 PolicyNetwork(obs_dim=4, act_dim=2, hidden=32, lr=0.001, seed=42)
    And value_w SHALL 为 np.zeros(obs_dim)
    And rng SHALL 为 np.random.default_rng(seed)

  Scenario: train 训练循环
    Given RLTrainer(config=TrainingConfig(total_steps=200))
    When 调用 train(callback)
    Then SHALL 执行 200 步训练循环
    And 每步 SHALL: select_action -> env.step -> compute advantage -> policy update -> value update
    And SHALL 返回 list[StepMetric]

  Scenario: GAE-like 优势计算
    Given 训练中收集了 rewards, values, dones 列表
    When 调用 _compute_returns(rewards, values, dones)
    Then SHALL 从后向前计算:
      delta[t] = r[t] + gamma * V(t+1) - V(t)
      gae[t] = delta[t] + gamma * lambda * gae[t+1]
    And done=True 时 SHALL 重置 next_value=0, gae=0
    And returns SHALL 为 advantages + values

  Scenario: 线性 value baseline
    Given RLTrainer 的 value_w 向量
    When 调用 _estimate_value(obs)
    Then SHALL 返回 float(obs @ value_w)
    When 调用 _update_value(obs, target)
    Then SHALL 使用 SGD: value_w -= lr * (pred - target) * obs
```

## Feature: NOT IMPLEMENTED (Future Enhancements)

```gherkin
Feature: 以下功能在 rlforge 中未实现
  当前 rlforge 实现为最小化策略梯度框架，以下功能未实现:

  Scenario: Gymnasium 5-tuple API — NOT IMPLEMENTED
    Given Environment.step 返回 StepResult(obs, reward, done, info)
    Then 没有 truncated 字段（不是 5-tuple）
    And 没有 GymWrapper 适配层

  Scenario: VectorEnv 并行环境 — NOT IMPLEMENTED
    Given 当前仅支持单环境顺序执行
    Then 没有 num_envs 配置
    And 没有多进程或异步并行

  Scenario: ReplayBuffer — NOT IMPLEMENTED
    Given 当前为 on-policy 即时更新
    Then 没有经验回放缓冲区
    And rlforge/buffers/ 目录存在但未在训练中使用

  Scenario: TensorBoard Logger — NOT IMPLEMENTED
    Given 没有日志持久化系统
    Then 训练指标仅通过 callback 实时返回
    And rlforge/logging/ 目录存在但无实际实现

  Scenario: PyTorch 支持 — NOT IMPLEMENTED
    Given 所有计算使用 NumPy
    Then 没有 GPU 加速
    And 没有 nn.Module 抽象
    And 没有自动微分（手动反向传播）

  Scenario: Network Protocol 抽象 — NOT IMPLEMENTED
    Given PolicyNetwork 是具体类而非 Protocol
    Then 没有 get_weights/set_weights 接口
    And 没有 MLP 工厂

  Scenario: Checkpoint 保存/恢复 — NOT IMPLEMENTED
    Given RLTrainer 没有 save/load 方法
    Then 训练状态无法持久化
```
