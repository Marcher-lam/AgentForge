# AgentForge — 项目全景文档

> 版本: 6.3 | 更新: 2026-05-19 | 方法论: STDD
> 前后端 + 三个算法引擎 + Agentic RAG + 技能/工具系统 + RL 写回闭环 + 流式输出 + 消息持久化 + 工具执行 + 协同进化 + 统一监控 + LLM Profile 批量应用

---

## 1. 项目概览

| 维度 | 数据 |
|------|------|
| 项目名称 | AgentForge — 多智能体协作平台 |
| 一句话定位 | Spec-Driven Multi-Agent RL + Evolution Framework with Agentic RAG |
| 后端 | Python 3.12+ / FastAPI / WebSocket / asyncio |
| 前端 | React 19 + TypeScript + Vite + TailwindCSS + Recharts |
| RL 引擎 | PPO / DQN / REINFORCE（NumPy 真实训练） |
| 进化引擎 | 遗传算法（锦标赛/SBX/高斯变异 + 人格优化 → 结果写回 Agent） |
| 知识库 | Milvus + fastembed (BAAI/bge-small-en-v1.5, 384维语义 embedding) |
| 聊天架构 | Agentic RAG（LLM 自主决策：知识库检索/联网搜索/直接回答） |
| 技能系统 | SKILL.md 原生格式（OpenClaw / AgentSkills 兼容）+ 在线 URL 安装 |
| 工具系统 | MCP 协议（JSON Schema 校验）+ npm 在线安装 |
| 记忆系统 | 双层：ChatMemory(时序摘要) + 向量索引(fastembed 384维)，严格 ≤4400 chars 上下文预算 |
| API 端点 | 58 REST/WebSocket 路由 |
| 流式输出 | WebSocket chunk 协议 + typing 指示器 + 自动滚动 |
| 消息持久化 | SQLite write-through 缓存（sessions/messages/agent_configs 三表）+ 重启自动恢复 |
| 工具执行闭环 | ReAct 循环（LLM tool_calls → 执行 MCP/Skill → 回复），最多 3 轮 |
| 协同进化 | RL + Evolution 两阶段（RL 训练 → 奖励统计注入进化适应度 → Pareto 前沿排名） |
| 前端测试 | 47 vitest 全部通过 |
| 状态管理 | Jotai atoms |

---

## 2. 技术栈

| 层 | 技术 | 选型理由 |
|----|------|----------|
| Agent 核心 | Python 3.12 + asyncio | 异步原生，Protocol 接口 |
| 消息通信 | asyncio + websockets | 进程内零拷贝 + 跨进程 WebSocket |
| 记忆存储 | SQLite + NumPy vectors | 嵌入式、零运维、语义检索 |
| 知识库 | Milvus + fastembed | Per-Agent collection, 创建 Agent 自动建库, JSON 文件上传 |
| 联网搜索 | DuckDuckGo HTML | 零外部依赖 |
| RL 训练 | NumPy | 轻量数值计算，真实 PPO/DQN |
| 进化计算 | NumPy | 轻量遗传算法 |
| 技能系统 | SKILL.md (OpenClaw 兼容) | 标准格式，生态复用 |
| 工具系统 | MCP 协议 + JSON Schema | 标准化工具注册 |
| 前端 | React 19 + Jotai + Tailwind + Recharts + react-markdown + KaTeX | 响应式状态管理 + 数据可视化 + Markdown/LaTeX 渲染 |
| 测试 | pytest + vitest | 全栈 TDD |

---

## 3. 项目结构

