# EvoRL: Evolutionary Reinforcement Learning Agent Framework

> **Specification & Task Document** | Version 1.0 | 2026-05-14
>
> 本文档用于验证 STDD Copilot 全部 `/stdd:` 斜杠命令的可用性。
> **请在 Claude Code 中按顺序逐行执行以下命令。**
> CLI 命令与斜杠命令一一对应，均可使用。

---

## 项目概述

EvoRL 是一个 **进化强化学习多 Agent 协作框架**。前端展示用户与多个 Agent 的交互，支持一对一/一对多通信，Agent 之间可相互通信。每个 Agent 拥有独立的 MCP (Model Context Protocol) 能力、Skill 库、长期记忆，并能通过遗传算法进行进化。

### 技术栈预设
- **前端**: React + TypeScript + Vite
- **后端**: Node.js + Express + WebSocket
- **AI**: OpenAI API / Claude API (可插拔)
- **数据库**: SQLite (记忆存储) + Redis (消息队列)
- **测试**: Vitest + Playwright

---

## Phase 1: 初始化工作区

```
/stdd:init
```

---

## Phase 2: 需求提案 → 澄清 → 确认

### 变更 1: 核心 Agent 引擎

```
/stdd:new 实现一个多Agent协作框架的核心引擎，包括：
1. Agent基类和生命周期管理(init/run/stop/destroy)
2. Agent通信总线(WebSocket pub/sub)
3. MCP协议适配层(工具注册/调用/结果解析)
4. Skill系统(skill注册/发现/执行/依赖解析)
5. 记忆系统(短期记忆/长期记忆/向量检索)
```

```
/stdd:propose
```

```
/stdd:clarify
```

```
/stdd:confirm
```

### 变更 2: 遗传进化引擎

```
/stdd:new 实现Agent遗传进化引擎，包括：
1. 基因组编码(Agent参数序列化)
2. 适应度函数框架(自定义评估指标)
3. 选择算子(轮盘赌/锦标赛/精英)
4. 交叉算子(单点/多点/均匀)
5. 变异算子(高斯/均匀/位翻转)
6. 进化循环(世代交替/种群管理)
```

```
/stdd:propose
/stdd:clarify
/stdd:confirm
```

### 变更 3: 强化学习引擎

```
/stdd:new 实现强化学习引擎，包括：
1. 环境抽象层(Env基类/gym接口)
2. DQN算法(网络/经验回放/目标网络)
3. PPO算法(Actor-Critic/GAE/Clipping)
4. 多Agent RL协调(MADDPG/共享经验池)
5. RL训练可视化(TensorBoard集成)
```

```
/stdd:propose
/stdd:clarify
/stdd:confirm
```

### 变更 4: 前端交互界面

```
/stdd:new 实现前端交互界面，包括：
1. Agent对话面板(消息列表/输入框/发送)
2. 多Agent网格视图(拖拽布局/分屏)
3. 一对一会话模式(用户→Agent私聊)
4. 群组会话模式(一对多广播/多播)
5. Agent间通信监视器(消息可视化)
6. 进化仪表板(世代/适应度/基因树)
7. RL训练监控面板(episode/奖励曲线)
```

```
/stdd:propose
/stdd:clarify
/stdd:confirm
```

---

## Phase 3: 生成 BDD 规格

```
/stdd:spec
/stdd:spec agent-core
/stdd:spec evolution-engine
/stdd:spec rl-engine
/stdd:spec frontend-ui
```

---

## Phase 4: 任务拆解与技术设计

```
/stdd:plan
/stdd:plan agent-core
/stdd:plan evolution-engine
/stdd:plan rl-engine
/stdd:plan frontend-ui
```

---

## Phase 5: API 规范生成

```
/stdd:api-spec 为 agent-core 生成 OpenAPI 规范，包含 Agent 生命周期管理和通信总线接口
/stdd:api-spec 为 evolution-engine 生成 OpenAPI 规范，包含进化循环和种群管理接口
/stdd:api-spec 为 rl-engine 生成 OpenAPI 规范，包含环境注册和训练任务接口
/stdd:api-spec 为 frontend-ui 生成后端 API 规范，包含会话管理和消息推送接口
```

