# STDD Copilot 全斜杠命令实操验证文档

> **验证项目**: EvoAgent — 强化学习/遗传算法的可进化 Agent 框架
> **验证日期**: 2026-05-14
> **验证环境**: Claude Code
> **覆盖范围**: 20 个命令模板 + 38 个 Skill + 53 个 CLI 命令 = 69 个唯一入口
> **测试用例数**: 109

---

## 验证项目描述

**EvoAgent** — 基于 RL + GA 的可进化 Agent 框架。

| 模块 | 技术栈 |
|------|--------|
| 前端 | React + TypeScript |
| 后端 | Express + Node.js |
| 数据库 | PostgreSQL + Redis |
| AI 核心 | RL 策略梯度 + GA 交叉变异 |
| 实时通信 | WebSocket (群聊/讨论) |

**功能清单**:
1. 用户注册/登录 (JWT 鉴权)
2. Agent 创建与管理 (CRUD)
3. 群组管理 (创建/加入/退出)
4. Slack 风格群聊 (Agent 在群组中讨论交流)
5. 1v1 / 1v多 讨论
6. Agent 自进化 (RL 策略优化 + GA 交叉变异)

---

## 环境准备

### 安装 STDD Copilot (三选一)

**方式 A: npm 全局安装**
```bash
npm install -g @marcher-lam/stdd-copilot@latest
stdd --version
```

**方式 B: 源码安装 (可二次开发)**
```bash
git clone https://github.com/Marcher-lam/STDD-COPILOT.git ~/stdd-copilot
cd ~/stdd-copilot && npm install && npm link
stdd --version
```

**方式 C: Docker**
```bash
git clone https://github.com/Marcher-lam/STDD-COPILOT.git ~/stdd-copilot
cd ~/stdd-copilot && docker build -t stdd-copilot . && docker-compose up -d
docker exec -it stdd-copilot stdd --help
```

### 创建验证项目

```bash
mkdir ~/evo-agent && cd ~/evo-agent
git init && npm init -y
```

之后在 `~/evo-agent` 目录下打开 Claude Code 开始验证。

---

## 测试约定

| 标记 | 含义 |
|------|------|
| `[PASS]` | 命令执行成功，输出/产物符合预期 |
| `[PASS*]` | 核心功能正常，部分行为有差异 |
| `[FAIL]` | 命令报错或产物异常 |
| `[SKIP]` | 前置条件不满足 (需 Playwright/Stryker 等) |

每个测试用例格式：
```
### T## — /stdd:xxx
输入命令 → 预期产物 → 验证点
```

---

# Part I: 完整 Feature 开发流 (核心闭环)

> 以「用户注册登录」为第一个功能，走完从 init 到 archive 的全链路。

## Phase 0: 项目初始化

### T01 — /stdd:init
```
/stdd:init
```
**预期产物**: `stdd/` 目录结构 + `stdd/config.yaml` + `.claude/commands/stdd/` + `.claude/skills/`
**验证点**:
- [ ] `stdd/` 下存在 `changes/`, `specs/`, `memory/`, `graph/`
- [ ] `stdd/config.yaml` 存在且为合法 YAML
- [ ] `.claude/commands/stdd/` 下有 20 个 `.md` 命令模板
- [ ] `.claude/skills/` 下有技能定义目录

### T02 — /stdd:vision
```
/stdd:vision
```
**预期产物**: `stdd/vision.md`
**验证点**:
- [ ] 包含 EvoAgent 的长期目标、架构北极星、战略方向

### T03 — /stdd:help
```
/stdd:help
```
**预期产物**: 上下文感知的帮助信息
**验证点**:
- [ ] 检测到项目刚初始化，推荐下一步命令
- [ ] 显示相关命令和示例

---

## Phase 1: 需求探索 (只读)

### T04 — /stdd:explore
```
/stdd:explore 分析当前项目结构和已有的代码
```
**预期产物**: `stdd/explorations/explore-*.md` 探索报告
**验证点**:
- [ ] 输出项目类型检测结果
- [ ] 报告写入 `stdd/explorations/`
- [ ] 未修改任何业务代码 (只读)

### T05 — /stdd:explore --deep
```
/stdd:explore 深入分析用户认证相关的技术选型和架构决策 --deep
```
**预期产物**: 深度探索报告
**验证点**:
- [ ] 包含技术选型建议 (JWT vs Session 等)
- [ ] 包含架构影响分析

### T06 — /stdd:brainstorm
```
/stdd:brainstorm
```
**预期产物**: 多维度分析报告 (架构洞察/代码质量/技术评估/重构建议)
**验证点**:
- [ ] 输出纯分析建议，零文件修改
- [ ] 覆盖多个分析维度

---

## Phase 2: 需求提案与澄清

### T07 — /stdd:new
```
/stdd:new 实现用户注册和登录，支持邮箱密码注册、JWT 鉴权、Token 刷新
```
**预期产物**: `stdd/changes/change-*/proposal.md` + `.status.yaml`
**验证点**:
- [ ] 创建变更目录 `stdd/changes/change-*/`
- [ ] `proposal.md` 包含需求描述
- [ ] `.status.yaml` 初始状态为 proposal 阶段