```
AgentForge/
├── agentforge/                        # Python 后端
│   ├── agent/
│   │   ├── base.py                    # AgentBase ABC（状态机：init→run→stop→destroy）
│   │   ├── events.py                  # Agent 事件定义
│   │   └── llm_agent.py              # LLMAgent（LLM + 工具 + 技能 + 记忆集成）
│   ├── bus/
│   │   ├── inprocess.py               # 进程内消息总线（pub/sub, RPC, 背压）
│   │   ├── websocket.py               # WebSocket 消息总线（重连恢复）
│   │   └── topic_matcher.py           # Topic 匹配器（*单层, **多层通配）
│   ├── llm/
│   │   ├── protocol.py                # LLMBackend Protocol + LLMRequest/LLMMessage
│   │   ├── openai_backend.py          # OpenAI 兼容后端
│   │   ├── anthropic_backend.py        # Anthropic Claude 后端
│   │   └── ollama_backend.py          # Ollama 本地模型后端
│   ├── evoforge/                      # 遗传算法引擎
│   │   ├── engine/
│   │   │   ├── evolution.py           # EvolutionEngine（世代循环）
│   │   │   ├── population.py          # Population + Individual（谱系追踪）
│   │   │   ├── callbacks.py           # 回调系统 + 统计收集
│   │   │   └── termination.py         # 终止条件（含多样性检测）
│   │   ├── genomes/                   # RealGenome / BinaryGenome / TreeGenome
│   │   ├── operators/                 # 选择/交叉/变异/替换
│   │   └── fitness/                   # 适应度函数 + 多目标 + 异步包装
│   ├── rlforge/                       # 强化学习引擎
│   │   ├── environment.py             # CartPole 风格环境
│   │   ├── policy.py                  # 2层 MLP 策略网络 + Adam 优化器
│   │   ├── trainer.py                 # RLTrainer（统一训练入口）
│   │   ├── ppo.py                     # PPO（ActorCritic + GAE + PPO-Clip）
│   │   ├── dqn.py                     # DQN（ReplayBuffer + 目标网络 + e-greedy）
│   │   ├── buffer.py                  # ReplayBuffer + RolloutBuffer
│   │   └── checkpoint.py              # 模型检查点保存/加载
│   ├── skills/
│   │   ├── registry.py                # 技能注册表（SKILL.md 原生格式）
│   │   └── skill_md.py                # SKILL.md 解析/序列化
│   ├── tools/
│   │   ├── registry.py                # 简单工具注册表
│   │   └── mcp_registry.py            # MCP 工具注册表（JSON Schema 校验）
│   ├── memory/
│   │   ├── chat_memory.py             # 时序记忆（Per-session 紧凑摘要，≤800 chars 预算）
│   │   ├── short_term.py              # 短期记忆（LRU, OrderedDict）
│   │   ├── long_term.py               # 长期记忆（SQLite + TTL）
│   │   ├── vector_memory.py           # 向量记忆（fastembed 384维语义 embedding）
│   │   ├── knowledge_base.py          # Milvus 知识库（Per-Agent collection + JSON上传）
│   │   └── manager.py                 # 三层记忆统一门面
│   ├── server/
│   │   ├── app.py                     # FastAPI 应用（完整后端）
│   │   ├── main.py                    # Uvicorn 启动入口
│   │   └── run.py                     # CLI REPL 入口
│   ├── types/
│   │   ├── config.py                  # AgentConfig / LLMOverride / Evolution / RL / MCP 配置
│   │   ├── errors.py                  # 异常类型层级
│   │   ├── message.py                 # 消息类型定义
│   │   ├── memory.py                  # 记忆类型（MemoryType / MemoryEntry / SearchResult）
│   │   ├── protocols.py               # Protocol 接口定义
│   │   └── state.py                   # Agent 状态机（AgentState + 状态转换）
│   └── infra/
│       ├── config.py                  # 全局配置管理
│       ├── logging.py                 # structlog 结构化日志
│       ├── shutdown.py                # 优雅关闭（信号处理）
│       ├── persistence.py             # SQLite 消息持久化（WAL 模式三表 + 重启恢复）
│       └── monitoring.py              # 统一监控系统（5000 事件环形缓冲 + 类型/严重度/会话过滤）
├── skills/                            # 技能目录（SKILL.md 格式）
│   ├── code-review/SKILL.md           # 代码审查技能
│   └── web-search/SKILL.md            # 网络搜索技能
├── schemas/                           # JSON Schema 模板
│   └── knowledge-template.json        # 知识库上传空模板
├── frontend/                          # React 前端
│   ├── src/
│   │   ├── App.tsx                    # 主应用（WebSocket + REST + 聊天管理）
│   │   ├── atoms/
│   │   │   └── index.ts              # Jotai 状态 atoms
│   │   ├── types/
│   │   │   └── api.ts                 # TypeScript 类型定义
│   │   ├── schemas/
│   │   │   ├── communication.ts       # 通信协议 schema
│   │   │   ├── evorl-custom.ts        # EvoRL 自定义 schema
│   │   │   └── evorl-workflow.ts      # EvoRL 工作流 schema
│   │   ├── components/
│   │   │   ├── chat/
│   │   │   │   ├── MessagePanel.tsx    # 消息列表渲染
│   │   │   │   └── ChatInput.tsx       # 输入框 + 发送
│   │   │   ├── grid/
│   │   │   │   └── AgentGrid.tsx       # 智能体卡片管理（创建/编辑/删除 + 全配置）
│   │   │   ├── dashboard/
│   │   │   │   └── DashboardPage.tsx   # 仪表盘（卡片网格 + 训练记录分栏 + 图表）
│   │   │   ├── monitor/
│   │   │   │   └── MonitorPage.tsx      # 消息监控面板（统计/筛选/自动滚动）
│   │   │   └── settings/
│   │   │       └── SettingsPage.tsx    # 设置页（LLM卡片/MCP/技能 + 在线安装）
│   │   ├── hooks/
│   │   │   └── useWebSocket.ts        # WebSocket Hook
│   │   └── utils/
│   │       └── lttb.ts                # LTTB 降采样算法
│   ├── index.html
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── package.json
├── tests/                             # 后端测试目录
├── pyproject.toml                     # Python 项目配置
├── stdd/                              # STDD 方法论文档
│   ├── vision.md                      # 项目愿景
│   ├── FINAL_REQUIREMENT.md           # 全项目交付文档
│   ├── specs/                         # BDD 规格文件
│   └── changes/                       # 变更记录
└── project.md                         # 本文档
```

---

## 4. 核心功能详解

### 4.1 多智能体三阶段讨论引擎

用户发送消息后，系统自动执行三阶段讨论流程（严格相关性过滤，避免所有 Agent 扎堆回复）：

```
┌─────────────────────────────────────────────────────────┐
│                  用户发送消息                              │
├─────────────────────────────────────────────────────────┤
│  Phase 1 — 严格相关性判定                                 │
│  每个 Agent LLM 判断话题是否属于核心专业                    │
│  "必须是只有你这个角色才能专业回答才算相关"                 │
│  泛社交不算相关，宽泛问题只有最对口专家回答                 │
│  无人相关时 fallback 取前 2 个 Agent 友好回复              │
│  ↓ relevant_agents / spectator_agents 分类               │
├─────────────────────────────────────────────────────────┤
│  Phase 2 — 核心讨论 + @提及链（relevant agents）           │
│  仅相关 Agent 多轮深度讨论（2-3轮），保持角色风格和口头禅    │
│  Agent 可主动 @其他Agent 转交问题或邀请补充视角             │
│  被 @ 的 Agent 自动加入讨论（链式深度最多 3 层）           │
├─────────────────────────────────────────────────────────┤
│  Phase 3 — 旁观者评论（spectator agents）                  │
│  不相关 Agent 仅在确有独特跨界视角时简短发言（64 tokens）   │
│  否则 PASS，不强行蹭话题                                  │
└─────────────────────────────────────────────────────────┘
```

**实现位置**: `agentforge/server/app.py` → `_handle_group_chat()` 函数

