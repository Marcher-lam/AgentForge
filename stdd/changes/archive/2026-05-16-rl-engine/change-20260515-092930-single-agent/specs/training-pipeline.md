# Delta Spec: Training Pipeline

> Change: change-20260515-092930-single-agent | Domain: training | Type: ADDED
> Status: Draft

---

## Feature: Trainer Architecture

```gherkin
Feature: 独立 Trainer 类
  DQN 和 PPO SHALL 各自拥有独立 Trainer，共享 TrainerMixin。

  Scenario: DQNTrainer 接口
    Given DQNTrainer 实例
    Then SHALL 暴露以下方法:
      | method       | signature                    |
      | train        | async (env, config) -> dict  |
      | evaluate     | async (env, n_episodes) -> float |
      | save         | (path: str) -> None          |
      | load         | (path: str) -> None          |

  Scenario: PPOTrainer 接口
    Given PPOTrainer 实例
    Then SHALL 暴露与 DQNTrainer 相同的方法签名

  Scenario: TrainerMixin 共享逻辑
    Given TrainerMixin 包含共享逻辑
    Then 以下功能 SHALL 被 DQNTrainer 和 PPOTrainer 共享:
      | 功能          | 描述                  |
      | seed_control  | 设置随机种子确保可复现  |
      | logging       | TensorBoard + 控制台日志 |
      | checkpoint    | 保存/恢复完整状态       |
      | evaluation    | 定期评估 + 可选渲染     |
```

## Feature: Checkpoint

```gherkin
Feature: 完整 Checkpoint 保存/恢复
  训练 SHALL 支持完整状态的保存和恢复。

  Scenario: 保存完整 checkpoint
    Given 训练进行到第 50000 步
    When 调用 trainer.save("ckpt.pt")
    Then 文件 SHALL 包含:
      | 内容              |
      | 模型权重           |
      | optimizer 状态     |
      | buffer 数据        |
      | 训练计数器 (steps/episodes) |
      | 随机数生成器状态    |

  Scenario: 恢复训练
    Given checkpoint 文件 "ckpt.pt"
    When 调用 trainer.load("ckpt.pt")
    Then 训练 SHALL 从保存时的精确状态继续
    And 后续训练结果 SHALL 与不中断训练一致
```

## Feature: Seed Control

```gherkin
Feature: 随机种子控制
  训练 SHALL 支持种子控制确保可复现。

  Scenario: 相同种子相同结果
    Given seed=42
    When 运行 DQN 训练 10000 步
    And 用相同 seed=42 再次运行
    Then 两轮的 reward 曲线 SHALL 完全一致

  Scenario: 不同种子不同结果
    Given seed=42 和 seed=123
    When 分别运行训练
    Then 两轮的 reward 曲线 SHALL 不同
```

## Feature: Callbacks

```gherkin
Feature: 训练回调系统
  训练过程 SHALL 支持回调注入。

  Scenario: on_step_end 回调
    Given 注册了 on_step_end 回调
    When 每步训练完成
    Then 回调 SHALL 被调用
    And 参数 SHALL 包含 step, reward, loss, epsilon(或 policy_entropy)

  Scenario: on_episode_end 回调
    Given 注册了 on_episode_end 回调
    When 一个 episode 结束
    Then 回调 SHALL 被调用
    And 参数 SHALL 包含 episode, total_reward, episode_length

  Scenario: on_update_end 回调
    Given 注册了 on_update_end 回调
    When 一次网络参数更新完成
    Then 回调 SHALL 被调用
    And 参数 SHALL 包含 update, loss_dict
```

## Feature: Evaluation

```gherkin
Feature: 定期评估 + 可选渲染
  训练 SHALL 定期评估并可选渲染。

  Scenario: 定期评估
    Given eval_freq=10（每 10 episode）
    When 第 10, 20, 30... 个 episode 结束
    Then SHALL 运行评估 episode
    And 评估结果 SHALL 记录到 TensorBoard

  Scenario: 可选渲染
    Given render=True
    When 评估 episode 运行
    Then SHALL 调用 env.render() 显示画面

  Scenario: 评估不影响训练
    Given 评估期间使用 greedy 策略（无探索噪声）
    When 评估完成
    Then 训练 SHALL 继续正常进行
    And 评估结果 SHALL NOT 影响训练 buffer
```

## Feature: Parallel Training

```gherkin
Feature: VectorEnv 并行训练加速
  训练 SHALL 支持 VectorEnv 多环境并行加速。

  Scenario: PPO 使用 VectorEnv
    Given PPOConfig 配置 num_envs=8
    When 训练开始
    Then SHALL 创建 8 个并行环境
    And 每个 step SHALL 同时收集 8 条 transition
    And 总采样步数 SHALL 按 num_envs 倍速增长

  Scenario: DQN 使用 VectorEnv
    Given DQNConfig 配置 num_envs=4
    When 训练开始
    Then SHALL 创建 4 个并行环境
    And ReplayBuffer SHALL 接收来自所有环境的 transition

  Scenario: 单环境兼容
    Given num_envs=1（默认）
    When 训练开始
    Then SHALL 使用单个环境顺序执行
    And 行为 SHALL 与不使用 VectorEnv 完全一致
```