### T08 — /stdd:propose
```
/stdd:propose 用户注册登录系统，需要支持邮箱注册、密码加密存储、JWT Token 签发与刷新、登出时 Token 失效
```
**预期产物**: 更新 `proposal.md`，含 Epic 检测和边界分析
**验证点**:
- [ ] 自动检测是否需要拆分为多个 Epic
- [ ] 包含边界条件和隐式约束分析

### T09 — /stdd:clarify
```
/stdd:clarify
```
**预期产物**: 多轮澄清记录，更新 `proposal.md`
**验证点**:
- [ ] 识别模糊点、边缘场景、非功能需求
- [ ] 提出澄清问题

### T10 — /stdd:confirm
```
/stdd:confirm
```
**预期产物**: 确认门，等待人类 yes/no
**验证点**:
- [ ] 显示 proposal 摘要和范围
- [ ] 回复「确认」后推进到 spec 阶段

### T11 — /stdd:prp
```
/stdd:prp
```
**预期产物**: What/Why/How/Success 结构化规划文档
**验证点**:
- [ ] 输出四段式规划 (What/Why/How/Success)
- [ ] 便于干系人对齐

---

## Phase 3: 规格生成 (BDD)

### T12 — /stdd:spec
```
/stdd:spec
```
**预期产物**: `specs/` 下的 BDD `.feature` 文件 (Given/When/Then)
**验证点**:
- [ ] 生成 delta specs，含 ADDED/MODIFIED/REMOVED 标记
- [ ] 每个 scenario 遵循 Given/When/Then 格式

### T13 — /stdd:validate
```
/stdd:validate
```
**预期产物**: 规格合规诊断报告
**验证点**:
- [ ] 检查 BDD 格式合规
- [ ] 检查 RFC 2119 关键词使用
- [ ] 检测覆盖缺口和跨变更冲突

### T14 — /stdd:validate --spec-guardian --fix
```
/stdd:validate --spec-guardian --fix
```
**预期产物**: Spec Guardian 泄漏检测 + 自动修复
**验证点**:
- [ ] 检测 specs 中是否泄漏了实现细节 (路径、DB 表名、类名)
- [ ] `--fix` 自动写入 rewrite suggestions

### T15 — /stdd:api-spec
```
/stdd:api-spec
```
**预期产物**: `api-spec.yaml` (OpenAPI 规范) + TypeScript 类型定义
**验证点**:
- [ ] 包含 `/auth/register`、`/auth/login`、`/auth/refresh`、`/auth/logout` 路径
- [ ] 生成 `src/types/api.ts` 类型定义

### T16 — /stdd:schema
```
/stdd:schema
```
**预期产物**: JSON Schema + Zod 运行时校验 + TypeScript 类型
**验证点**:
- [ ] 生成 `{User,LoginRequest,AuthResponse}.schema.json`
- [ ] 生成 `src/schemas/{type}.ts` Zod schema

### T17 — /stdd:contract
```
/stdd:contract
```
**预期产物**: 消费者驱动契约测试 (Pact 格式)
**验证点**:
- [ ] 生成 `{consumer}-{provider}.pact.json`
- [ ] 包含注册/登录的请求响应契约

---

## Phase 4: 设计与任务拆解

### T18 — /stdd:plan
```
/stdd:plan
```
**预期产物**: `tasks.md` (5-6 个原子微任务，每个约 30 分钟)
**验证点**:
- [ ] 每个任务有明确描述和验收标准
- [ ] 任务粒度在 5-6 个左右
- [ ] `.status.yaml` 更新到 design 阶段

### T19 — /stdd:design --full
```
/stdd:design --full
```
**预期产物**: `design.md` (技术设计文档 + ADR)
**验证点**:
- [ ] 包含 Context/Decision/Rationale/Consequences ADR 格式
- [ ] 包含数据模型、API 设计、文件级变更
- [ ] 包含风险评估和测试策略

---

## Phase 5: TDD 实现

### T20 — /stdd:guard on
```
/stdd:guard on
```
**预期产物**: TDD 守护规则启用
**验证点**:
- [ ] 启用 test-first (Blocking)、minimal-impl (Warning)、test-must-fail (Warning)、no-skip-refactor (Suggestion) 四条规则

### T21 — /stdd:apply
```
/stdd:apply
```
**预期产物**: Ralph Loop TDD 循环 (RED → CHECK → GREEN → MUTATION → REFACTOR)
**验证点**:
- [ ] 先生成失败测试 (RED)
- [ ] 运行静态检查 (CHECK)
- [ ] 最简实现通过测试 (GREEN)
- [ ] 变异审查 (MUTATION)
- [ ] 代码重构 (REFACTOR)
- [ ] `.status.yaml` 更新任务完成状态

### T22 — /stdd:apply --task=TASK-002
```
/stdd:apply --task=TASK-002
```
**预期产物**: 执行指定任务
**验证点**:
- [ ] 跳到 TASK-002 执行，不影响 TASK-001 状态