**关键参数**:
- 最大讨论轮数: 3（可配置）
- 相关性判定: 每个 Agent 独立 LLM 调用，严格过滤（"必须是只有你这个角色才能专业回答才算相关"）
- 旁观者约束: max_tokens=64 + 严格 PASS prompt，防止强行蹭话题
- @提及链: Agent 回复中含 @其他Agent名 时，被 @ Agent 自动加入讨论，最多 3 层链式触发
- @提及范围: 前端 @mention 下拉列表仅展示当前会话成员（session 级过滤），非全局 Agent 列表
- 群成员管理: 点击群聊标识弹出成员面板，支持查看/邀请/移出成员（类微信群交互）
- Fallback: 无人相关时取前 2 个 Agent 友好回复，避免全体沉默
- 群聊模式: `GROUP_BROADCAST` 会话类型

**记忆接入**: 每个 Agent 在讨论时独立检索自己的记忆上下文，包括短期、长期和向量记忆。

### 4.2 Agentic RAG（知识库 + 联网搜索）

每个 Agent 独立拥有 Milvus collection（创建 Agent 时自动创建对应知识库，启动时自动 seed 8 条角色专属领域知识），聊天时遵循 Agentic RAG 范式：

```
┌───────────────────────────────────────────────────────┐
│               Agentic RAG 三阶段流程                    │
├───────────────────────────────────────────────────────┤
│  Stage 1 — 记忆检索 (严格预算控制)                      │
│  热层: ChatMemory 当前会话时序 (≤800 chars)              │
│  冷层: 向量语义跨会话检索 (≤300 chars)                   │
│  ↓                                                     │
│  Stage 2 — Agentic 决策（LLM 根据问题+角色自主判断）     │
│  输入: 用户原始问题 + Agent 角色信息                      │
│  LLM 选择策略:                                         │
│    A. 仅知识库检索 (Per-Agent Milvus collection)            │
│    B. 仅联网搜索 (DuckDuckGo)                           │
│    C. 知识库 + 联网搜索                                 │
│    D. 直接回答（不需要外部信息）                          │
│  ↓                                                     │
│  Stage 3 — 生成回复                                    │
│  融合 system_prompt + 记忆 + RAG + 讨论记录              │
│  总上下文 ≤4400 chars / 2200 tokens                     │
└───────────────────────────────────────────────────────┘
```

**实现位置**: `agentforge/server/app.py` → `_agent_reply()` 函数

**技术栈**:
- **Milvus**: 向量数据库，Per-Agent collection 隔离，默认 Docker 地址 `http://127.0.0.1:19530`，可用 `MILVUS_URI` 覆盖
- **fastembed**: BAAI/bge-small-en-v1.5, 384维 ONNX 语义 embedding（无需 PyTorch）
- **DuckDuckGo**: HTML 搜索，urllib 实现，零外部依赖

**知识库 API**:

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/agents/{id}/knowledge` | 兼容旧接口：上传 texts 数组 |
| POST | `/api/agents/{id}/knowledge/upload-json` | 上传 JSON 知识文件（用户预处理 documents 格式） |
| GET | `/api/agents/{id}/knowledge/search?q=关键词` | 语义检索知识 |
| GET | `/api/knowledge/template` | 下载知识库 JSON 空模板（含字段说明） |

### 4.3 Per-Agent 独立配置

每个智能体根据自身角色独立配置所有能力：

```
AgentConfig:
  ├── name: str                      # 智能体名称
  ├── system_prompt: str             # 系统提示词
  ├── llm: LLMOverride              # 独立的模型/温度/Key 配置
  │   ├── provider_profile: str     # 引用 LLM Profile 卡片
  │   ├── model: str                # 具体模型 ID
  │   ├── temperature: float
  │   └── api_key: str
  ├── tool_ids: list[str]           # 从全局工具池选择
  ├── skill_ids: list[str]          # 从全局技能池选择
  ├── mcp_server_ids: list[str]     # 关联的 MCP 服务器
  ├── evolution: EvolutionConfig    # 独立进化参数
  │   ├── mode: str                 # "agent" | "sphere"
  │   ├── population_size: int
  │   ├── max_generations: int
  │   ├── mutation_rate: float
  │   ├── elite_size: int
  │   ├── genome_dim: int
  │   └── seed: int
  └── rl: RLConfig                  # 独立 RL 训练参数
      ├── algorithm: str            # "PPO" | "DQN" | "REINFORCE"
      ├── total_steps: int
      ├── learning_rate: float
      └── seed: int
```

**三层架构**: 全局注册表 → AgentConfig 筛选 → 运行时接线

**LLM Profile 卡片**: 设置页管理多个 Provider（OpenAI/Anthropic/Ollama），每个卡片包含 provider + base_url + api_key + models 列表。Agent 通过 `provider_profile` 引用卡片 + `model` 选择具体模型。

**实现位置**:
- 后端类型: `agentforge/types/config.py`
- 后端逻辑: `agentforge/server/app.py` → `_create_llm_for_agent()`
- 前端组件: `frontend/src/components/grid/AgentGrid.tsx`

### 4.4 SKILL.md 技能系统（OpenClaw 兼容）

技能使用 SKILL.md 标准格式，与 OpenClaw / AgentSkills 完全兼容：

```markdown
---
name: code-review
description: Code review skill
metadata: {"openclaw": {"requires": {"bins": ["python"]}}}
---

# Instructions
Step-by-step instructions for the agent...
```

**功能特性**:
- YAML frontmatter（name / description / metadata）+ Markdown 指令体
- 支持 OpenClaw 门控机制（requires.bins / requires.env / os）
- 技能指令自动注入到 Agent 的系统提示中
- 同一技能目录在 AgentForge 和 OpenClaw 中都能直接使用

**安装方式**:
- 直接内容 POST: `{ "content": "---\\nname: ...\\n---\\n..." }`
- 本地路径安装: `{ "path": "./skills/code-review" }`
- 在线 URL 安装: `{ "url": "https://github.com/user/skill-repo" }`

**实现位置**:
- 解析/序列化: `agentforge/skills/skill_md.py`
- 注册表: `agentforge/skills/registry.py`
- API: `agentforge/server/app.py` → skill 相关端点

### 4.5 MCP 工具管理

- MCP 协议工具注册表（JSON Schema 参数校验）
- 全局工具池 + 按 Agent 筛选接线
- MCP 服务器注册（stdio / url 连接方式）
- 在线安装：输入 npm 包名自动配置为 stdio 模式

```bash
# 从 npm 在线安装 MCP 服务器
curl -X POST localhost:8000/api/mcp-servers/install-online \
  -d '{"package": "@modelcontextprotocol/server-filesystem", "args": "/path/to/dir"}'
