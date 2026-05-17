# Delta Spec: Multi-Agent RL (MADDPG)

> Change: change-20260515-092930-multi-agent | Domain: multi_agent | Type: ADDED
> Status: Draft

---

## Feature: MultiAgentEnv

```gherkin
Feature: 多 Agent 环境抽象
  系统 SHALL 提供 MultiAgentEnv ABC。

  Scenario: reset 返回 per-agent obs
    Given 3 个 Agent 环境
    When 调用 env.reset()
    Then SHALL 返回 {"agent_0": obs0, "agent_1": obs1, "agent_2": obs2}

  Scenario: step 返回 per-agent 数据
    When 调用 env.step({"agent_0": a0, "agent_1": a1, "agent_2": a2})
    Then SHALL 返回 5-tuple:
      | 返回值             | 格式                   |
      | per-agent obs      | dict[str, ObsType]     |
      | per-agent reward   | dict[str, float]       |
      | per-agent terminated| dict[str, bool]       |
      | per-agent truncated| dict[str, bool]        |
      | shared info        | dict[str, dict]        |
```

```gherkin
Feature: 自建 GridWorld 环境
  系统 SHALL 提供自建的 GridWorld 测试环境。

  Scenario: 协作模式
    Given GridWorld 协作模式
    Then 所有 Agent SHALL 共享目标
    And 全部到达目标点时 episode 结束

  Scenario: 竞争模式
    Given GridWorld 竞争模式
    Then Agent 组间 SHALL 对抗
    And 胜负条件 SHALL 明确定义
```

```gherkin
Feature: PettingZoo 兼容
  系统 SHALL 提供 PettingZoo Wrapper。

  Scenario: 包装 PettingZoo 环境
    Given 一个 PettingZoo ParallelEnv
    When 通过 PettingZooWrapper 包装
    Then SHALL 暴露 MultiAgentEnv 接口
    And reset/step SHALL 正确转换数据格式
```

## Feature: MADDPG Architecture

```gherkin
Feature: 集中式 Critic
  Critic SHALL 接收全局观测和全局动作。

  Scenario: Critic 输入
    Given 3 个 Agent，每个 obs 维度 4，action 维度 2
    When Critic 前向传播
    Then 输入 SHALL 为 [obs0, obs1, obs2, act0, act1, act2]（全局 obs+action）
    And 输出 SHALL 为 Q(s_global, a_global)
```

```gherkin
Feature: 分布式 Actor
  Actor SHALL 仅接收局部观测。

  Scenario: Actor 输入
    Given Agent-0 的 obs 维度 4
    When Actor 前向传播
    Then 输入 SHALL 仅为 Agent-0 的 obs（局部观测）
    And 输出 SHALL 为 Agent-0 的 action
```

```gherkin
Feature: 可配置噪声策略
  系统 SHALL 支持 Gaussian 和 OU Noise。

  Scenario: Gaussian 噪声（默认）
    Given noise_type="gaussian", sigma=0.2
    When 添加噪声到 action
    Then SHALL 添加 N(0, 0.2) 噪声

  Scenario: OU 噪声
    Given noise_type="ou"
    When 添加噪声
    Then SHALL 使用 Ornstein-Uhlenbeck 过程生成时间相关噪声
```

## Feature: Shared Replay Buffer

```gherkin
Feature: 共享经验池
  多 Agent 经验 SHALL 可聚合到共享 buffer。

  Scenario: 全局共享（默认）
    Given shared_buffer=True
    When 3 个 Agent 各存 10 条经验
    Then buffer SHALL 包含 30 条经验
    And 采样时 SHALL 不区分来源 Agent

  Scenario: 按 Agent 分组
    Given shared_buffer=False
    When 3 个 Agent 各存经验
    Then 每个 Agent SHALL 有独立 sub-buffer
    And 采样时 SHALL 可按 Agent 过滤

  Scenario: 可配置采样策略
    Given sampler_type="uniform"
    When 采样 batch_size=256
    Then SHALL 均匀随机采样
    Given sampler_type="priority"
    Then SHALL 按 TD-error 优先采样
    Given sampler_type="agent_aware"
    Then SHALL 保证每个 Agent 被均衡采样
```

## Feature: MADDPG Training

```gherkin
Feature: MADDPG 训练收敛
  MADDPG SHALL 在多 Agent 环境中训练收敛。

  Scenario: 协作环境收敛
    Given MADDPGConfig 默认超参数
    When 在 GridWorld 协作环境训练
    Then 全局 reward 曲线 SHALL 呈上升趋势

  Scenario: 竞争环境收敛
    When 在 GridWorld 竞争环境训练
    Then 各组 reward 曲线 SHALL 呈差异化趋势

  Scenario: per-Agent 日志
    Given 3 个 Agent 训练中
    When 查看日志
    Then SHALL 有 per-Agent 的 reward/loss 曲线
    And SHALL 有全局聚合指标
```