### T23 — /stdd:apply --fix
```
/stdd:apply --fix
```
**预期产物**: 修复失败测试
**验证点**:
- [ ] 识别当前失败测试并修复

### T24 — /stdd:execute
```
/stdd:execute
```
**预期产物**: Ralph Loop 执行循环 (与 apply 互为别名)
**验证点**:
- [ ] 同样执行 RED → GREEN → REFACTOR 循环

### T25 — /stdd:mock
```
/stdd:mock
```
**预期产物**: `src/__mocks__/{service}.mock.ts`
**验证点**:
- [ ] 为外部依赖生成 mock 实现
- [ ] mock 文件可被测试框架自动加载

### T26 — /stdd:mock --all --fake
```
/stdd:mock --all --fake
```
**预期产物**: 扫描所有依赖并生成 working fakes
**验证点**:
- [ ] `--all` 扫描所有外部依赖
- [ ] `--fake` 生成可运行的 fake 而非 stub

### T27 — /stdd:factory
```
/stdd:factory
```
**预期产物**: `src/__factories__/{Type}Factory.ts` + `scenarios.ts`
**验证点**:
- [ ] 使用 Builder pattern + Faker.js 生成测试数据工厂
- [ ] 覆盖正常/边界/异常场景

### T28 — /stdd:mutation
```
/stdd:mutation
```
**预期产物**: 变异测试报告 (Quick AI + Stryker 两层)
**验证点**:
- [ ] Quick 模式生成启发式 mutation score
- [ ] 输出 anti-fake-green 检测结果

### T29 — /stdd:outside-in
```
/stdd:outside-in
```
**预期产物**: 从 E2E → 集成 → 单元 层层推进的 TDD 实现
**验证点**:
- [ ] 从用户可见行为开始写测试
- [ ] 逐步向内驱动实现

---

## Phase 6: 验证与质量

### T30 — /stdd:verify
```
/stdd:verify
```
**预期产物**: 5 维验证报告 (API 签名/BDD 覆盖/类型/边界异常/文档一致性)
**验证点**:
- [ ] 检查实现与规格的一致性
- [ ] 输出逐项验证结果

### T31 — /stdd:verify --all --fix
```
/stdd:verify --all --fix
```
**预期产物**: 验证所有变更 + 自动修复
**验证点**:
- [ ] `--all` 验证所有活跃变更
- [ ] `--fix` 自动修复不一致

### T32 — /stdd:metrics
```
/stdd:metrics
```
**预期产物**: 质量指标仪表板
**验证点**:
- [ ] 显示测试覆盖率 (>=80%)、mutation score (>=70%)
- [ ] 显示 lint 警告、类型错误、复杂度
- [ ] 跨变更趋势

### T33 — /stdd:metrics --export
```
/stdd:metrics --export
```
**预期产物**: 导出质量报告到文件
**验证点**:
- [ ] 生成可归档的指标报告文件

### T34 — /stdd:complexity
```
/stdd:complexity
```
**预期产物**: 代码复杂度分析 + Top-10 热点
**验证点**:
- [ ] 圈复杂度、认知复杂度、APP Mass 分析
- [ ] 输出重构建议

### T35 — /stdd:certainty
```
/stdd:certainty
```
**预期产物**: 5 维度置信度评分 (需求清晰度/技术可行性/风险/测试覆盖/愿景对齐)
**验证点**:
- [ ] 每个维度 1-5 分评分
- [ ] 低于阈值 (默认 3.5) 时暂停请求人类确认

---

## Phase 7: 提交与归档

### T36 — /stdd:user-test
```
/stdd:user-test
```
**预期产物**: `user-test.md` 人类可读的验收测试脚本
**验证点**:
- [ ] 从 BDD 规格生成自然语言测试步骤
- [ ] 非技术人员可执行

### T37 — /stdd:final-doc
```
/stdd:final-doc
```
**预期产物**: `FINAL_REQUIREMENT.md` 综合文档
**验证点**:
- [ ] 聚合 proposal + specs + design + tasks + 实现记录 + 质量指标

### T38 — /stdd:commit
```
/stdd:commit
```
**预期产物**: 原子化 git commit (red:/green:/refactor: 前缀)
**验证点**:
- [ ] 提交信息遵循 TDG 阶段前缀格式
- [ ] 提交前通过 Constitution 规则验证

### T39 — /stdd:archive
```
/stdd:archive
```
**预期产物**: 变更归档 + delta specs 合并到 `stdd/specs/`
**验证点**:
- [ ] 变更目录移动到 `stdd/changes/archive/YYYY-MM-DD-{change-id}/`
- [ ] ADDED specs 追加、MODIFIED specs 替换、REMOVED specs 删除
- [ ] 生成 `spec-merge-report.json`

### T40 — /stdd:guard status
```
/stdd:guard status
```
**预期产物**: 当前 guard 规则状态
**验证点**:
- [ ] 显示四条规则的启用/禁用状态

---

# Part II: 快捷流程与 Bug 修复

## Phase 8: 快捷入口

