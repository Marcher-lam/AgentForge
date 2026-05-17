# AgentForge — 项目全景文档

> 版本: 3.0 | 更新: 2026-05-17 | 方法论: STDD
> 前后端 + 三个算法引擎 + Agentic RAG + 技能/工具系统

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
| 知识库 | ChromaDB + fastembed (BAAI/bge-small-en-v1.5, 384维语义 embedding) |
| 聊天架构 | Agentic RAG（LLM 自主决策：知识库检索/联网搜索/直接回答） |
| 技能系统 | SKILL.md 原生格式（OpenClaw / AgentSkills 兼容）+ 在线 URL 安装 |
| 工具系统 | MCP 协议（JSON Schema 校验）+ npm 在线安装 |
| 记忆系统 | 三层（短期 LRU + 长期 SQLite + 向量 NumPy）+ 聊天读写闭环 |
| API 端点 | 49+ REST/WebSocket 路由 |
| 前端测试 | 47 vitest 全部通过 |
| 状态管理 | Jotai atoms |

---

## 2. 技术栈

| 层 | 技术 | 选型理由 |
|----|------|----------|
| Agent 核心 | Python 3.12 + asyncio | 异步原生，Protocol 接口 |
| 消息通信 | asyncio + websockets | 进程内零拷贝 + 跨进程 WebSocket |
| 记忆存储 | SQLite + NumPy vectors | 嵌入式、零运维、语义检索 |
| 知识库 | ChromaDB + fastembed | Per-Agent collection, ONNX 推理, 384维语义 embedding |
| 联网搜索 | DuckDuckGo HTML | 零外部依赖 |
| RL 训练 | NumPy | 轻量数值计算，真实 PPO/DQN |
| 进化计算 | NumPy | 轻量遗传算法 |
| 技能系统 | SKILL.md (OpenClaw 兼容) | 标准格式，生态复用 |
| 工具系统 | MCP 协议 + JSON Schema | 标准化工具注册 |
| 前端 | React 19 + Jotai + Tailwind + Recharts | 响应式状态管理 + 数据可视化 |
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
│   │   ├── algorithms/
│   │   │   ├── dqn/                   # DQN（ReplayBuffer + 目标网络 + e-greedy）
│   │   │   └── ppo/                   # PPO（ActorCritic + GAE + PPO-Clip）
│   │   ├── buffers/                   # ReplayBuffer + RolloutBuffer
│   │   ├── networks/                  # MLP 策略网络
│   │   ├── trainer.py                 # RLTrainer（统一训练入口）
│   │   └── checkpoint.py              # 模型检查点保存/加载
│   ├── skills/
│   │   ├── registry.py                # 技能注册表（SKILL.md 原生格式）
│   │   └── skill_md.py                # SKILL.md 解析/序列化
│   ├── tools/
│   │   ├── registry.py                # 简单工具注册表
│   │   └── mcp_registry.py            # MCP 工具注册表（JSON Schema 校验）
│   ├── memory/
│   │   ├── short_term.py              # 短期记忆（LRU, OrderedDict）
│   │   ├── long_term.py               # 长期记忆（SQLite + TTL）
│   │   ├── vector_memory.py           # 向量记忆（NumPy 余弦相似度）
│   │   ├── knowledge_base.py          # ChromaDB 知识库（fastembed 语义 embedding）
│   │   └── manager.py                 # 三层记忆统一门面
│   ├── server/
│   │   ├── app.py                     # FastAPI 应用（完整后端）
│   │   ├── main.py                    # Uvicorn 启动入口
│   │   └── run.py                     # CLI REPL 入口
│   ├── types/
│   │   ├── config.py                  # AgentConfig / LLMOverride / Evolution / RL / MCP 配置
│   │   ├── errors.py                  # 异常类型层级│   │   └── message.py                 # 消息类型定义
│   └── infra/
│       ├── config.py                  # 全局配置管理
│       ├── logging.py                 # structlog 结构化日志
│       └── shutdown.py                # 优雅关闭（信号处理）
├── skills/                            # 技能目录（SKILL.md 格式）
│   ├── code-review/SKILL.md           # 代码审查技能
│   └── web-search/SKILL.md            # 网络搜索技能
├── frontend/                          # React 前端
│   ├── src/
│   │   ├── App.tsx                    # 主应用（WebSocket + REST + 聊天管理）
│   │   ├── atoms.ts                   # Jotai 状态 atoms
│   │   ├── types/
│   │   │   └── api.ts                 # TypeScript 类型定义
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

