# AgentForge — 项目愿景

> 版本: 3.0 | 更新: 2026-05-18
> 方法论: STDD (Spec-Driven Test-Driven Development)

---

## 问题陈述

构建智能 Agent 系统时，开发者面临三大挑战：
1. **Agent 行为不可预测** — 缺乏规范驱动的开发流程，Agent 行为难以验证
2. **训练与进化割裂** — 强化学习和进化计算各自为政，无法协同优化
3. **缺乏可观测性** — Agent 间通信、训练过程、进化状态难以实时监控

AgentForge 要解决的核心问题：**如何用规范驱动的方式，构建可验证、可观测、可进化的多 Agent 智能系统？**

## 产品定位

AgentForge 是一个**多 Agent 智能系统开发框架**，融合三大范式：

```
Agent 框架 (AgentForge)
  + 强化学习引擎 (RLForge)
  + 进化计算引擎 (EvoForge)
  + SKILL.md 技能系统（OpenClaw 兼容）
  = 可进化智能体系统
```

**一句话定位**: Spec-Driven Multi-Agent RL + Evolution Framework with OpenClaw Skill Compatibility

## 目标用户

| 用户 | 场景 | 核心需求 |
|------|------|----------|
| RL 研究员 | 快速实现和验证新算法 | 可扩展的算法框架、可复现的实验 |
| AI 工程师 | 构建生产级 Agent 系统 | 可靠通信、状态管理、技能复用 |
| 进化计算研究者 | 优化策略/超参/网络拓扑 | 灵活的基因组表示、可配置算子 |
| OpenClaw 用户 | 在 AgentForge 中复用已有技能 | SKILL.md 格式兼容，零转换迁移 |

## 技术愿景

### 架构原则

1. **Spec-Driven** — 每个功能先写 BDD 规范，再写测试，最后实现
2. **Protocol-First** — 模块间通过 Protocol 接口解耦，支持多实现
3. **Per-Agent 配置** — 每个 Agent 独立配置 LLM/工具/技能/MCP/进化/RL
4. **SKILL.md 原生** — 技能使用 SKILL.md 标准格式，与 OpenClaw 完全兼容
5. **可观测优先** — 所有 Agent 通信、训练指标、进化状态实时可视化

### 系统架构

```
┌─────────────────────────────────────────────────────┐
│                   Frontend UI                        │
│  Chat │ AgentGrid │ Monitor │ Dashboard │ Settings   │
├─────────────────────────────────────────────────────┤
│                   AgentForge API                     │
│  Agents CRUD │ Tools CRUD │ Skills CRUD │ MCP CRUD  │
│  Skills URL Install │ MCP npm Install │ LLM Profiles│
│  Evolution │ RL │ CoEvolution │ Training History │ WebSocket    │
├─────────────────────────────────────────────────────┤
│                Per-Agent Wiring                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐            │
│  │ Agent A  │ │ Agent B  │ │ Agent C  │            │
│  │ tools:[] │ │ tools:[] │ │ tools:[] │            │
│  │ skills[] │ │ skills[] │ │ skills[] │            │
│  │ LLM: GPT │ │ LLM:本地 │ │ LLM: Claude│          │
│  │ evo: on  │ │ evo: off │ │ evo: on  │            │
│  │ rl: PPO  │ │ rl: DQN  │ │ rl: off  │            │
│  │ coevo:✓  │ │ coevo:✓  │ │ coevo:✗  │            │
│  └──────────┘ └──────────┘ └──────────┘            │
├───────────────────┬─────────────────────────────────┤
│    RLForge        │           EvoForge               │
│  PPO/DQN/REINFORCE│  Selection/Crossover/Mutation   │
│  Replay+Target    │  Fitness/Termination/Callback    │
├───────────────────┴─────────────────────────────────┤
│              CoEvolution (Phase 5)                    │
│  RL training → Reward stats → Enhanced fitness      │
│  60% personality + 40% RL alignment → Pareto front  │
├─────────────────────────────────────────────────────┤
│              Skill System (SKILL.md)                 │
│  OpenClaw compatible │ YAML frontmatter │ 指令注入  │
├─────────────────────────────────────────────────────┤
│              Memory System                           │
│  Short-term (LRU) │ Long-term (SQLite) │ Vector     │
└─────────────────────────────────────────────────────┘
```

### 技术栈

| 层 | 技术 | 选型理由 |
|----|------|----------|
| Agent 核心 | Python 3.12 + asyncio | 异步原生，Protocol 接口 |
| 消息通信 | asyncio + websockets | 进程内零拷贝 + 跨进程 WebSocket |
| 记忆存储 | SQLite + NumPy vectors | 嵌入式、零运维、语义检索 |
| RL 训练 | NumPy | 轻量数值计算，真实 PPO/DQN |
| 进化计算 | NumPy | 轻量遗传算法 |
| 技能系统 | SKILL.md (OpenClaw 兼容) | 标准格式，生态复用 |
| 工具系统 | MCP 协议 + JSON Schema | 标准化工具注册 |
| 前端 | React 19 + Jotai + Tailwind + Recharts | 响应式状态管理 + 数据可视化 |
| 测试 | pytest + vitest | 全栈 TDD |

## 里程碑

### Phase 1: 核心骨架 ✅

- [x] AgentForge 类型系统
- [x] AgentBase 状态机 + 生命周期
- [x] InProcessMessageBus + WebSocketMessageBus
- [x] 基础设施 (structlog, config, shutdown)

### Phase 2: 能力层 ✅

- [x] MCPToolRegistry（JSON Schema 校验）
- [x] SkillRegistry（SKILL.md 原生格式，OpenClaw 兼容）
- [x] 三层记忆系统（短期 + 长期 SQLite + 向量 NumPy）
- [x] MemoryManager 统一门面
- [x] Per-Agent 独立配置（LLM/工具/技能/MCP/进化/RL）