### T41 — /stdd:ff (Fast-Forward)
```
/stdd:ff 实现 Agent 创建与管理，支持 CRUD 操作，每个 Agent 有名称、描述、配置参数
```
**预期产物**: 一次性生成 proposal + specs + design + tasks 四个核心产物
**验证点**:
- [ ] 四个文件全部生成
- [ ] 变更目录结构完整
- [ ] 控制台提示可执行 `/stdd:apply`

### T42 — /stdd:ff --dry-run
```
/stdd:ff 实现群组管理功能 --dry-run
```
**预期产物**: 仅预览不执行
**验证点**:
- [ ] 显示将要生成的产物列表
- [ ] 未创建任何文件

### T43 — /stdd:continue
```
/stdd:continue
```
**预期产物**: 自动检测 `.status.yaml`，推进到下一个缺失产物
**验证点**:
- [ ] 正确识别当前阶段
- [ ] 生成下一个产物并更新状态

### T44 — /stdd:continue --specs
```
/stdd:continue --specs
```
**预期产物**: 强制生成 specs 产物
**验证点**:
- [ ] 跳过其他阶段，直接生成 specs

### T45 — /stdd:turbo
```
/stdd:turbo 实现 Agent 自进化功能，支持 RL 策略梯度优化和 GA 交叉变异，包含适应度评估和进化代数追踪
```
**预期产物**: 串行执行 propose → clarify → confirm → spec → plan 全流程
**验证点**:
- [ ] 所有前置阶段产物完整
- [ ] 在确认门暂停等待人类确认

---

## Phase 9: Bug 修复

### T46 — /stdd:issue
```
/stdd:issue
```
**预期产物**: TDD Bug 修复流程
**验证点**:
- [ ] 引导用户描述 bug
- [ ] 自动分类 bug 类型
- [ ] 先写失败测试 (RED)，再最小修复 (GREEN)
- [ ] 回归验证

---

# Part III: Graph 引擎与多 Agent 协作

## Phase 10: Graph 引擎

### T47 — /stdd:graph visualize
```
/stdd:graph visualize
```
**预期产物**: Skill Graph 依赖图 (Mermaid 格式)
**验证点**:
- [ ] 显示 38 个 Skill 的 DAG 依赖关系
- [ ] 当前阶段高亮

### T48 — /stdd:graph visualize --format=html
```
/stdd:graph visualize --format=html
```
**预期产物**: HTML 格式可视化
**验证点**:
- [ ] 生成可浏览器打开的 HTML 文件

### T49 — /stdd:graph analyze
```
/stdd:graph analyze
```
**预期产物**: 当前状态分析 + 可执行路径
**验证点**:
- [ ] 分析当前项目状态
- [ ] 列出可执行的 Skill 路径

### T50 — /stdd:graph analyze --bottlenecks
```
/stdd:graph analyze --bottlenecks
```
**预期产物**: 瓶颈分析
**验证点**:
- [ ] 识别工作流瓶颈

### T51 — /stdd:graph run feature
```
/stdd:graph run feature
```
**预期产物**: 按 feature intent DAG 执行完整 workflow
**验证点**:
- [ ] 按 ff → spec → outside-in → apply → verify → archive 路径执行

### T52 — /stdd:graph run --intent repair
```
/stdd:graph run --intent repair --change-name <change>
```
**预期产物**: 按 repair intent 走 fix-packet → apply → verify
**验证点**:
- [ ] 从 fix-packet 开始修复流程

### T53 — /stdd:graph parallel --detect
```
/stdd:graph parallel --detect
```
**预期产物**: 检测可并行的 Skill
**验证点**:
- [ ] 列出无依赖关系的 Skill 组

### T54 — /stdd:graph parallel --execute
```
/stdd:graph parallel --execute --max-workers=4
```
**预期产物**: 并行执行独立 Skill
**验证点**:
- [ ] 并行执行无依赖任务

### T55 — /stdd:graph history
```
/stdd:graph history
```
**预期产物**: 执行历史记录
**验证点**:
- [ ] 显示时间戳、执行状态、Skill 名称

### T56 — /stdd:graph history --failures
```
/stdd:graph history --failures
```
**预期产物**: 仅显示失败记录
**验证点**:
- [ ] 过滤只显示失败项

### T57 — /stdd:graph recommend
```
/stdd:graph recommend
```
**预期产物**: 智能推荐下一步
**验证点**:
- [ ] 基于当前状态推荐命令和原因

---

## Phase 11: 多 Agent 与角色协作

### T58 — /stdd:roles list
```
/stdd:roles list
```
**预期产物**: 12 个 Agent 角色列表
**验证点**:
- [ ] 显示 po, developer, tester, reviewer, architect, security, devops, ux, ba, techwriter, qalead, dataanalyst

### T59 — /stdd:roles party
```
/stdd:roles party 群组讨论的 WebSocket 通信协议选型 --roles=architect,developer,security
```
**预期产物**: 多 Agent 辩论记录
**验证点**:
- [ ] 三个角色依次发言
- [ ] 观点有冲突和收敛