用户发送消息后，系统自动执行三阶段讨论流程：

```
┌─────────────────────────────────────────────────────────┐
│                  用户发送消息                              │
├─────────────────────────────────────────────────────────┤
│  Phase 1 — 相关性判定                                    │
│  每个 Agent 通过轻量 LLM 调用自判话题是否与角色相关          │
│  ↓ relevant_agents / spectator_agents 分类               │
├─────────────────────────────────────────────────────────┤
│  Phase 2 — 核心讨论（relevant agents）                    │
│  相关智能体进行多轮深度讨论，可互相 @回应                    │
│  每轮最多 3 轮，每轮 LLM 生成回复                          │
├─────────────────────────────────────────────────────────┤
│  Phase 3 — 旁观者评论（spectator agents）                  │
│  不相关智能体可选择发表跨界观点或 PASS                      │
└─────────────────────────────────────────────────────────┘
```

**实现位置**: `agentforge/server/app.py` → `_handle_group_chat()` 函数

**关键参数**:
- 最大讨论轮数: 3（可配置）
- 相关性判定: 每个 Agent 独立 LLM 调用，判断话题相关性
- 群聊模式: `GROUP_BROADCAST` 会话类型

**记忆接入**: 每个 Agent 在讨论时独立检索自己的记忆上下文，包括短期、长期和向量记忆。

### 4.2 Agentic RAG（知识库 + 联网搜索）

每个 Agent 独立拥有 ChromaDB 知识库，聊天时遵循 Agentic RAG 范式：

```
┌───────────────────────────────────────────────────────┐
│               Agentic RAG 三阶段流程                    │
├───────────────────────────────────────────────────────┤
│  Stage 1 — 记忆检索                                    │
│  从短期/长期/向量三层记忆检索对话历史                      │
│  ↓                                                     │
│  Stage 2 — Agentic 决策（LLM 自主判断）                 │
│  LLM 选择策略:                                         │
│    A. 仅知识库检索                                      │
│    B. 仅联网搜索                                        │
│    C. 知识库 + 联网搜索                                 │
│    D. 直接回答（不需要外部信息）                          │
│  ↓                                                     │
│  Stage 3 — 生成回复                                    │
│  融合 记忆 + 知识库 + 联网搜索 + 讨论记录                │
└───────────────────────────────────────────────────────┘
```

**实现位置**: `agentforge/server/app.py` → `_agent_reply()` 函数

**技术栈**:
- **ChromaDB**: 持久化向量数据库，Per-Agent collection 隔离
- **fastembed**: BAAI/bge-small-en-v1.5, 384维 ONNX 语义 embedding（无需 PyTorch）
- **DuckDuckGo**: HTML 搜索，urllib 实现，零外部依赖

