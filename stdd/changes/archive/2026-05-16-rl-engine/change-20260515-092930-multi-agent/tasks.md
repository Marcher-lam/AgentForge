# Task Breakdown: Multi-Agent RL (MADDPG)

> Change: change-20260515-092930-multi-agent | Priority: P1 | Depends on: change-20260515-092930-foundation

---

## Task 1: MultiAgentEnv 接口 + 适配器
- [ ] 实现 MultiAgentEnv ABC（n_agents, observation_spaces, action_spaces）
- [ ] 实现 step/reset 多智能体返回（obs_dict, reward_dict, done_dict, info_dict）
- [ ] 实现 GridWorld 简单多智能体环境（测试用）
- [ ] 实现 PettingZoo 适配器（parallel API → MultiAgentEnv）
- [ ] 单元测试：reset/step + 观测/动作空间 + 多智能体返回格式
- **预估**: 35min | **依赖**: change-20260515-092930-foundation Task 2

## Task 2: MADDPG 网络架构
- [ ] 实现 MADDPGActor（局部 obs → action，无参数共享）
- [ ] 实现 MADDPGCritic（全局 obs + 全局 action → Q-value）
- [ ] 实现 SoftUpdate 目标网络（Polyak 平均）
- [ ] 实现 Ornstein-Uhlenbeck 噪声（连续动作探索）
- [ ] 单元测试：前向传播 + 输出形状 + 软更新
- **预估**: 35min | **依赖**: change-20260515-092930-foundation Task 1

## Task 3: Shared Replay Buffer
- [ ] 实现 MultiAgentReplayBuffer（存储 multi-agent transitions）
- [ ] 实现采样策略（uniform / priority / agent-aware）
- [ ] 实现线程安全 + 容量溢出
- [ ] 单元测试：存储/采样 + 采样策略 + 线程安全
- **预估**: 30min | **依赖**: Task 1

## Task 4: MADDPGTrainer
- [ ] 实现 MADDPGTrainer（多 Actor + 多 Critic 协调）
- [ ] 实现 centralized training / distributed execution 流程
- [ ] 实现 MADDPGConfig dataclass（所有超参）
- [ ] 实现 target policy smooth regularization
- [ ] 单元测试：训练一步 + gradient flow + loss 计算
- **预估**: 40min | **依赖**: Task 2, Task 3, change-20260515-092930-foundation Task 4

## Task 5: 集成测试 + 覆盖率验证
- [ ] GridWorld 多智能体训练集成测试（收敛验证）
- [ ] 完整 checkpoint 保存/恢复测试
- [ ] Callback 触发 + 日志记录测试
- [ ] 验证测试覆盖率 ≥ 80%
- **预估**: 35min | **依赖**: Task 4
