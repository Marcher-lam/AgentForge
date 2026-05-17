# Change Proposal: Reinforcement Learning Engine

> Type: feature | Priority: high | Status: Archived
> Created: 2026-05-15
> Archive Reason: Epic 拆分为 3 个独立 Change

---

## 1. Intent (意图)

实现一个强化学习（RL）训练引擎，提供从环境交互、算法训练到可视化的完整闭环。支持单 Agent（DQN/PPO）和多 Agent（MADDPG）场景，面向研究和原型验证。

**核心价值**：
- 标准化的环境抽象，兼容 Gymnasium 接口
- 经典 RL 算法开箱即用（DQN、PPO）
- 多 Agent RL 协调机制
- 训练过程实时可视化

---

## 2. Scope (范围)

### In Scope (本期实现)

| # | 子系统 | 核心能力 | 技术选型 |
|---|--------|---------|---------|
| 1 | 环境抽象层 | Env 基类、Gymnasium 接口适配、VectorEnv 并行 | Gymnasium API |
| 2 | DQN 算法 | Q-Network、Experience Replay、Target Network、ε-greedy | PyTorch |
| 3 | PPO 算法 | Actor-Critic、GAE、Clipping、Mini-batch 更新 | PyTorch |
| 4 | 多 Agent RL | MADDPG、共享经验池、集中式 Critic | PyTorch |
| 5 | 训练可视化 | TensorBoard 集成、指标记录、曲线绘制 | TensorBoard |

### Out of Scope (不在本期)

- 分布式训练（Ray/RLlib 集成）
- 模型压缩与推理优化
- 自定义环境 DSL
- 超参数自动搜索（Optuna 等）
- ONNX / TensorRT 导出
- 在线学习 / 实时部署

---

## 3. Approach (方案)

### 3.1 架构分层

```
┌───────────────────────────────────────────┐
│          Training Pipeline                 │
│  (Trainer / Callbacks / Checkpoint)       │
├───────────────────────────────────────────┤
│  DQN Agent  │  PPO Agent  │  MADDPG Agent │
│  (算法实现)  │  (算法实现)  │  (算法实现)    │
├───────────────────────────────────────────┤
│        RL Core (共享基础设施)               │
│  Buffer │ Network │ Sampler │ Logger      │
├───────────────────────────────────────────┤
│        Environment Abstraction             │
│  EnvBase │ GymWrapper │ VectorEnv         │
├───────────────────────────────────────────┤
│        TensorBoard Visualization           │
└───────────────────────────────────────────┘
```

### 3.2 分期建议

**Epic 检测**：5 个子系统，跨 RL 算法 + 环境抽象 + 多 Agent + 可视化，建议分 3 期：

- **Phase 1（基础层）**：环境抽象 + RL Core（Buffer/Network/Sampler）+ TensorBoard Logger
- **Phase 2（单 Agent）**：DQN + PPO 算法实现
- **Phase 3（多 Agent）**：MADDPG + 共享经验池 + 集成测试

---

## 4. Success Criteria (验收标准)

### 功能验收

- [ ] Env 基类兼容 Gymnasium API（reset/step/render/close）
- [ ] VectorEnv 支持至少 4 个并行环境
- [ ] DQN 在 CartPole-v1 上达到 score ≥ 475（100 episode 均值）
- [ ] PPO 在 CartPole-v1 上达到 score ≥ 475（100 episode 均值）
- [ ] MADDPG 在简单多 Agent 环境中收敛
- [ ] TensorBoard 实时显示 reward/loss 曲线

### 质量验收

- [ ] 核心模块单元测试覆盖率 ≥ 80%
- [ ] 所有网络层和算法有完整 type hints
- [ ] 算法实现可复现（seed 控制）
- [ ] 训练支持 checkpoint 保存/恢复

---

## 5. Risks & Open Questions (风险与待确认)

### 风险

| # | 风险 | 影响 | 缓解措施 |
|---|------|------|---------|
| 1 | MADDPG 训练不稳定 | 多 Agent 收敛困难 | 提供默认超参 + 调参指南 |
| 2 | PyTorch 版本兼容性 | API 变动导致接口失效 | 支持 PyTorch ≥ 2.0 |
| 3 | 并行环境性能 | VectorEnv GIL 瓶颈 | 使用 multiprocessing 而非 threading |

### 待确认

1. **语言/框架**：Python + PyTorch？是否需要 JAX 支持？
2. **Gymnasium 版本**：基于 Gymnasium 0.29+ 还是 1.0+？
3. **PyTorch 版本**：最低 2.0？还是 2.1+？
4. **设备支持**：仅 CPU？还是必须支持 CUDA GPU？
5. **并行环境数**：VectorEnv 默认并行数？上限？
6. **训练基准**：CartPole 作为基准环境是否可接受？
7. **依赖管理**：poetry / uv / pip？
8. **包名**：`rlforge`？还是其他？

---

## 6. References (参考)

- Gymnasium: https://gymnasium.farama.org/
- PyTorch: https://pytorch.org/
- TensorBoard: https://www.tensorflow.org/tensorboard
- DQN Paper: Mnih et al. 2015 "Human-level control through deep RL"
- PPO Paper: Schulman et al. 2017 "Proximal Policy Optimization Algorithms"
- MADDPG Paper: Lowe et al. 2017 "Multi-Agent Actor-Critic for Mixed Cooperative-Competitive"