---

## Phase 6: 技术设计文档

```
/stdd:design
/stdd:design agent-core
/stdd:design evolution-engine
/stdd:design rl-engine
/stdd:design frontend-ui
```

---

## Phase 7: TDD 实现循环 (Red → Green → Refactor)

### agent-core

```
/stdd:apply 为 agent-core 的 TASK-001 编写失败测试：Agent 基类初始化、启动、停止、销毁生命周期
/stdd:apply 实现 agent-core TASK-001：Agent 基类，让测试通过
/stdd:apply 重构 agent-core 的 Agent 基类，保持测试通过
/stdd:apply 实现 agent-core TASK-002：Agent 通信总线(WebSocket pub/sub)
/stdd:apply 实现 agent-core TASK-003：MCP 协议适配层
/stdd:apply 实现 agent-core TASK-004：Skill 系统
/stdd:apply 实现 agent-core TASK-005：记忆系统
```

### evolution-engine

```
/stdd:apply 实现 evolution-engine TASK-001：基因组编码
/stdd:apply 实现 evolution-engine TASK-002：适应度函数框架
/stdd:apply 实现 evolution-engine TASK-003：选择算子(轮盘赌/锦标赛/精英)
/stdd:apply 实现 evolution-engine TASK-004：交叉算子(单点/多点/均匀)
/stdd:apply 实现 evolution-engine TASK-005：变异算子(高斯/均匀/位翻转)
/stdd:apply 实现 evolution-engine TASK-006：进化循环(世代交替/种群管理)
```

### rl-engine

```
/stdd:apply 实现 rl-engine TASK-001：环境抽象层
/stdd:apply 实现 rl-engine TASK-002：DQN 算法
/stdd:apply 实现 rl-engine TASK-003：PPO 算法
/stdd:apply 实现 rl-engine TASK-004：多 Agent RL 协调(MADDPG/共享经验池)
/stdd:apply 实现 rl-engine TASK-005：RL 训练可视化(TensorBoard集成)
```

### frontend-ui

```
/stdd:apply 实现 frontend-ui TASK-001：Agent 对话面板
/stdd:apply 实现 frontend-ui TASK-002：多 Agent 网格视图
/stdd:apply 实现 frontend-ui TASK-003：一对一会话模式
/stdd:apply 实现 frontend-ui TASK-004：群组会话模式
/stdd:apply 实现 frontend-ui TASK-005：Agent 间通信监视器
/stdd:apply 实现 frontend-ui TASK-006：进化仪表板
/stdd:apply 实现 frontend-ui TASK-007：RL 训练监控面板
```

---

## Phase 8: Ralph Loop 自动执行

```
/stdd:execute
/stdd:execute agent-core
/stdd:execute evolution-engine
/stdd:execute rl-engine
/stdd:execute frontend-ui
```

---

## Phase 9: 变异测试

```
/stdd:mutation agent-core
/stdd:mutation agent-core --mode stryker
/stdd:mutation evolution-engine
/stdd:mutation rl-engine
/stdd:mutation frontend-ui
```

---

## Phase 10: 验证

```
/stdd:verify agent-core
/stdd:verify evolution-engine
/stdd:verify rl-engine
/stdd:verify frontend-ui
```

---

## Phase 11: 质量门禁

```
/stdd:guard
/stdd:guard --strict
```

---

## Phase 12: Constitution 合规管理

```
/stdd:constitution
/stdd:constitution show 2
/stdd:constitution show 7
/stdd:constitution check
/stdd:constitution status
/stdd:constitution fix
/stdd:constitution audit --json
/stdd:constitution waive 2 --reason "Legacy migration" --days 7
```

---

## Phase 13: Hook 管理

```
/stdd:hooks install
/stdd:hooks verify
/stdd:hooks status
/stdd:hooks disable
/stdd:hooks enable
```

---

## Phase 14: Graph 引擎

```
/stdd:graph visualize
/stdd:graph analyze
/stdd:graph parallel
/stdd:graph replay
/stdd:graph run feature
/stdd:graph run --intent repair --change-name agent-core
/stdd:graph history
/stdd:graph recommend
```