### T60 — /stdd:roles adversarial
```
/stdd:roles adversarial src/auth/
```
**预期产物**: 对抗式安全审查报告
**验证点**:
- [ ] 扫描 risk-pattern
- [ ] 输出安全风险和建议

### T61 — /stdd:supervisor start
```
/stdd:supervisor start
```
**预期产物**: 启动 Supervisor 多 Agent 协调器
**验证点**:
- [ ] 显示协调器状态

### T62 — /stdd:supervisor status
```
/stdd:supervisor status
```
**预期产物**: 当前 agent 任务分配状态
**验证点**:
- [ ] 显示各 agent 工作状态

### T63 — /stdd:parallel
```
/stdd:parallel
```
**预期产物**: DAG 分析 + 并行执行独立任务
**验证点**:
- [ ] 识别可并行的任务组
- [ ] 并行执行并聚合结果

---

# Part IV: 学习、记忆与迭代

## Phase 12: 记忆系统

### T64 — /stdd:memory save
```
/stdd:memory save
```
**预期产物**: 将高价值上下文持久化到向量数据库
**验证点**:
- [ ] 存储到 `stdd/memory/vectors/`

### T65 — /stdd:memory search
```
/stdd:memory search 用户认证架构决策
```
**预期产物**: 语义搜索结果
**验证点**:
- [ ] 返回相关记忆条目

### T66 — /stdd:memory stats
```
/stdd:memory stats
```
**预期产物**: 记忆系统统计
**验证点**:
- [ ] 显示存储条目数和占用空间

---

## Phase 13: 自适应学习

### T67 — /stdd:learn scan
```
/stdd:learn scan
```
**预期产物**: 代码风格 pattern 提取 → `code-patterns.json` + `styleguide.md`
**验证点**:
- [ ] 提取命名/模块/测试/错误处理风格
- [ ] 输出可复用的 pattern

### T68 — /stdd:learn good
```
/stdd:learn good "TDD 循环中红绿重构的节奏控制得很好"
```
**预期产物**: 记录正面反馈
**验证点**:
- [ ] 反馈被记录到学习系统

### T69 — /stdd:learn bad
```
/stdd:learn bad "mock 数据不够真实，导致集成测试通过了但生产环境失败"
```
**预期产物**: 记录负面反馈
**验证点**:
- [ ] 反馈被记录，影响后续行为

### T70 — /stdd:learn suggest
```
/stdd:learn suggest "群聊消息应该使用消息队列而不是直接 WebSocket 推送"
```
**预期产物**: 记录改进建议
**验证点**:
- [ ] 建议被记录

### T71 — /stdd:learn status
```
/stdd:learn status --json
```
**预期产物**: 学习系统状态
**验证点**:
- [ ] 显示已学习的 pattern 数量和反馈统计

---

## Phase 14: 上下文与迭代

### T72 — /stdd:context
```
/stdd:context
```
**预期产物**: 三层文档上下文 (Foundation ~500t + Component ~1000t + Feature ~2000t)
**验证点**:
- [ ] 加载 foundation.md、components.md、contracts.md
- [ ] 总 token 不超过 ~3500

### T73 — /stdd:context --export
```
/stdd:context --export
```
**预期产物**: 导出上下文到文件
**验证点**:
- [ ] 生成可共享的上下文文件

### T74 — /stdd:iterate
```
/stdd:iterate
```
**预期产物**: Plan-Execute-Reflect 自主迭代循环
**验证点**:
- [ ] 自动迭代改进实现质量
- [ ] 检测质量退化时停止

### T75 — /stdd:iterate --max 5
```
/stdd:iterate --max 5
```
**预期产物**: 限制最多 5 轮迭代
**验证点**:
- [ ] 5 轮后自动停止

---

# Part V: Constitution 治理

## Phase 15: Constitution 管理

### T76 — /stdd:constitution
```
/stdd:constitution
```
**预期产物**: 显示 9 篇条例概览
**验证点**:
- [ ] 列出全部 9 篇，含优先级 (Blocking/Warning/Suggestion)

### T77 — /stdd:constitution show 2
```
/stdd:constitution show 2
```
**预期产物**: TDD 条例 (Article 2) 详情
**验证点**:
- [ ] 显示测试先行、覆盖率 gate、mutation evidence gate 规则

### T78 — /stdd:constitution check
```
/stdd:constitution check
```
**预期产物**: 逐条合规检查结果
**验证点**:
- [ ] 每篇条例显示通过/失败

### T79 — /stdd:constitution check --changed
```
/stdd:constitution check --changed
```
**预期产物**: 仅检查有变更的条例
**验证点**:
- [ ] 过滤只检查变更相关条例

### T80 — /stdd:constitution waivers
```
/stdd:constitution waivers
```
**预期产物**: 当前豁免列表
**验证点**:
- [ ] 显示已申请的豁免及有效期

### T81 — /stdd:constitution waiver
```
/stdd:constitution waiver --article=2 --reason="Legacy 认证模块迁移" --days=7
```
**预期产物**: 创建临时豁免
**验证点**:
- [ ] 写入豁免记录，7 天后自动过期
- [ ] 审计追踪完整

---

# Part VI: 辅助 CLI 验证 (终端执行)