```

**实现位置**:
- 注册表: `agentforge/tools/mcp_registry.py`
- API: `agentforge/server/app.py` → mcp-server 相关端点

### 4.6 双轨记忆系统（共享 + 独立，严格上下文预算）

**核心设计**: 群聊共享全量记忆 + Agent独立标记 + 总上下文 ≤4400 chars (≈2200 tokens)

```
┌───────────────────────────────────────────────────┐
│  热层: ChatMemory (双轨时序记忆)                    │
│  ├── 共享层: 群聊完整对话流(所有Agent看到相同记录)    │
│  │   ├── 保留 raw_content (≤300字原文)              │
│  │   └── 每个 Agent 看到 (我) 标记自己的发言和被@    │
│  ├── 个人层: Per-Agent 独立过滤视图                  │
│  │   ├── 自己的回复                                 │
│  │   ├── 被 @mention 的事件                         │
│  │   ├── 用户问题 + 共识点                          │
│  │   └── 独立存储，互不干扰                         │
│  ├── 按 session_id 隔离（群聊A不污染群聊B）         │
│  ├── 事件摘要 ≤80字（非原文500字）                  │
│  ├── 注入 prompt 严格 ≤800 chars                    │
│  └── 动作: 问/答/@提及/PASS/共识/话题切换           │
├───────────────────────────────────────────────────┤
│  冷层: 向量语义索引 (跨会话长尾检索)                 │
│  ├── fastembed BAAI/bge-small-en-v1.5 (384维)      │
│  ├── 仅存储长度>100的实质性回复                      │
│  ├── cosine 相似度排序 + 去重                       │
│  ├── 每 Agent 最多 500 条，自动淘汰                  │
│  └── 注入 ≤300 chars                                │
├───────────────────────────────────────────────────┤
│  上下文预算控制:                                    │
│  ├── 时序记忆 (热层): ≤800 chars                    │
│  ├── 语义记忆 (冷层): ≤300 chars                    │
│  ├── RAG 检索结果:   ≤1000 chars                    │
│  ├── 讨论原文:       ≤3000 chars (最新10条)          │
│  └── 总计:           ≤4400 chars / 2200 tokens      │
│      (vs 旧系统 ~8400 chars / 4200 tokens)          │
└───────────────────────────────────────────────────┘
```

**实现位置**:
- 时序记忆: `agentforge/memory/chat_memory.py`（ChatEvent + ChatMemory）
- 向量记忆: `agentforge/memory/vector_memory.py`（NumPy + fastembed）
- 管理器: `agentforge/memory/manager.py`（统一检索 + 去重排序）
- 长期记忆: `agentforge/memory/long_term.py`（SQLite，周期清理 TTL 过期）

### 4.7 进化引擎（EvoForge）

**智能体人格优化模式**:
- 10 维人格基因（sigmoid → [0,1]）
- 维度: 创造力、同理心、幽默感、严谨性、好奇心、冒险性、社交性、耐心、批判性、适应性
- 适应度 = 平衡性 + 多样性 - 极端值

**进化结果闭环**:
1. 进化完成 → 获取最优基因组
2. sigmoid 值映射为人格特质描述
3. 自动修改 Agent 的 system_prompt，追加人格修饰

```python
# 进化写回回调模式
run = EvolutionRun(
    config=..., 
    broadcast_fn=..., 
    agent_id=agent_id,
    on_complete=lambda result: writeback_personality(agent_id, result)
)
```

**经典基准模式**: 球面函数优化

**算子**:
- 选择: 锦标赛 / 轮盘赌 / 精英保留
- 交叉: 单点 / 多点 / 均匀 / SBX / 子树交换
- 变异: 高斯 / 均匀 / 位翻转 / 子树变异

**可视化**: 进化树 SVG（红→绿颜色映射适应度）+ 基因热力图

**实现位置**: `agentforge/evoforge/`

### 4.8 强化学习引擎（RLForge）

**真实训练**（NumPy 实现），非模拟：

| 算法 | 核心实现 |
|------|----------|
| PPO | ActorCritic + GAE + PPO-Clip + mini-batch epochs + entropy bonus |
| DQN | ReplayBuffer + 目标网络 + ε-greedy 衰减 |
| REINFORCE | 简单策略梯度 + 价值基线 |

**训练环境**: CartPole 风格（4维状态, 2动作）

**网络**: 2层 MLP 策略网络 + Adam 优化器

**Checkpoint**: 训练后自动保存到 `checkpoints/` 目录

**RL 结果写回 Agent**（与进化引擎闭环一致）:
1. 训练完成 → `_extract_strategy()` 提取策略信号
2. 奖励方差 → temperature 映射（高方差=创意型=高 temp，低方差=稳健型=低 temp）
3. 后期 loss → max_tokens 映射（收敛=简洁，未收敛=详细）
4. 算法特征 → 策略描述（PPO=平衡型，DQN=经验型，REINFORCE=探索型）
5. 写入 Agent system_prompt `[RL策略优化]` 标签 + 更新 config.llm.temperature/max_tokens
6. `_agent_reply` 使用 Agent 级 temperature（非硬编码 0.7）

**训练流程**:
```
Agent 创建 → 配置 RL 参数 → POST /api/agents/{id}/rl/start
→ 后台异步训练 → WebSocket 广播进度 → 训练完成保存 checkpoint
→ GET /api/agents/{id}/rl/runs 查看历史
```

**实现位置**: `agentforge/rlforge/`

### 4.9 流式输出（WebSocket Chunk 协议）

**完整事件序列**:
```
用户发送消息
  → WebSocket {type: "message", sender: "user", content: "..."}
  → WebSocket {type: "typing", sender_name: "程序员"}
  → WebSocket {type: "chunk", content: "首"}    ← 逐 token
  → WebSocket {type: "chunk", content: "先"}    ← 逐 token
  → ...
  → WebSocket {type: "message", sender: agent_id, content: "完整回复"}