**知识库 API**:

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/agents/{id}/knowledge` | 上传知识文档（texts 数组） |
| GET | `/api/agents/{id}/knowledge/search?q=关键词` | 语义检索知识 |

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
  ├── evolution: EvoConfig          # 独立进化参数
  │   ├── mode: str                 # "personality" | "benchmark"
  │   ├── population_size: int
  │   ├── max_generations: int
  │   ├── mutation_rate: float
  │   └── elite_count: int
  └── rl: RLConfig                  # 独立 RL 训练参数
      ├── algorithm: str            # "PPO" | "DQN" | "REINFORCE"
      ├── total_steps: int
      └── learning_rate: float
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

### 4.6 三层记忆系统

```
┌───────────────────────────────────────────────────┐
│                MemoryManager                      │
│               (统一门面)                           │
├───────────┬───────────────┬───────────────────────┤
│  短期记忆  │   长期记忆     │     向量记忆          │
│  LRU      │   SQLite      │     NumPy             │
│  100条/会话│   支持 TTL    │  余弦相似度检索        │
├───────────┴───────────────┴───────────────────────┤
│  聊天闭环:                                        │
│  1. Agent 回复前 → 检索三层记忆注入 prompt          │
│  2. 用户消息 → 存入短期 + 长期 + 向量               │
│  3. Agent 回复 → 存入短期 + 长期 + 向量             │
│  4. 群聊 → 每个 Agent 独立记忆上下文               │
└───────────────────────────────────────────────────┘
```

**实现位置**:
- 短期: `agentforge/memory/short_term.py`（OrderedDict LRU）
- 长期: `agentforge/memory/long_term.py`（SQLite + TTL 过期）
- 向量: `agentforge/memory/vector_memory.py`（NumPy 余弦相似度）
- 管理器: `agentforge/memory/manager.py`（统一 store/search 接口）

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

**训练流程**:
```
Agent 创建 → 配置 RL 参数 → POST /api/agents/{id}/rl/start
→ 后台异步训练 → WebSocket 广播进度 → 训练完成保存 checkpoint
→ GET /api/agents/{id}/rl/runs 查看历史
```

**实现位置**: `agentforge/rlforge/`

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
| POST | `/api/agents/{id}/knowledge` | 上传知识文档（texts 数组） |
| GET | `/api/agents/{id}/knowledge/search` | 语义检索知识（?q=关键词&top_k=5） |

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

---

## 6. 前端页面

| Tab | 功能描述 |
|-----|----------|
| **对话** | 会话列表（单聊/群聊切换）+ 消息面板 + WebSocket 实时通信。支持删除会话（带确认）、导出聊天记录（JSON 下载）、群聊多 Agent 讨论 |
| **智能体** | 卡片式管理。创建时一步配齐 LLM Provider/Model + 技能 + MCP + 进化参数 + RL 参数。渐变头像、能力徽章、per-agent 配置。点击跳转对话 |
| **监控** | 消息流监控面板。统计条（消息总数/Agent 分布）、类型筛选、自动滚动切换 |
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
| `LLM_SYSTEM_PROMPT` | `You are a helpful AI assistant.` | 默认智能体提示词 |

---

## 8. 快速启动

```bash
# 1. 安装后端依赖
pip install -e ".[dev,llm]"

# 2. 安装前端依赖
cd frontend && npm install && cd ..

# 3. 启动后端（使用本地模型示例）
LLM_PROVIDER=openai \
LLM_MODEL='VLM/Qwen3.5-9B-MLX-4bit' \
LLM_API_KEY=EMPTY \
LLM_BASE_URL='http://127.0.0.1:8888/v1' \
uvicorn agentforge.server.main:create_and_run --host 0.0.0.0 --port 8000 --factory

# 4. 启动前端（另一个终端）
cd frontend && npx vite --host 0.0.0.0 --port 5173

# 5. 打开浏览器
open http://localhost:5173
```

---

## 9. 测试

```bash
# 前端测试
cd frontend && npx vitest run

# 前端类型检查
cd frontend && npx tsc --noEmit