> 以下命令需在终端执行（Claude Code 中用 `!` 前缀），用于辅助验证斜杠命令产生的产物。

### T82 — stdd list / status
```bash
! stdd list
! stdd list --specs
! stdd list --archived
! stdd list --json
! stdd status
! stdd status --json
```
**验证点**: 确认斜杠命令创建的变更在 list/status 中可见

### T83 — stdd skills / commands
```bash
! stdd skills
! stdd skills --phase 4
! stdd commands
```
**验证点**: Skills 和斜杠命令列表完整

### T84 — stdd hooks
```bash
! stdd hooks install
! stdd hooks verify
! stdd hooks status
! stdd hooks disable
! stdd hooks enable
```
**验证点**: Hook 系统安装/验证/状态/切换

### T85 — stdd workspace
```bash
! stdd workspace list
! stdd workspace validate
! stdd workspace repair
```
**验证点**: Workspace 管理三件套

### T86 — stdd recommend / depcheck / doctor
```bash
! stdd recommend
! stdd depcheck
! stdd doctor
```
**验证点**: 推荐/依赖检查/诊断

### T87 — stdd constitution (CLI 侧)
```bash
! stdd constitution
! stdd constitution show 2
! stdd constitution status
! stdd constitution audit --json
! stdd constitution fix --article 2 --dry-run
```
**验证点**: Constitution 完整 CLI 流程

### T88 — stdd runtime
```bash
! stdd runtime agent start "Agent 通信协议选型" --rounds 3
! stdd runtime agent next --json
! stdd runtime agent stop
```
**验证点**: Agent 状态机 (Party Mode) 运行时

### T89 — stdd browser
```bash
! stdd browser doctor
! stdd browser doctor --json
# (需要前端 dev server 运行)
! stdd browser snapshot http://localhost:3000
! stdd browser inspect http://localhost:3000
```
**验证点**: 浏览器自动化 (需 Playwright)

---

# Part VII: 实时进度追踪与断点续传

> **新增功能**: `stdd progress` 命令 + `stdd/progress.jsonl` 全局进度日志。
> 每条 CLI 命令执行时自动记录 start/complete/fail/interrupt，终端关闭/崩溃后可断点恢复。

### T90 — stdd progress
```bash
! stdd progress
```
**预期产物**: 显示最近 20 条进度记录 (▶start ✓complete ✗fail ⚡interrupt)
**验证点**:
- [ ] 显示每条命令的类型、时间、命令名、关联 change
- [ ] 包含之前所有已执行命令的记录

### T91 — stdd progress --last 50
```bash
! stdd progress --last 50
```
**预期产物**: 显示最近 50 条记录
**验证点**:
- [ ] 数量上限正确

### T92 — stdd progress --summary
```bash
! stdd progress --summary
```
**预期产物**: 进度总览 (总命令数/成功/失败/中断/未完成)
**验证点**:
- [ ] `Completed` 数量 >= 0
- [ ] 如有未完成命令，显示 `⚠ N incomplete → stdd progress --resume`

### T93 — stdd progress --resume
```bash
! stdd progress --resume
```
**预期产物**: 显示上次中断命令的恢复上下文 + 推荐的 resume 命令
**验证点**:
- [ ] 如有未完成命令：显示 command、timestamp、推荐 `stdd continue`
- [ ] 如无未完成：显示 `✅ No incomplete commands.`

### T94 — stdd progress --json
```bash
! stdd progress --json
```
**预期产物**: JSON 格式输出最近进度
**验证点**:
- [ ] 输出为合法 JSON 数组
- [ ] 每条记录含 id/ts/ev/cmd 字段

### T95 — stdd progress --clear
```bash
! stdd progress --clear
```
**预期产物**: 清空进度日志
**验证点**:
- [ ] `stdd/progress.jsonl` 文件被清空
- [ ] `stdd progress` 显示 `No progress recorded.`

### T96 — 进度文件持久化验证
```bash
# 1. 执行一个命令
! stdd ff "测试进度追踪" --change-name test-progress-track

# 2. 查看原始进度文件
! cat stdd/progress.jsonl

# 3. 确认包含 ff 命令的 start 和 complete 记录
```
**预期产物**: `stdd/progress.jsonl` 中包含 JSONL 格式的进度记录
**验证点**:
- [ ] 每行是合法 JSON
- [ ] ff 命令有对应的 `{"ev":"start","cmd":"ff",...}` 和 `{"ev":"complete",...}` 两行
- [ ] `args` 字段包含 changeName 信息

### T97 — 中断恢复场景模拟
```bash
# 模拟：执行一个会失败的命令，验证 fail 记录
! stdd apply nonexistent-change 2>/dev/null; true

# 查看进度
! stdd progress --last 5

# 查看恢复上下文
! stdd progress --resume
```
**预期产物**: 失败命令被记录为 `✗ fail`
**验证点**:
- [ ] 进度日志中出现 `ev: "fail"` 记录
- [ ] `stdd progress --resume` 能识别失败并提供恢复建议

---

# Part VIII: 补全 CLI 命令覆盖