```

**前端实现**:
- 收到 `typing` → 显示 "XXX 正在输入..."
- 收到 `chunk` → 追加到占位消息，逐 token 渲染
- 收到最终 `message` → 替换占位消息为完整消息
- 自动滚动到底部（可手动关闭）

### 4.10 消息持久化（SQLite Write-Through）

**架构**:
```
┌────────────────────────────────────────────────┐
│  PersistenceStore (persistence.py)              │
│  ├── SQLite WAL 模式（读写并发安全）              │
│  ├── sessions 表: 会话元数据                     │
│  ├── messages 表: 消息记录（含 sender/content）   │
│  ├── agent_configs 表: Agent 配置快照             │
│  ├── 写入路径: 每条消息即时写入                    │
│  ├── 读取路径: 启动时全量恢复 + API 查询时读取     │
│  └── 搜索: FTS5 全文搜索（messages 内容）          │
└────────────────────────────────────────────────┘
```

**恢复流程**: 后端启动 → `state.db.restore_all_sessions()` → 重建内存会话/消息/Agent 配置

### 4.11 工具执行闭环（ReAct 循环）

```
用户提问 → LLM 第 1 次 complete()
  → 检测 tool_calls？
    → 有: 执行工具 → 记录 monitor(tool_call) → 结果追加到上下文
    → LLM 第 2 次 complete()（使用工具结果）
      → 还有 tool_calls？
        → 重复（最多 3 轮）
      → 无: 流式输出最终回复
    → 无: 流式输出回复
```

**支持的工具类型**:
- MCP 工具：通过 MCP 服务器调用（JSON Schema 参数校验）
- 技能工具：SKILL.md 格式技能的指令注入
- 内置工具：web_search（DuckDuckGo）

### 4.12 协同进化（Phase 5：RL + Evolution）

**两阶段流程**:
```
阶段 1: RL 训练
  → 指定 Agent 的 RL 配置启动训练
  → 训练完成 → 提取奖励统计（均值/方差/最大值）

阶段 2: RL 增强的进化
  → 适应度函数: 60% 人格质量 + 40% RL 对齐度
  → 运行遗传算法 N 代
  → Pareto 前沿排名（Top 5 个体）
  → 写回最优个体人格 → [协同进化人格优化] 标签
```

**API**: `POST /api/coevolution/start` 或 `POST /api/agents/{id}/coevolution/start`

**实现位置**: `agentforge/server/app.py` → `CoEvolutionRun` 类

### 4.13 统一监控系统

**架构**:
```
┌──────────────────────────────────────────────────┐
│  MonitorStore (monitoring.py)                     │
│  ├── 5000 事件 deque 环形缓冲（自动淘汰旧事件）     │
│  ├── 14 种事件类型:                                │
│  │   system / message / typing / chunk             │
│  │   tool_call / llm / rag / memory                │
│  │   rl / evolution / coevolution / persistence    │
│  │   error / custom                                │
│  ├── 3 种严重度: info / warning / error             │
│  ├── 维度过滤: type / severity / session / agent   │
│  ├── 实时统计: 总量/按类型/按严重度/活跃Agent        │
│  └── WebSocket 在线数 + 训练状态                    │
├──────────────────────────────────────────────────┤
│  监控埋点位置（app.py）:                           │
│  ├── 用户发消息 → record("message")                │
│  ├── Agent 打字中 → record("typing")               │
│  ├── LLM 探测工具 → record("llm")                 │
│  ├── 工具执行 → record("tool_call")                │
│  ├── chunk 收集完成 → record("chunk")              │
│  ├── 消息持久化 → record("persistence")            │
│  └── 系统启动 → record("system")                   │
├──────────────────────────────────────────────────┤
│  前端: MonitorPage.tsx                            │
│  ├── 系统概览卡片 (Events/WebSocket/Training/统计)  │
│  ├── 事件类型分布条（颜色编码）                     │
│  ├── 最近错误提示栏                                │
│  ├── 事件列表 + 类型筛选 + 关键词搜索 + 自动滚动    │
│  ├── 事件详情面板（点击展开 payload）               │
│  └── 3 秒轮询刷新                                 │
└──────────────────────────────────────────────────┘
```

**API 端点**:
- `GET /api/monitor/events` — 事件列表（支持 type/severity/session_id/agent_id/run_id/limit 过滤）
- `GET /api/monitor/stats` — 系统概览（事件统计 + WebSocket 在线数 + 训练状态）

---

## 5. API 端点大全

### 5.1 智能体管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/agents` | 列出所有智能体 |
| POST | `/api/agents` | 创建智能体（含完整 config: LLM/技能/MCP/进化/RL） |
| GET | `/api/agents/{id}` | 获取智能体详情（含接线工具、技能、配置） |
| PATCH | `/api/agents/{id}` | 热更新智能体配置 |
| DELETE | `/api/agents/{id}` | 删除智能体 |
| POST | `/api/agents/{id}/evolution/start` | 启动 per-agent 进化 |
| POST | `/api/agents/{id}/rl/start` | 启动 per-agent RL 训练 |
| GET | `/api/agents/{id}/evolution/runs` | 获取 Agent 进化训练历史 |
| GET | `/api/agents/{id}/rl/runs` | 获取 Agent RL 训练历史 |

### 5.2 知识库（Agentic RAG）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/agents/{id}/knowledge` | 兼容旧接口：上传 texts 数组 |
| POST | `/api/agents/{id}/knowledge/upload-json` | 上传 JSON 知识文件（用户预处理 documents 格式） |
| GET | `/api/agents/{id}/knowledge/search` | 语义检索知识（?q=关键词&top_k=5） |
| GET | `/api/knowledge/template` | 下载知识库 JSON 空模板 |