# 后端测试
python -m pytest tests/ -v
```

---

## 10. 架构特征

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
| RAG 闭环 | Per-Agent ChromaDB + fastembed + 联网搜索 + LLM 自主决策 |
| 数据可视化 | Recharts 双 Y 轴图表 + LTTB 降采样 + 进化树 SVG + 热力图 |

---

## 11. 关键数据结构

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
    name: str
    system_prompt: str
    llm: LLMOverride | None = None
    tool_ids: list[str] = field(default_factory=list)
    skill_ids: list[str] = field(default_factory=list)
    mcp_server_ids: list[str] = field(default_factory=list)
    evolution: EvoConfig | None = None
    rl: RLConfig | None = None

@dataclass
class LLMOverride:
    provider_profile: str | None = None  # 引用 LLM Profile 卡片
    model: str | None = None
    temperature: float | None = None
    api_key: str | None = None
    base_url: str | None = None
    provider: str | None = None

@dataclass
class EvoConfig:
    mode: str = "personality"        # "personality" | "benchmark"
    population_size: int = 20
    max_generations: int = 50
    mutation_rate: float = 0.1
    elite_count: int = 2
    crossover_rate: float = 0.8

@dataclass
class RLConfig:
    algorithm: str = "PPO"           # "PPO" | "DQN" | "REINFORCE"
    total_steps: int = 5000
    learning_rate: float = 0.001
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

## 12. 里程碑状态

| Phase | 描述 | 状态 |
|-------|------|------|
| Phase 1 | 核心骨架（Agent 状态机 + 消息总线 + 基础设施） | ✅ 完成 |
| Phase 2 | 能力层（MCP 工具 + SKILL.md 技能 + 三层记忆 + Per-Agent 配置） | ✅ 完成 |
| Phase 3 | 算法引擎（PPO/DQN/REINFORCE + 遗传算法 + 人格优化） | ✅ 完成 |
| Phase 4 | 可视化 & UX（仪表盘 + 监控 + 设置 + 聊天管理 + RAG） | ✅ 完成 |
| Phase 5 | 协同进化（RL + Evolution 协同 + Pareto 优化） | 📋 待开发 |
| Phase 6 | 生产就绪（分布式训练 + 端到端加密 + CI/CD） | 📋 待开发 |

---

## 13. 质量度量

| 维度 | 数据 |
|------|------|
| 后端导入 | 全模块零错误 |
| 前端编译 | TypeScript 零错误 |
| 前端测试 | 47 vitest 全部通过 |
| API 端点 | 49+ REST/WebSocket 路由 |
| 总代码覆盖 | 93% |
| 总语句数 | 1,362 |
| 测试总数 | 269（228 unit + 16 integration + 25 e2e） |
| APP Mass | 0.278 CC/SLOC（健康 < 0.3） |
| 平均 CC | 2.4（Grade A） |

---

## 14. 已知问题与改进计划

### P0 — 待修复

| ID | 描述 | 影响 |
|----|------|------|
| BUG-1 | ~~websocket.py subscribe 帧解析 KeyError~~ ✅ 已修复 | 统一帧格式 `type:"subscribe"` + 健壮解析 |

### P1 — 近期计划

| ID | 描述 | 优先级理由 |
|----|------|-----------|
| REFACTOR-1 | should_terminate 策略模式拆分 (CC=12→5) | 降低复杂度 |
| REFACTOR-2 | publish 背压逻辑提取 (CC=11→5) | 可维护性 |
| PERF-1 | WebSocket 二进制序列化 (JSON→MessagePack) | 跨进程延迟优化 |
| PERF-2 | Topic Trie 替代线性扫描 | 大量订阅场景性能 |
| TEST-1 | websocket.py 覆盖率 88%→95% | 补齐测试 |

### P2 — 优化项

| ID | 描述 |
|----|------|
| Phase 5 | RL + Evolution 协同优化 + 策略编码为基因组 |
| Phase 6 | 分布式训练 + 端到端加密 + CI/CD |
| IMPL-2 | OAuth2 认证实现 (PKCE + react-router) |

---

## 15. 技能开发指南

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

> 本文档为 AgentForge 项目全景文档，覆盖后端、前端、三个算法引擎、Agentic RAG、技能/工具系统的完整技术细节。
> 更新时间: 2026-05-17 (v3.0)。
