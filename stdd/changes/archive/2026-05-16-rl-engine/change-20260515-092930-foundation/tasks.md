# Task Breakdown: RL Foundation Layer

> Change: change-20260515-092930-foundation | Priority: P0 | Depends on: none

---

## Task 1: Core Types + Network Protocol 抽象
- [x] 定义 RLConfig 基类、ActionType/ObservationType 类型别名
- [ ] 定义 Network Protocol（forward/output/trainable——隐藏 PyTorch）
- [ ] 定义 Transition/Episode/BatchResult dataclass
- [ ] 定义 RLError 异常层次
- [ ] 导出 `rlforge.types.__all__`
- **预估**: 25min | **依赖**: 无

## Task 2: EnvBase + VectorEnv
- [ ] 实现 EnvBase ABC（reset/step/close，5-tuple Gymnasium API）
- [ ] 实现 VectorEnv（multiprocessing，默认 8 并行，最大 32）
- [ ] 实现 SpaceWrapper（Gymnasium → 内部类型适配）
- [ ] 实现 seed 管理（可复现）
- [ ] 单元测试：reset/step + 5-tuple 返回 + seed 可复现
- **预估**: 40min | **依赖**: Task 1

## Task 3: 线程安全 Buffer
- [ ] 实现 ReplayBuffer（均匀采样）
- [ ] 实现 PrioritizedReplayBuffer（sum-tree，α/β 可配置）
- [ ] 实现 RolloutBuffer（GAE 计算）
- [ ] 实现 Buffer 线程安全（Lock 保护）
- [ ] 单元测试：容量/溢出 + 采样分布 + 优先级更新 + GAE 计算
- **预估**: 45min | **依赖**: Task 1

## Task 4: Trainer 基础设施
- [ ] 实现 TrainerMixin（seed 设置 + 设备管理 + checkpoint 序列化）
- [ ] 实现 Callback 系统（on_step_end / on_episode_end / on_update_end）
- [ ] 实现完整 checkpoint（weights + optimizer + buffer + counters + RNG）
- [ ] 实现周期性评估（可选 render）
- [ ] 单元测试：callback 触发 + checkpoint 保存/加载 + seed 可复现
- **预估**: 40min | **依赖**: Task 2, Task 3

## Task 5: TensorBoard 日志集成
- [ ] 实现 RLLogger（TensorBoard writer 封装）
- [ ] 实现标量/直方图/文本日志
- [ ] 实现 episode 统计（奖励/长度/成功率）
- [ ] 实现 log_dir 配置（默认 ./runs/{timestamp}）
- [ ] 单元测试：日志写入 + 目录结构
- **预估**: 25min | **依赖**: Task 1

## Task 6: 集成测试 + 覆盖率验证
- [ ] EnvBase + Buffer + Trainer 完整链路集成测试
- [ ] VectorEnv 多进程并行采集测试
- [ ] Checkpoint 保存/恢复正确性测试
- [ ] 验证测试覆盖率 ≥ 85%
- **预估**: 30min | **依赖**: Task 4, Task 5