> 补全 12 个之前未覆盖的 CLI 命令：update / fix-packet / ci / starters / extensions / story / pipeline / tdd-init / audit / baby-steps / sudo run / start。

### T98 — stdd update
```bash
! stdd update --dry-run
```
**预期产物**: 显示将要更新的文件列表，不实际写入
**验证点**:
- [ ] 输出 diff 列表或 "Already up to date"
- [ ] `--dry-run` 模式未修改任何文件

### T99 — stdd fix-packet
```bash
! stdd fix-packet
```
**预期产物**: 为当前变更生成 Golden Packet 风格的失败上下文
**验证点**:
- [ ] 检测当前活跃变更
- [ ] 输出包含 task 描述、测试命令、环境信息

### T100 — stdd ci
```bash
! stdd ci github
```
**预期产物**: 生成 `.github/workflows/ci.yml`
**验证点**:
- [ ] 文件存在且为合法 YAML
- [ ] 包含 test、lint、verify 步骤

### T101 — stdd starters
```bash
! stdd starters list
```
**预期产物**: 显示可用 starter 模板列表
**验证点**:
- [ ] 输出至少一个 starter 类型
- [ ] 显示使用说明

### T102 — stdd extensions
```bash
! stdd extensions list
! stdd extensions validate
```
**预期产物**: 扩展列表 + 验证结果
**验证点**:
- [ ] `list` 显示已安装扩展 (可能为空)
- [ ] `validate` 检查扩展结构合规

### T103 — stdd story
```bash
! stdd story create evo-journey --persona "AI Researcher"
```
**预期产物**: `stdd/journeys/evo-journey.yaml` 故事映射文件
**验证点**:
- [ ] 生成 YAML 文件包含 persona、episodes、steps
- [ ] 格式可被 `stdd story bdd` 解析

### T104 — stdd pipeline
```bash
! stdd pipeline
```
**预期产物**: 从 specs 生成 parser IR 和验收测试骨架
**验证点**:
- [ ] 扫描活跃变更的 specs
- [ ] 输出 pipeline IR 或测试骨架文件

### T105 — stdd tdd-init
```bash
! stdd tdd-init --dry-run
```
**预期产物**: 显示将要生成的测试脚手架
**验证点**:
- [ ] 扫描 src/ 下的源文件
- [ ] `--dry-run` 不写入文件

### T106 — stdd audit
```bash
! stdd audit --json
```
**预期产物**: 历史合规审计报告 (JSON)
**验证点**:
- [ ] 输出合法 JSON
- [ ] 包含 constitution 合规历史记录

### T107 — stdd baby-steps
```bash
! stdd baby-steps "实现 Agent 通信总线"
```
**预期产物**: 交互式 TDD 小步引导
**验证点**:
- [ ] 检测到活跃变更
- [ ] 输出 TDD 步骤提示 (或需要 TTY 交互)

### T108 — stdd sudo run
```bash
! stdd sudo run evorl.sudo
```
**预期产物**: 执行 SudoLang 逻辑并返回验证结果
**验证点**:
- [ ] 文件不存在时输出错误信息
- [ ] 文件存在时解析并执行伪代码逻辑

### T109 — stdd start
```bash
! stdd start
```
**预期产物**: 非 TTY 环境输出帮助文本，TTY 环境启动交互向导
**验证点**:
- [ ] Claude Code 中 (`!` 前缀) 输出帮助文本
- [ ] 终端中启动交互式 quick-start 向导

---

# 验证结果汇总