---

## Phase 15: 工作区管理

```
/stdd:workspace list
/stdd:workspace validate
/stdd:workspace repair
/stdd:workspace list --json
```

---

## Phase 16: 状态检查

```
/stdd:status
/stdd:status agent-core
/stdd:status --json
/stdd:list
/stdd:list --archived
/stdd:list --specs
/stdd:list --json
/stdd:skills
/stdd:skills --phase 4
/stdd:commands
```

---

## Phase 17: Schema 管理

```
/stdd:schema 为 EvoRL 项目创建 JSON Schema 类型定义，包含 AgentConfig、Genome、Environment 等核心类型
/stdd:schema 为 Agent 通信消息创建类型定义(Action/Response/Broadcast)
/stdd:schema validate schemas/spec-driven/schema.yaml
/stdd:schema create evorl-workflow
/stdd:schema fork schemas/spec-driven/schema.yaml evorl-custom
```

---

## Phase 18: 契约测试

```
/stdd:contract generate agent-core
/stdd:contract verify agent-core
/stdd:contract generate frontend-ui
/stdd:contract verify frontend-ui
```

---

## Phase 19: Mock 与 Factory

```
/stdd:mock agent-core
/stdd:mock rl-engine
/stdd:factory agent-core
/stdd:factory evolution-engine
```

---

## Phase 20: 规范验证 (Spec Guardian)

```
/stdd:validate agent-core
/stdd:validate agent-core --spec-guardian --fix
/stdd:validate evolution-engine
/stdd:validate rl-engine
/stdd:validate frontend-ui
```

---

## Phase 21: 外向内 TDD

```
/stdd:outside-in init
/stdd:outside-in scaffold agent-core
/stdd:outside-in scaffold frontend-ui
/stdd:outside-in status
```

---

## Phase 22: 高级工作流

```
/stdd:ff 实现 Agent 记忆持久化与向量检索，支持长期记忆压缩
/stdd:issue Agent 通信时偶发消息丢失，需要添加可靠投递机制
/stdd:turbo 添加 OAuth2 认证支持到 frontend-ui
/stdd:continue agent-core
/stdd:explore agent-core
```

---

## Phase 23: 头脑风暴与评估

```
/stdd:brainstorm 如何优化多 Agent 通信延迟
/stdd:brainstorm --method first-principles "RL 奖励函数设计的最佳实践"
/stdd:certainty 评估 agent-core 当前实现的置信度
/stdd:complexity 评估 agent-core 的代码复杂度(APP Mass)
```

---

## Phase 24: 项目愿景与文档

```
/stdd:vision 为 EvoRL 项目创建愿景文档
/stdd:final-doc agent-core
/stdd:final-doc evolution-engine
/stdd:final-doc rl-engine
/stdd:final-doc frontend-ui
```

---

## Phase 25: 结构化规划与协调

```
/stdd:prp 为 evolution-engine 的下一代版本做结构化规划
/stdd:supervisor 协调 agent-core、evolution-engine、rl-engine 三个模块的开发进度
/stdd:context
/stdd:context --export
/stdd:context --json
```

---

## Phase 26: 协作角色

```
/stdd:roles list
/stdd:roles 组织 PO、Architect、Developer、Tester 评审 agent-core 设计
/stdd:roles party --roles po,arch,dev,qa
```

---

## Phase 27: 学习与记忆

```
/stdd:learn status
/stdd:learn patterns --json
/stdd:learn 分析项目中 agent-core 的代码模式并记录
/stdd:memory scan
/stdd:memory list
/stdd:memory 将 agent-core 的架构决策存入向量数据库
```

---

## Phase 28: 并行与迭代

```
/stdd:parallel 并行执行 agent-core 和 evolution-engine 的验证
/stdd:iterate agent-core
```

---

## Phase 29: 质量指标

```
/stdd:metrics
/stdd:metrics agent-core --json
/stdd:metrics evolution-engine --json
/stdd:metrics rl-engine --json
/stdd:metrics frontend-ui --json
```