### 5.3 LLM Profile 管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/llm-profiles` | 返回所有 Provider 卡片（api_key 打码） |
| POST | `/api/llm-profiles` | 创建 Provider 卡片 |
| PUT | `/api/llm-profiles/{id}` | 更新卡片 |
| DELETE | `/api/llm-profiles/{id}` | 删除卡片 |

### 5.4 工具管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/tools` | 列出全局工具池 |
| POST | `/api/tools` | 注册工具（name, schema, description） |
| DELETE | `/api/tools/{name}` | 注销工具 |

### 5.5 技能管理（SKILL.md 格式）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/skills` | 列出已安装技能 |
| POST | `/api/skills` | 安装技能（提供 SKILL.md 内容） |
| POST | `/api/skills/install-path` | 从路径安装技能 |
| POST | `/api/skills/install-url` | 从在线 URL 安装技能（支持 GitHub） |
| GET | `/api/skills/{name}` | 获取技能详情（含 SKILL.md 原文） |
| DELETE | `/api/skills/{name}` | 卸载技能 |

### 5.6 MCP 服务器管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/mcp-servers` | 列出已注册 MCP 服务器 |
| POST | `/api/mcp-servers` | 注册 MCP 服务器 |
| POST | `/api/mcp-servers/install-online` | 从 npm 在线安装 MCP 服务器 |
| DELETE | `/api/mcp-servers/{id}` | 注销 MCP 服务器 |

### 5.7 会话 & 通信

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/sessions` | 列出会话 |
| POST | `/api/sessions` | 创建会话（单聊/群聊，含 agent_ids 和 type） |
| GET | `/api/sessions/{id}/messages` | 获取消息历史 |
| DELETE | `/api/sessions/{id}` | 删除会话及其消息 |
| DELETE | `/api/sessions/{id}/messages/{mid}` | 删除单条消息 |
| GET | `/api/sessions/{id}/export` | 导出聊天记录（JSON，含会话/消息/Agent 信息） |
| GET | `/api/sessions/{id}/members` | 获取群成员列表 |
| POST | `/api/sessions/{id}/members` | 添加群成员（body: `{agent_id}`） |
| DELETE | `/api/sessions/{id}/members/{agent_id}` | 移除群成员 |
| GET | `/api/settings` | 获取全局 LLM 配置 |
| PUT | `/api/settings` | 更新全局 LLM 配置 |
| WS | `/ws` | WebSocket 实时通信 |

### 5.8 进化 & RL

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/evolution/start` | 启动进化引擎 |
| GET | `/api/evolution/{id}` | 查询进化状态（含进化树 + 热力图 + 逐代日志） |
| POST | `/api/evolution/{id}/cancel` | 取消进化 |
| POST | `/api/rl/start` | 启动 RL 训练 |
| GET | `/api/rl/{id}` | 查询训练状态（含逐步日志） |
| POST | `/api/rl/{id}/cancel` | 取消训练 |

### 5.9 协同进化

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/coevolution/start` | 启动全局协同进化 |
| POST | `/api/agents/{id}/coevolution/start` | 启动 per-agent 协同进化 |
| GET | `/api/coevolution/{id}` | 查询协同进化状态（Pareto 前沿 + 双阶段进度） |
| POST | `/api/coevolution/{id}/cancel` | 取消协同进化 |

### 5.10 监控系统

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/monitor/events` | 事件列表（支持 type/severity/session_id/agent_id/run_id/limit 过滤） |
| GET | `/api/monitor/stats` | 系统概览（事件统计 + WebSocket 在线数 + 训练状态 + Agents/Sessions/Messages） |

### 5.11 消息搜索

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/messages/search` | 全文搜索消息（?q=关键词&session_id=&limit=） |

### 5.12 批量操作

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/agents/batch-update-llm` | 批量更新 Agent 的 LLM Profile（指定 agent_ids + provider_profile + model） |

---

## 6. 前端页面

| Tab | 功能描述 |
|-----|----------|
| **对话** | 会话列表（单聊/群聊切换）+ 消息面板 + WebSocket 实时通信。现代 IM 风格 UI：渐变圆形头像（12 种角色配色）、Per-Agent 独立色调气泡、完整 Markdown 渲染（标题/代码块/表格/列表/引用）+ LaTeX 公式（KaTeX 行内 `$...$` / 块级 `$$...$$`）+ 代码语法高亮（highlight.js）。@提及仅展示当前会话成员（非全局 Agent）。群聊成员管理：点击群标识弹出成员面板，支持查看成员、邀请新成员、移出成员（类微信群交互）。启动自带"AI 专家团队"群聊（10 个预设角色）。支持删除会话（带确认）、导出聊天记录 |
| **智能体** | 卡片式管理。创建时一步配齐 LLM Provider/Model + 技能 + MCP + 进化参数 + RL 参数。渐变头像、能力徽章、per-agent 配置。详情弹窗支持下载 JSON 空模板 + 上传知识文件到 Milvus 专属 collection。点击跳转对话 |
| **监控** | 统一监控面板。系统概览卡片（事件数/WebSocket 在线/训练状态/Agents/Sessions/Messages）+ 事件类型分布条 + 最近错误栏 + 事件列表（14 种类型筛选/关键词搜索/自动滚动）+ 点击查看事件详情（完整 payload） |
| **仪表盘** | Agent 卡片网格 → 点击弹出训练记录（进化/RL 双 Tab）→ 左日志右图表分栏 + 每图放大按钮 + LTTB 大数据降采样 |
| **设置** | 多 Provider LLM 卡片（启动自动创建默认卡片）+ MCP 服务（手动 + 在线 npm 安装）+ 技能管理（在线 URL + 路径 + 文本安装） |

---