### Phase 3: 算法引擎 ✅

- [x] PPO（ActorCritic + GAE + PPO-Clip + mini-batch）
- [x] DQN（ReplayBuffer + 目标网络 + ε-greedy）
- [x] REINFORCE（策略梯度 + 价值基线）
- [x] 遗传算法（选择/交叉/变异/替换/终止）
- [x] 智能体人格优化模式（10维 sigmoid 基因）
- [x] 进化树 SVG 可视化 + 热力图

### Phase 4: 可视化 & UX ✅

- [x] 仪表盘 V2：Agent 卡片网格 → 点击弹出训练记录（进化/RL 双 Tab）
- [x] 训练记录左右分栏：左侧可滚动日志表格 + 右侧 Recharts 图表
- [x] 每个图表放大按钮 + ZoomOverlay 全屏查看
- [x] LTTB 大数据集降采样（>2000 点自动降采样）
- [x] 卡片式智能体管理（创建时一步配齐 LLM/技能/MCP/进化/RL + 渐变头像）
- [x] 监控面板（统计条/类型筛选/自动滚动）
- [x] 设置页：多 Provider LLM 卡片（启动自动创建默认卡片）+ MCP 服务（手动+在线 npm 安装）+ 技能管理（在线 URL+路径+文本安装）
- [x] Per-Agent 训练历史 API（GET /agents/{id}/evolution/runs + GET /agents/{id}/rl/runs）
- [x] 聊天管理：删除对话记录 + 群聊（单聊/群聊切换 + 多 Agent 三阶段讨论）+ 导出聊天记录（JSON 下载）
- [x] 记忆系统闭环：三层记忆（短期LRU+长期SQLite+向量）接入聊天，Agent 回复前检索相关记忆注入 prompt
- [x] 进化结果写回：进化完成后最优基因组映射为 10 维人格特质，自动修改 Agent system_prompt
- [x] RL DQN 修复：algo_map 映射正确，训练后自动保存 checkpoint
- [x] RL 结果写回：训练完成自动提取策略信号写回 system_prompt + LLM 参数（temperature/max_tokens/风格描述）
- [x] 技术债修复：WebSocket subscribe KeyError、VectorMemory 真实语义 embedding、asyncio/anyio 统一
- [x] 预设 AI 专家团队：启动自动创建 9 个角色（程序员/哲学家/数学家/ML工程师/DL工程师/RL工程师/C++工程师/推理工程师/前端工程师）+ 群聊会话
- [x] Agentic RAG：Per-Agent ChromaDB 知识库 + fastembed 语义 embedding + 联网搜索 + LLM 自主决策检索策略

### Phase 5: 协同进化 ✅

- [x] CoEvolutionRun: RL 训练 → 奖励统计注入进化适应度 → 多目标进化
- [x] RL 增强适应度函数（60% 人格质量 + 40% RL 对齐）
- [x] Pareto 前沿排名（Top 5 个体）
- [x] 流式输出（WebSocket chunk 协议 + typing 指示器）
- [x] 消息持久化（SQLite write-through + 重启自动恢复）
- [x] 工具执行闭环（ReAct 循环 + MCP/Skill 工具调用）

### Phase 6: 生产就绪 (待开发)

- [ ] 分布式训练
- [ ] 端到端加密通信
- [ ] CI/CD 流水线

## 成功指标

| 维度 | 指标 | 当前状态 |
|------|------|----------|
| 后端导入 | 全模块零错误 | ✅ 通过 |
| 前端编译 | TypeScript 零错误 | ✅ 通过 |
| 前端测试 | 47 tests | ✅ 全部通过 |
| API 端点 | 55 个路由 | ✅ 全部注册 |
| 协同进化 | RL→Evo 两阶段 + Pareto 前沿 | ✅ 端到端验证通过 |
| 流式输出 | chunk + typing + auto-scroll | ✅ 9 chunks 验证通过 |
| 消息持久化 | SQLite 三表 + 重启恢复 | ✅ 验证通过 |
| 工具执行 | ReAct loop + tool_call 事件 | ✅ 验证通过 |
| OpenClaw 兼容 | SKILL.md 读写 + 门控 | ✅ 通过 |
| 技能互操作 | 双向零转换 | ✅ 验证通过 |
| 在线安装 | Skill URL + MCP npm | ✅ 验证通过 |
| 仪表盘 | Agent 卡片 + 训练记录分栏 | ✅ 验证通过 |
| 记忆闭环 | 三层记忆读写接入聊天 | ✅ 验证通过 |
| 进化写回 | 最优基因组映射人格特质到 prompt | ✅ 验证通过 |
| RL 修复 | DQN 映射正确 + checkpoint 保存 | ✅ 验证通过 |
| RL 写回 | 训练结果提取策略信号写回 Agent | ✅ 验证通过 |
| Agentic RAG | ChromaDB + fastembed + 联网搜索 | ✅ 语义检索验证通过 |
| 技术债修复 | WebSocket/VectorMemory/anyio | ✅ 已修复 |

## 约束与边界

### IN（项目范围内）

- 单机多 Agent 系统
- Python 3.12+ 后端
- React 前端
- SKILL.md / OpenClaw 技能格式
- STDD 开发方法论

### OUT（不在范围内）

- 移动端 App
- 分布式训练框架
- 自研大语言模型
- 商业 SaaS 平台

## 愿景声明

> AgentForge 致力于成为**最灵活的多 Agent 智能系统开发框架**。
> 每个 Agent 独立配置，技能与 OpenClaw 生态互通，进化与 RL 协同优化。
> Spec-Driven, Per-Agent Configurable, Ecosystem Compatible.