---

## Phase 30: 测试辅助

```
/stdd:user-test frontend-ui
/stdd:story create evorl-journey --persona "AI Researcher"
/stdd:story bdd stdd/journeys/evorl-journey.yaml
/stdd:pipeline agent-core
/stdd:pipeline frontend-ui
```

---

## Phase 31: CI 与 Starter

```
/stdd:ci github
/stdd:starters list
/stdd:starters create evorl-app --type typescript
```

---

## Phase 32: 扩展管理

```
/stdd:extensions list
/stdd:extensions validate
/stdd:extensions install ./my-extension
```

---

## Phase 33: 依赖检查

```
/stdd:depcheck
/stdd:depcheck --json
```

---

## Phase 34: 诊断与修复

```
/stdd:doctor
/stdd:fix-packet agent-core --test-command "npx vitest run"
/stdd:fix-packet evolution-engine
/stdd:tdd-init
/stdd:tdd-init --dry-run
```

---

## Phase 35: 推荐与更新

```
/stdd:recommend
/stdd:recommend --json
/stdd:update --dry-run
/stdd:audit --json
```

---

## Phase 36: Baby Steps TDD

```
/stdd:baby-steps
/stdd:baby-steps "实现 Agent 通信总线的重连机制"
```

---

## Phase 37: Runtime 引擎

```
/stdd:runtime agent start "EvoRL 架构设计评审" --rounds 3
/stdd:runtime agent next
/stdd:runtime agent stop
/stdd:runtime agent run "审查 agent-core 的安全设计" --role architect
/stdd:runtime sudo evorl.sudo --generate
/stdd:runtime sudo evorl.sudo
```

---

## Phase 38: 浏览器驱动

```
/stdd:browser doctor
/stdd:browser inspect https://localhost:5173
/stdd:browser snapshot https://localhost:5173 --width 1920 --height 1080
```

---

## Phase 39: 提交信息生成

```
/stdd:commit agent-core --tdd --phase green --issue 42
/stdd:commit evolution-engine --tdd --phase green --issue 43
/stdd:commit agent-core --tdd --phase refactor
```

---

## Phase 40: 归档

```
/stdd:archive agent-core
/stdd:archive evolution-engine
/stdd:archive rl-engine
/stdd:archive frontend-ui
```

---

## Phase 41: 上下文帮助

```
/stdd:help
```

---

## Phase 42: 进度追踪与断点续传

```
/stdd:progress
/stdd:progress --last 50
/stdd:progress --summary
/stdd:progress --resume
/stdd:progress --json
/stdd:progress --clear
```

---

## Phase 43: 快速启动向导

```
/stdd:start
```

---

## Phase 44: 历史合规审计

```
/stdd:audit
/stdd:audit --json
```

---

## Phase 45: SudoLang 执行

```
/stdd:sudo run evorl.sudo
```

---

## 预期产出

执行以上所有 `/stdd:` 命令后，应产生以下产物：

| 目录/文件 | 来源命令 |
|-----------|----------|
| `stdd/changes/agent-core/proposal.md` | `/stdd:propose` |
| `stdd/changes/agent-core/specs/*.feature` | `/stdd:spec` |
| `stdd/changes/agent-core/design.md` | `/stdd:design` `/stdd:plan` |
| `stdd/changes/agent-core/tasks.md` | `/stdd:plan` |
| `stdd/changes/agent-core/arch-decisions.md` | `/stdd:plan` |
| `stdd/changes/agent-core/evidence/` | `/stdd:apply` `/stdd:verify` |
| `stdd/changes/evolution-engine/` | `/stdd:new` `/stdd:spec` |
| `stdd/changes/rl-engine/` | `/stdd:new` `/stdd:spec` |
| `stdd/changes/frontend-ui/` | `/stdd:new` `/stdd:spec` |
| `stdd/changes/archive/` | `/stdd:archive` |
| `stdd/specs/openapi.yaml` | `/stdd:api-spec` |
| `stdd/schemas/` | `/stdd:schema` |
| `stdd/contracts/` | `/stdd:contract` |
| `src/__mocks__/` | `/stdd:mock` |
| `src/__tests__/factories/` | `/stdd:factory` |
| `stdd/memory/` | `/stdd:memory` |
| `FINAL_REQUIREMENT.md` | `/stdd:final-doc` |
| `stdd/journeys/evorl-journey.yaml` | `/stdd:story` |
| `stdd/tdd-registry.yaml` | `/stdd:outside-in init` |
| `.github/workflows/ci.yml` | `/stdd:ci` |
| `stdd/evidence/` | `/stdd:guard` `/stdd:verify` |
| `stdd/progress.jsonl` | `/stdd:progress` |
| `stdd/logs/` | 运行时生成 |