## 7. 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `LLM_PROVIDER` | `openai` | LLM 服务商（openai / anthropic / ollama） |
| `LLM_MODEL` | — | 模型名称 |
| `LLM_API_KEY` | — | API 密钥 |
| `LLM_BASE_URL` | — | 自定义 API 地址 |
| `MILVUS_URI` | `http://127.0.0.1:19530` | Milvus Docker standalone 服务地址（可用环境变量覆盖） |
| `LLM_SYSTEM_PROMPT` | `You are a helpful AI assistant.` | 默认智能体提示词 |

---

## 8. 预设 AI 专家团队

系统启动时自动创建 10 个 AI 专家 Agent + 一个"AI 专家团队"群聊会话：

| # | 角色 | 个性关键词 | 口头禅 | 进化 | RL |
|---|------|-----------|--------|------|-----|
| 1 | 程序员 | 务实、冷幽默、直接 | "别急，先看日志" | 30代 | PPO 300步 |
| 2 | 哲学家 | 温和、爱反问、安静幽默 | "我们可能在问错问题" | 40代 | REINFORCE 500步 |
| 3 | 数学家 | 简洁精准、逻辑洁癖 | "等一下，这个前提成立吗？" | 50代 | DQN 500步 |
| 4 | ML工程师 | 接地气、先看数据 | "先跑个baseline再说" | 35代 | PPO 400步 |
| 5 | DL工程师 | 热情、爱打比方 | "这跟Attention的思路好像" | 40代 | PPO 500步 |
| 6 | RL工程师 | 自嘲、冒险家气质 | "奖励函数决定一切" | 50代 | PPO 1000步 |
| 7 | C++工程师 | 干脆利落、强迫症 | "先profile再优化" | 30代 | DQN 400步 |
| 8 | 推理工程师 | 实际、不画饼 | "推理延迟打下来才是真本事" | 35代 | PPO 500步 |
| 9 | 前端工程师 | 活泼、UX执念 | "这个交互可以再丝滑一点" | 30代 | PPO 300步 |
| 10 | 产品经理 | 感染力、用户至上 | "用户场景是什么？" | 30代 | PPO 300步 |

---

## 9. 快速启动

```bash
# 1. 安装后端依赖
pip install -e ".[dev,llm]"

# 2. 安装前端依赖
cd frontend && npm install && cd ..

# 3. 启动后端（使用本地模型示例）
LLM_PROVIDER=openai \
LLM_MODEL='VLM/Qwen3.6-35B-A3B-4bit' \
LLM_API_KEY=EMPTY \
LLM_BASE_URL='http://127.0.0.1:8888/v1' \
uvicorn agentforge.server.main:create_and_run --host 0.0.0.0 --port 8000 --factory

# 4. 启动前端（另一个终端）
cd frontend && npx vite --host 0.0.0.0 --port 5173

# 5. 打开浏览器
open http://localhost:5173
```

---

## 10. 测试

```bash
# 前端测试
cd frontend && npx vitest run

# 前端类型检查
cd frontend && npx tsc --noEmit

# 后端测试
python -m pytest tests/ -v
```

---

## 11. 架构特征

| 特征 | 描述 |
|------|------|
| 项目类型 | 全栈 Web 应用 + AI Agent 框架 + 算法引擎 |
| 架构模式 | 前后端分离，REST + WebSocket，Per-Agent 配置 |
| Agent 状态机 | init → run → stop → destroy（AgentBase ABC） |
| 消息总线 | InProcess（进程内 pub/sub/RPC）+ WebSocket（跨进程重连恢复） |
| LLM 后端 | Protocol 接口解耦，支持 OpenAI / Anthropic / Ollama |
| 算法引擎 | EvoForge（遗传算法）+ RLForge（PPO/DQN/REINFORCE）独立模块 |
| 技能互操作 | SKILL.md 标准格式，与 OpenClaw 生态双向零转换 |
| 记忆闭环 | 三层记忆接入聊天，Agent 回复前检索 + 回复后存储 |
| 进化闭环 | 最优基因组 → 人格特质 → system_prompt 写回 |
| RAG 闭环 | Per-Agent Milvus collection + fastembed + JSON上传 + 联网搜索 + LLM 自主决策 |
| 数据可视化 | Recharts 双 Y 轴图表 + LTTB 降采样 + 进化树 SVG + 热力图 |
| 群聊管理 | @提及会话级过滤 + 群成员面板（查看/邀请/移出）+ 成员 API |

---

## 12. 关键数据结构

### 11.1 消息类型

```python
# agentforge/types/message.py
class Message:
    id: str
    session_id: str
    sender: str          # "user" | agent_id
    content: str
    msg_type: str        # "chat" | "system" | "command"
    metadata: dict
    timestamp: datetime
```

### 11.2 Agent 配置

```python
# agentforge/types/config.py
@dataclass
class AgentConfig:
    llm: LLMOverride | None = None
    tool_ids: list[str] = field(default_factory=list)
    skill_ids: list[str] = field(default_factory=list)
    mcp_server_ids: list[str] = field(default_factory=list)
    evolution: EvolutionConfig | None = None
    rl: RLConfig | None = None

@dataclass
class LLMOverride:
    provider_profile: str | None = None  # 引用 LLM Profile 卡片
    provider: str | None = None
    model: str | None = None
    base_url: str | None = None
    api_key: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None

@dataclass
class EvolutionConfig:
    mode: str = "agent"              # "agent" | "sphere"
    population_size: int = 50
    max_generations: int = 50
    mutation_rate: float = 0.1
    elite_size: int = 2
    genome_dim: int = 10
    seed: int = 42

@dataclass
class RLConfig:
    algorithm: str = "PPO"           # "PPO" | "DQN" | "REINFORCE"
    total_steps: int = 200
    learning_rate: float = 0.001
    seed: int = 42
```

### 11.3 LLM Profile

