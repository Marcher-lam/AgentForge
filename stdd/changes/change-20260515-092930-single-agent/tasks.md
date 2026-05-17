# Task Breakdown: Single-Agent RL (DQN + PPO)

> Change: change-20260515-092930-single-agent | Priority: P0 | Depends on: change-20260515-092930-foundation

---

## Task 1: Q-Network + Dueling 架构
- [ ] 实现 QNetwork（MLP，可配置隐藏层）
- [ ] 实现 DuelingQNetwork（Value + Advantage 分离）
- [ ] 实现 ε-greedy 策略（线性/指数衰减）
- [ ] 单元测试：前向传播 + 输出形状 + ε 衰减曲线
- **预估**: 30min | **依赖**: change-20260515-092930-foundation Task 1

## Task 2: DQN Trainer
- [ ] 实现 DQNTrainer（继承 TrainerMixin）
- [ ] 实现 Double DQN（online → target action 选择）
- [ ] 实现目标网络更新（hard copy / soft Polyak）
- [ ] 实现 DQNConfig dataclass（所有超参）
- [ ] 单元测试：训练一步 + 目标更新 + gradient flow
- **预估**: 40min | **依赖**: Task 1, change-20260515-092930-foundation Task 4

## Task 3: Actor-Critic + PPO 核心
- [ ] 实现 ActorCritic（共享/分离 backbone）
- [ ] 实现 GAE 优势估计
- [ ] 实现 PPO-Clip loss（clipping ε=0.2）
- [ ] 实现 entropy bonus + value loss
- [ ] 实现离散/连续动作空间支持
- [ ] 单元测试：前向 + loss 计算 + clip 范围
- **预估**: 45min | **依赖**: change-20260515-092930-foundation Task 1

## Task 4: PPO Trainer
- [ ] 实现 PPOTrainer（继承 TrainerMixin）
- [ ] 实现 mini-batch 更新（可配置 epochs，默认 10）
- [ ] 实现 PPOConfig dataclass（所有超参）
- [ ] 实现 rollout 收集 → GAE → mini-batch 更新循环
- [ ] 单元测试：单次更新 + 数据流 + gradient
- **预估**: 35min | **依赖**: Task 3, change-20260515-092930-foundation Task 4

## Task 5: CartPole 收敛验证 + 集成测试
- [ ] DQN CartPole-v1 收敛测试（≤500k steps, mean ≥ 475）
- [ ] PPO CartPole-v1 收敛测试（≤200k steps, mean ≥ 475）
- [ ] 完整 checkpoint 保存/恢复集成测试
- [ ] Callback 触发集成测试
- [ ] 验证测试覆盖率 ≥ 80%
- **预估**: 45min | **依赖**: Task 2, Task 4