---

## 覆盖统计

| # | `/stdd:` 命令 | # | `/stdd:` 命令 |
|---|--------------|---|--------------|
| 1 | `/stdd:init` | 24 | `/stdd:plan` |
| 2 | `/stdd:new` | 25 | `/stdd:prp` |
| 3 | `/stdd:propose` | 26 | `/stdd:recommend` |
| 4 | `/stdd:clarify` | 27 | `/stdd:roles` |
| 5 | `/stdd:confirm` | 28 | `/stdd:runtime` |
| 6 | `/stdd:spec` | 29 | `/stdd:schema` |
| 7 | `/stdd:api-spec` | 30 | `/stdd:skills` |
| 8 | `/stdd:design` | 31 | `/stdd:starters` |
| 9 | `/stdd:apply` | 32 | `/stdd:status` |
| 10 | `/stdd:execute` | 33 | `/stdd:story` |
| 11 | `/stdd:continue` | 34 | `/stdd:supervisor` |
| 12 | `/stdd:verify` | 35 | `/stdd:tdd-init` |
| 13 | `/stdd:archive` | 36 | `/stdd:turbo` |
| 14 | `/stdd:mutation` | 37 | `/stdd:update` |
| 15 | `/stdd:outside-in` | 38 | `/stdd:user-test` |
| 16 | `/stdd:guard` | 39 | `/stdd:validate` |
| 17 | `/stdd:constitution` | 40 | `/stdd:vision` |
| 18 | `/stdd:contract` | 41 | `/stdd:workspace` |
| 19 | `/stdd:mock` | 42 | `/stdd:commit` |
| 20 | `/stdd:factory` | 43 | `/stdd:learn` |
| 21 | `/stdd:baby-steps` | 44 | `/stdd:brainstorm` |
| 22 | `/stdd:ff` | 45 | `/stdd:certainty` |
| 23 | `/stdd:issue` | 46 | `/stdd:complexity` |

| 续 | `/stdd:` 命令 |
|----|--------------|
| 47 | `/stdd:browser` |
| 48 | `/stdd:ci` |
| 49 | `/stdd:commands` |
| 50 | `/stdd:context` |
| 51 | `/stdd:depcheck` |
| 52 | `/stdd:doctor` |
| 53 | `/stdd:explore` |
| 54 | `/stdd:extensions` |
| 55 | `/stdd:final-doc` |
| 56 | `/stdd:fix-packet` |
| 57 | `/stdd:graph` |
| 58 | `/stdd:help` |
| 59 | `/stdd:hooks` |
| 60 | `/stdd:iterate` |
| 61 | `/stdd:list` |
| 62 | `/stdd:memory` |
| 63 | `/stdd:metrics` |
| 64 | `/stdd:parallel` |
| 65 | `/stdd:pipeline` |
| 66 | `/stdd:progress` |
| 67 | `/stdd:start` |
| 68 | `/stdd:audit` |
| 69 | `/stdd:sudo` |

> **全部 69 个 `/stdd:` 命令覆盖完毕。**

---

> 本文档用于验证 STDD Copilot 在 Claude Code 中的全部 `/stdd:` 斜杠命令可用性。
> 所有 CLI 命令与斜杠命令一一对应。
> 共覆盖 69 个斜杠命令 (含 20 个命令模板 + 38 个 Skill 模板 + 11 个 CLI-only 命令，去重后)。
> 请在 Claude Code 中按 Phase 顺序逐条执行。