```python
# agentforge/server/app.py (AppState.llm_profiles)
{
    "profile-id": {
        "id": "uuid",
        "name": "本地Qwen",
        "provider": "openai",
        "base_url": "http://127.0.0.1:8888/v1",
        "api_key": "EMPTY",
        "models": ["VLM/Qwen3.5-9B-MLX-4bit"]
    }
}
```

### 11.4 前端类型

```typescript
// frontend/src/types/api.ts
interface Agent {
  id: string;
  name: string;
  system_prompt: string;
  config: AgentConfig;
}

interface LLMProfile {
  id: string;
  name: string;
  provider: string;
  base_url: string;
  api_key: string;
  models: string[];
}

interface EvoRun {
  id: string;
  status: string;
  generation: number;
  best_fitness: number;
  config: object;
  log: object[];
}

interface RLRun {
  id: string;
  status: string;
  step: number;
  total_steps: number;
  reward: number;
  loss: number;
  config: object;
  log: object[];
}
```

---

## 13. 里程碑状态

| Phase | 描述 | 状态 |
|-------|------|------|
| Phase 1 | 核心骨架（Agent 状态机 + 消息总线 + 基础设施） | ✅ 完成 |
| Phase 2 | 能力层（MCP 工具 + SKILL.md 技能 + 三层记忆 + Per-Agent 配置） | ✅ 完成 |
| Phase 3 | 算法引擎（PPO/DQN/REINFORCE + 遗传算法 + 人格优化） | ✅ 完成 |
| Phase 4 | 可视化 & UX（仪表盘 + 监控 + 设置 + 聊天管理 + RAG） | ✅ 完成 |
| Phase 5 | 协同进化（RL + Evolution 协同 + Pareto 优化 + 人格写回闭环） | ✅ 完成 |
| Phase 6 | 生产就绪（分布式训练 + 端到端加密 + CI/CD） | 📋 待开发 |

---

## 14. 质量度量

| 维度 | 数据 |
|------|------|
| 后端导入 | 全模块零错误 |
| 前端编译 | TypeScript 零错误 |
| 后端测试 | 298 passed / 0 failed / 9 skipped |
| 后端测试文件 | 29（19 unit + 6 integration + 4 e2e） |
| 前端测试 | 47 vitest 全部通过 |
| API 端点 | 58 REST/WebSocket 路由 |
| 流式输出 | WebSocket chunk 协议 + typing 指示器 + 自动滚动 |
| 消息持久化 | SQLite write-through 缓存（sessions/messages/agent_configs 三表）+ 重启自动恢复 |
| 工具执行闭环 | ReAct 循环（LLM tool_calls → 执行 MCP/Skill → 回复），最多 3 轮 |
| 协同进化 | RL + Evolution 两阶段（RL 训练 → 奖励统计注入进化适应度 → Pareto 前沿排名） |
| 统一监控 | MonitorStore 5000 事件环形缓冲 + 14 种事件类型 + 前端实时面板 + 3 秒轮询 |
| LLM 批量应用 | Profile 卡片一键应用到多 Agent（选择弹窗 + 全选/单选 + 多模型选择） |
| 前端 LOC | 4,726 行 |
| 测试 LOC | 5,645 行 |

---

## 15. 已知问题与改进计划

### P0 — 待修复

| ID | 描述 | 影响 |
|----|------|------|
| ~~BUG-1~~ | ~~websocket.py subscribe 帧解析 KeyError~~ ✅ 已修复 + 测试对齐 | 测试帧格式统一为 `type:"subscribe"` |
| ~~BUG-2~~ | ~~LLM Agent test_chat_with_system_prompt 断言失败~~ ✅ 已修复 | 断言改为 `startswith` 适配技能指令追加 |
| ~~BUG-3~~ | ~~前端 18 个组件渲染测试失败~~ ✅ 已修复 | 根级 vitest.config.ts 配置 jsdom + 测试对齐组件接口 |

### P1 — 近期计划

| ID | 描述 | 优先级理由 |
|----|------|-----------|
| REFACTOR-1 | should_terminate 策略模式拆分 (CC=12→5) | 降低复杂度 |
| REFACTOR-2 | publish 背压逻辑提取 (CC=11→5) | 可维护性 |
| PERF-1 | WebSocket 二进制序列化 (JSON→MessagePack) | 跨进程延迟优化 |
| PERF-2 | Topic Trie 替代线性扫描 | 大量订阅场景性能 |
| TEST-1 | websocket.py 覆盖率 88%→95% | 补齐测试 |
| TEST-2 | 前端组件渲染测试修复（18/47 失败） | 测试可靠性 |

### P2 — 优化项

| ID | 描述 |
|----|------|
| Phase 5 | RL + Evolution 协同优化 + 策略编码为基因组 |
| Phase 6 | 分布式训练 + 端到端加密 + CI/CD |
| IMPL-2 | OAuth2 认证实现 (PKCE + react-router) |

---

## 16. 技能开发指南

在 `skills/` 目录下创建技能，格式与 OpenClaw 完全兼容：

```
skills/
└── my-skill/
    └── SKILL.md
```

SKILL.md 格式：

```markdown
---
name: my-skill
description: What this skill does
metadata: {"openclaw": {"requires": {"bins": ["python"]}}}
---

# Instructions for the agent
Step-by-step instructions here...
```

此技能可直接复制到 OpenClaw 的 `skills/` 目录使用，无需任何修改。

安装方式：
```bash
# 方式一：直接内容
curl -X POST localhost:8000/api/skills -d '{"content": "---\nname: ...\n---\n..."}'

# 方式二：本地路径
curl -X POST localhost:8000/api/skills/install-path -d '{"path": "./skills/my-skill"}'

# 方式三：在线 URL
curl -X POST localhost:8000/api/skills/install-url -d '{"url": "https://github.com/user/skill"}'
```

---

> 本文档为 AgentForge 项目全景文档，覆盖后端、前端、三个算法引擎、Agentic RAG、技能/工具系统、统一监控的完整技术细节。
> 更新时间: 2026-05-19 (v6.3)。