| # | 命令 | 状态 | 备注 |
|---|------|------|------|
| T01 | `/stdd:init` | | |
| T02 | `/stdd:vision` | | |
| T03 | `/stdd:help` | | |
| T04 | `/stdd:explore` | | |
| T05 | `/stdd:explore --deep` | | |
| T06 | `/stdd:brainstorm` | | |
| T07 | `/stdd:new` | | |
| T08 | `/stdd:propose` | | |
| T09 | `/stdd:clarify` | | |
| T10 | `/stdd:confirm` | | |
| T11 | `/stdd:prp` | | |
| T12 | `/stdd:spec` | | |
| T13 | `/stdd:validate` | | |
| T14 | `/stdd:validate --spec-guardian --fix` | | |
| T15 | `/stdd:api-spec` | | |
| T16 | `/stdd:schema` | | |
| T17 | `/stdd:contract` | | |
| T18 | `/stdd:plan` | | |
| T19 | `/stdd:design --full` | | |
| T20 | `/stdd:guard on` | | |
| T21 | `/stdd:apply` | | |
| T22 | `/stdd:apply --task=TASK-002` | | |
| T23 | `/stdd:apply --fix` | | |
| T24 | `/stdd:execute` | | |
| T25 | `/stdd:mock` | | |
| T26 | `/stdd:mock --all --fake` | | |
| T27 | `/stdd:factory` | | |
| T28 | `/stdd:mutation` | | |
| T29 | `/stdd:outside-in` | | |
| T30 | `/stdd:verify` | | |
| T31 | `/stdd:verify --all --fix` | | |
| T32 | `/stdd:metrics` | | |
| T33 | `/stdd:metrics --export` | | |
| T34 | `/stdd:complexity` | | |
| T35 | `/stdd:certainty` | | |
| T36 | `/stdd:user-test` | | |
| T37 | `/stdd:final-doc` | | |
| T38 | `/stdd:commit` | | |
| T39 | `/stdd:archive` | | |
| T40 | `/stdd:guard status` | | |
| T41 | `/stdd:ff` | | |
| T42 | `/stdd:ff --dry-run` | | |
| T43 | `/stdd:continue` | | |
| T44 | `/stdd:continue --specs` | | |
| T45 | `/stdd:turbo` | | |
| T46 | `/stdd:issue` | | |
| T47 | `/stdd:graph visualize` | | |
| T48 | `/stdd:graph visualize --format=html` | | |
| T49 | `/stdd:graph analyze` | | |
| T50 | `/stdd:graph analyze --bottlenecks` | | |
| T51 | `/stdd:graph run feature` | | |
| T52 | `/stdd:graph run --intent repair` | | |
| T53 | `/stdd:graph parallel --detect` | | |
| T54 | `/stdd:graph parallel --execute` | | |
| T55 | `/stdd:graph history` | | |
| T56 | `/stdd:graph history --failures` | | |
| T57 | `/stdd:graph recommend` | | |
| T58 | `/stdd:roles list` | | |
| T59 | `/stdd:roles party` | | |
| T60 | `/stdd:roles adversarial` | | |
| T61 | `/stdd:supervisor start` | | |
| T62 | `/stdd:supervisor status` | | |
| T63 | `/stdd:parallel` | | |
| T64 | `/stdd:memory save` | | |
| T65 | `/stdd:memory search` | | |
| T66 | `/stdd:memory stats` | | |
| T67 | `/stdd:learn scan` | | |
| T68 | `/stdd:learn good` | | |
| T69 | `/stdd:learn bad` | | |
| T70 | `/stdd:learn suggest` | | |
| T71 | `/stdd:learn status --json` | | |
| T72 | `/stdd:context` | | |
| T73 | `/stdd:context --export` | | |
| T74 | `/stdd:iterate` | | |
| T75 | `/stdd:iterate --max 5` | | |
| T76 | `/stdd:constitution` | | |
| T77 | `/stdd:constitution show 2` | | |
| T78 | `/stdd:constitution check` | | |
| T79 | `/stdd:constitution check --changed` | | |
| T80 | `/stdd:constitution waivers` | | |
| T81 | `/stdd:constitution waiver` | | |
| T82 | `stdd list/status` | | |
| T83 | `stdd skills/commands` | | |
| T84 | `stdd hooks` | | |
| T85 | `stdd workspace` | | |
| T86 | `stdd recommend/depcheck/doctor` | | |
| T87 | `stdd constitution (CLI)` | | |
| T88 | `stdd runtime agent` | | |
| T89 | `stdd browser` | | |
| T90 | `stdd progress` | | |
| T91 | `stdd progress --last 50` | | |
| T92 | `stdd progress --summary` | | |
| T93 | `stdd progress --resume` | | |
| T94 | `stdd progress --json` | | |
| T95 | `stdd progress --clear` | | |
| T96 | 进度文件持久化验证 | | |
| T97 | 中断恢复场景模拟 | | |
| T98 | `stdd update --dry-run` | | |
| T99 | `stdd fix-packet` | | |
| T100 | `stdd ci github` | | |
| T101 | `stdd starters list` | | |
| T102 | `stdd extensions list/validate` | | |
| T103 | `stdd story create` | | |
| T104 | `stdd pipeline` | | |
| T105 | `stdd tdd-init --dry-run` | | |
| T106 | `stdd audit --json` | | |
| T107 | `stdd baby-steps` | | |
| T108 | `stdd sudo run` | | |
| T109 | `stdd start` | | |

**总计**: 109 个测试用例
- 斜杠命令: 81 个 (T01-T81)
- 辅助 CLI: 8 个 (T82-T89)
- 进度追踪: 8 个 (T90-T97)
- 补全 CLI: 12 个 (T98-T109)
- 覆盖 20 个命令模板 + 38 个 Skill + 53 个 CLI 命令 + 进度追踪

---

## 推荐执行顺序

```
Part I    (T01-T40)  → 完整 Feature 闭环: init → explore → new → propose → clarify → confirm → spec → plan → apply → verify → archive
Part II   (T41-T46)  → 快捷流程: ff / continue / turbo / issue
Part III  (T47-T63)  → Graph 引擎 + 多 Agent: graph */roles/supervisor/parallel
Part IV   (T64-T75)  → 学习记忆: memory/learn/context/iterate
Part V    (T76-T81)  → Constitution 治理
Part VI   (T82-T89)  → 辅助 CLI 验证
Part VII  (T90-T97)  → 实时进度追踪与断点续传
Part VIII (T98-T109) → 补全 CLI 命令覆盖: update/fix-packet/ci/starters/extensions/story/pipeline/tdd-init/audit/baby-steps/sudo/start
```
