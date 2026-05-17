# Delta Spec: Training Pipeline (rlforge)

> Change: change-20260515-092930-single-agent | Domain: training | Type: ADDED
> Status: Draft

> **NOTE**: This spec describes the ACTUAL training pipeline implemented in
> `agentforge/rlforge/trainer.py` and `agentforge/server/app.py`. There is one
> RLTrainer class (not separate DQN/PPO trainers), using simplified policy gradient
> with NumPy. Training is synchronous and runs in an executor thread.

---

## Feature: RLTrainer Architecture

```gherkin
Feature: 单一 RLTrainer 类
  系统使用单一 RLTrainer 执行策略梯度训练，不是分离的 DQNTrainer/PPOTrainer。

  Scenario: RLTrainer 构造
    Given TrainingConfig 配置
    When 创建 RLTrainer(config)
    Then SHALL 内部创建:
      | 组件            | 类型              | 说明                  |
      | self.env       | Environment       | CartPole-like 环境     |
      | self.policy    | PolicyNetwork     | 2-layer MLP (NumPy)   |
      | self.value_w   | np.ndarray        | 线性 value baseline   |
      | self.rng       | Generator         | NumPy 随机数生成器     |

  Scenario: train 方法签名
    Given RLTrainer 实例
    Then train 方法 SHALL 为:
      def train(self, callback: Callable[[StepMetric], None] | None = None) -> list[StepMetric]
    And SHALL 为同步方法（非 async）
```

## Feature: Training Loop

```gherkin
Feature: 同步训练循环
  RLTrainer.train() 执行同步策略梯度训练循环。

  Scenario: 训练主循环
    Given RLTrainer(config=TrainingConfig(total_steps=200))
    When 调用 train(callback)
    Then SHALL 重置 env 获取初始 obs
    And SHALL 循环 total_steps 步

  Scenario: 单步训练流程
    Given 训练循环的每一步
    When 执行一个 step
    Then 顺序 SHALL 为:
      1. policy.select_action(obs) -> (action, cache)
      2. _estimate_value(obs) -> value
      3. env.step(action) -> StepResult(observation, reward, done, info)
      4. 累积 episode_reward += reward
      5. 计算 advantage = reward + gamma * V(next_obs) - V(obs)
      6. policy.compute_loss(cache, action, advantage) -> grads
      7. 计算 display loss = -log(prob[action]) * advantage
      8. policy.update(grads) — Adam 更新
      9. _update_value(obs, target) — 线性 baseline SGD 更新
      10. 生成 StepMetric 并调用 callback

  Scenario: Episode 结束
    Given env.step 返回 done=True
    When episode 结束
    Then SHALL 清空 episode 累积数据
    And SHALL 重置 env
    And SHALL 重置 episode_reward=0

  Scenario: 训练完成
    Given 循环达到 total_steps
    When train() 返回
    Then SHALL 返回 list[StepMetric]
    And 每个 StepMetric SHALL 包含:
      | 字段            | 类型   |
      | step           | int    |
      | reward         | float  |
      | loss           | float  |
      | episode_reward | float  |
      | value_estimate | float  |
```

## Feature: Integration with FastAPI

```gherkin
Feature: RLTrainingRun 异步集成
  RLTrainingRun 在 FastAPI 中包装 RLTrainer，使用 run_in_executor 运行同步训练。

  Scenario: 启动训练
    Given FastAPI AppState
    When POST /api/rl/start 传入配置
    Then SHALL 创建 RLTrainingRun 实例
    And SHALL 创建 asyncio.Task 执行训练
    And SHALL 返回 {"run_id": ..., "status": "running"}

  Scenario: 算法映射
    Given algo_map = {"PPO": "PPO", "DQN": "REINFORCE", "A2C": "A2C"}
    When 请求 algorithm="DQN"
    Then SHALL 降级映射到 "REINFORCE"
    And 始终使用相同的 RLTrainer（无 DQN 特定逻辑）

  Scenario: 回调收集指标
    Given RLTrainingRun 注册了 on_step 回调
    When 每个 step 完成
    Then 回调 SHALL 收集:
      metrics["reward"].append({"x": step, "y": reward})
      metrics["loss"].append({"x": step, "y": abs(loss)})

  Scenario: 训练完成通知
    Given RLTrainingRun 训练完成
    When train() 返回
    Then status SHALL 变为 "completed"
    And SHALL 广播 {"type": "rl_done", "run_id": ..., "status": "completed"}

  Scenario: 取消训练
    Given RLTrainingRun 正在运行
    When POST /api/rl/{run_id}/cancel
    Then SHALL 取消 asyncio.Task
    And status SHALL 变为 "cancelled"

  Scenario: 查询训练状态
    Given RLTrainingRun 存在
    When GET /api/rl/{run_id}
    Then SHALL 返回:
      | 字段              | 说明                  |
      | task_id          | run_id               |
      | algorithm        | 请求的算法名称         |
      | current_step     | 当前步数              |
      | status           | idle/running/completed/cancelled |
      | metrics          | {reward: [...], loss: [...]} |
      | hyperparameters  | 原始配置              |
```

## Feature: NOT IMPLEMENTED (Future Enhancements)

```gherkin
Feature: 以下训练管线功能未实现
  当前训练管线为最小化实现:

  Scenario: 分离 Trainer 架构 — NOT IMPLEMENTED
    Given 当前只有单一 RLTrainer
    Then 没有 DQNTrainer 和 PPOTrainer 分离
    And 没有 TrainerMixin 共享逻辑

  Scenario: Checkpoint 保存/恢复 — NOT IMPLEMENTED
    Given RLTrainer 没有 save/load 方法
    Then 训练状态无法持久化
    And 无法断点续训

  Scenario: Seed 控制可复现性 — PARTIALLY IMPLEMENTED
    Given Environment 和 PolicyNetwork 使用 seed
    Then 训练初始化 SHALL 可复现
    But 训练中途的随机性（action 采样噪声）未完全控制

  Scenario: 回调系统 — PARTIALLY IMPLEMENTED
    Given 仅有 on_step 回调（通过 train(callback)）
    Then 没有 on_episode_end 回调
    And 没有 on_update_end 回调

  Scenario: VectorEnv 并行训练 — NOT IMPLEMENTED
    Given 当前仅单环境
    Then 没有 num_envs 配置
    And 没有多环境并行采样

  Scenario: 定期评估 — NOT IMPLEMENTED
    Given 当前没有评估阶段
    Then 没有 eval_freq 配置
    And 没有 greedy 策略评估
    And 没有渲染支持
```
