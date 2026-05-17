# Delta Spec: RL Foundation Layer

> Change: change-20260515-092930-foundation | Domain: foundation | Type: ADDED
> Status: Draft

---

## Feature: Environment Abstraction

```gherkin
Feature: EnvBase ABC
  系统 SHALL 提供标准化的环境抽象，兼容 Gymnasium 0.29+ API。

  Scenario: 5-tuple step 返回值
    Given EnvBase 实例
    When 调用 env.step(action)
    Then SHALL 返回 (obs, reward, terminated, truncated, info) 5-tuple

  Scenario: reset 初始化
    When 调用 env.reset()
    Then SHALL 返回初始观测值 obs
    And 环境 SHALL 恢复到初始状态

  Scenario: Gymnasium 兼容
    Given Gymnasium CartPole-v1 环境
    When 通过 GymWrapper 包装
    Then SHALL 暴露与 EnvBase 一致的接口
    And 5-tuple 返回值 SHALL 正确传递
```

```gherkin
Feature: VectorEnv 并行环境
  系统 SHALL 支持多环境并行运行。

  Scenario: 8 个并行环境
    Given VectorEnv 配置 num_envs=8
    When 调用 vector_env.reset()
    Then SHALL 返回 8 个初始观测值
    When 调用 vector_env.step(actions)（8 个动作）
    Then SHALL 返回 8 组 (obs, reward, terminated, truncated, info)

  Scenario: 上限 32 个并行
    Given 配置 num_envs=32
    When 创建 VectorEnv
    Then SHALL 成功创建 32 个并行环境

  Scenario: multiprocessing 无 GIL
    Given 使用 multiprocessing 并行策略
    When 8 个环境同时 step
    Then SHALL 不受 GIL 限制
    And 吞吐量 SHALL 显著高于单环境顺序执行
```

## Feature: Buffers

```gherkin
Feature: ReplayBuffer
  系统 SHALL 提供线程安全的经验回放缓冲区。

  Scenario: push 和 sample
    Given ReplayBuffer 容量 10000
    When push 100 条 transition
    And sample batch_size=64
    Then SHALL 返回 64 条随机 transition

  Scenario: 线程安全
    Given 两个线程同时 push 和 sample
    When 并发操作
    Then SHALL NOT 出现数据竞争或索引错误

  Scenario: 容量溢出
    Given 容量 1000
    When push 第 1001 条
    Then 最早的 transition SHALL 被丢弃
```

```gherkin
Feature: PrioritizedReplayBuffer
  系统 SHALL 支持按 TD-error 优先采样。

  Scenario: 优先采样
    Given buffer 中 transition 的优先级为 [1, 10, 100]
    When sample
    Then 优先级为 100 的 transition SHALL 以最高概率被采样

  Scenario: 优先级更新
    Given 一条 transition 的 TD-error 更新为更大值
    When 更新优先级
    Then 后续采样该条目的概率 SHALL 增大
```

```gherkin
Feature: RolloutBuffer
  系统 SHALL 提供 PPO 用的 RolloutBuffer。

  Scenario: 存储轨迹
    Given RolloutBuffer
    When 存储一条 trajectory 的 obs, action, reward, value, log_prob
    Then SHALL 可按顺序检索

  Scenario: GAE 计算
    Given rollout 数据已存入
    When 计算 GAE(gamma=0.99, lambda=0.95)
    Then SHALL 返回每个时间步的优势估计
```

## Feature: Network Protocol

```gherkin
Feature: 网络抽象层
  系统 SHALL 提供完全抽象的 Network Protocol，隐藏 PyTorch。

  Scenario: Network Protocol 接口
    Given Network Protocol 定义
    Then SHALL 声明 forward, get_weights, set_weights 方法

  Scenario: MLP 实现
    Given MLP 类实现 Network Protocol
    When 创建 MLP(input_dim=4, output_dim=2, hidden=[256,256])
    Then SHALL 可通过 Protocol 接口使用
    And PyTorch 实现细节 SHALL 被隐藏

  Scenario: 设备自动检测
    When 调用 get_device()
    Then SHALL 返回 "cpu", "cuda", 或 "mps" 中可用的最优设备
```

## Feature: TensorBoard Logger

```gherkin
Feature: RLLogger + TensorBoard
  系统 SHALL 提供 RLLogger 接口和 TensorBoard 实现。

  Scenario: 记录 scalar
    When 调用 logger.log_scalar("reward", 10.5, step=100)
    Then TensorBoard SHALL 可查看 reward 曲线

  Scenario: 记录 histogram
    When 调用 logger.log_histogram("weights", array, step=100)
    Then TensorBoard SHALL 可查看权重分布直方图

  Scenario: 可配置采样率
    Given 采样率配置为 every=10
    When 连续 log_scalar 100 次
    Then 仅 10 条 SHALL 实际写入 TensorBoard
```
