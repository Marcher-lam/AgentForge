# AgentForge — 多智能体协作平台

> 进化强化学习驱动的多 Agent 协作框架，支持智能体自主讨论、提示词进化优化和策略训练。

## 技术栈

| 层 | 技术 |
|---|------|
| 后端 | Python 3.12+ / FastAPI / WebSocket / asyncio |
| 前端 | React 19 + TypeScript + Vite + TailwindCSS + Recharts |
| LLM | OpenAI 兼容 API（支持本地模型 / Anthropic / Ollama） |
| 进化 | 遗传算法（锦标赛选择 / SBX交叉 / 高斯变异） |
| RL | PPO / DQN / REINFORCE（NumPy 实现，真实训练） |
| 技能 | SKILL.md 格式（OpenClaw / AgentSkills 兼容） |
| 工具 | MCP 协议（JSON Schema 校验） |
| 状态管理 | Jotai atoms |
| 测试 | Vitest（前端）/ pytest（后端） |

## 快速启动

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

## 项目结构

```
AgentForge/
├── agentforge/                    # Python 后端
│   ├── agent/
│   │   ├── base.py                # AgentBase ABC（状态机：init→run→stop→destroy）
│   │   ├── events.py              # Agent 事件定义
│   │   └── llm_agent.py           # LLMAgent（LLM + 工具 + 技能集成）
│   ├── bus/
│   │   ├── inprocess.py           # 进程内消息总线（pub/sub）
│   │   ├── websocket.py           # WebSocket 消息总线（重连恢复）
│   │   └── topic_matcher.py       # Topic 匹配器
│   ├── llm/
│   │   ├── protocol.py            # LLMBackend Protocol + 数据类型
│   │   ├── openai_backend.py      # OpenAI 兼容后端
│   │   ├── anthropic_backend.py   # Anthropic Claude 后端
│   │   └── ollama_backend.py      # Ollama 本地模型后端
│   ├── evoforge/                  # 遗传算法引擎
│   │   ├── engine/
│   │   │   ├── evolution.py       # EvolutionEngine（世代循环）
│   │   │   ├── population.py      # Population + Individual（谱系追踪）
│   │   │   ├── callbacks.py       # 回调系统 + 统计收集
│   │   │   └── termination.py     # 终止条件（含多样性检测）
│   │   ├── genomes/               # 基因组：RealGenome / BinaryGenome / TreeGenome
│   │   ├── operators/             # 算子：选择/交叉/变异/替换
│   │   └── fitness/               # 适应度函数 + 多目标 + 异步包装
│   ├── rlforge/                   # 强化学习引擎（真实训练）
│   │   ├── environment.py         # CartPole 风格环境（step/reset API）
│   │   ├── policy.py              # 2层 MLP 策略网络 + Adam 优化器
│   │   ├── trainer.py             # 训练分发器（REINFORCE/PPO/DQN）
│   │   ├── ppo.py                 # PPO（ActorCritic + GAE + PPO-Clip + mini-batch）
│   │   ├── dqn.py                 # DQN（ReplayBuffer + 目标网络 + ε-greedy）
│   │   ├── buffer.py              # 经验回放缓冲区
│   │   └── checkpoint.py          # 模型检查点保存/加载
│   ├── skills/
│   │   ├── registry.py            # 技能注册表（SKILL.md 原生格式）
│   │   └── skill_md.py            # SKILL.md 解析/序列化（OpenClaw 兼容）
│   ├── tools/
│   │   ├── registry.py            # 简单工具注册表
│   │   └── mcp_registry.py        # MCP 工具注册表（JSON Schema 校验）
│   ├── memory/
│   │   ├── short_term.py          # 短期记忆
│   │   ├── long_term.py           # 长期记忆（SQLite + TTL）
│   │   ├── vector_memory.py       # 向量记忆（NumPy 余弦相似度）
│   │   └── manager.py             # 三层记忆管理器
│   ├── server/
│   │   ├── app.py                 # FastAPI 应用（三阶段讨论 + 完整 CRUD）
│   │   ├── main.py                # Uvicorn 启动入口
│   │   └── run.py                 # CLI REPL 入口
│   ├── types/
│   │   ├── config.py              # AgentConfig / LLMOverride / Evolution / RL / MCP 配置
│   │   ├── errors.py              # 异常类型层级
│   │   └── message.py             # 消息类型定义
│   └── infra/
│       ├── config.py              # 配置管理
│       ├── logging.py             # 结构化日志
│       └── shutdown.py            # 优雅关闭
├── skills/                        # 技能目录（SKILL.md 格式，与 OpenClaw 通用）
│   ├── code-review/SKILL.md       # 代码审查技能
│   └── web-search/SKILL.md        # 网络搜索技能
├── frontend/                      # React 前端
│   └── src/
│       ├── App.tsx                # 主应用（WebSocket + REST 轮询）
│       ├── atoms.ts               # Jotai 状态 atoms
│       ├── components/
│       │   ├── chat/              # 对话面板 + 输入框 + 群聊/删除/导出
│       │   ├── grid/              # 智能体卡片管理（创建时一步配齐 LLM/技能/MCP/进化/RL）
│       │   ├── dashboard/         # 仪表盘（Agent 卡片网格 + 训练记录左右分栏 + 图表放大 + 日志表格）
│       │   ├── monitor/           # 消息监控面板（统计条/类型筛选/自动滚动）
│       │   └── settings/          # 设置页（模型配置/MCP服务/技能管理 + 在线安装）
│       ├── utils/lttb.ts          # LTTB 降采样算法
│       └── types/api.ts           # API 类型定义（含 AgentConfig/LLMProfile/EvoRun/RLRun/MCPServer/Skill）
├── tests/                         # 后端测试
└── pyproject.toml
```

## 核心功能

### 0. 进化 & RL 如何影响 Agent（闭环机制）

```
进化引擎（EvoForge）                    RL 引擎（RLForge）
─────────────────                      ─────────────────
优化 Agent 的"人格"                     优化 Agent 的"策略参数"
                                       
10 维基因 → sigmoid → 人格特质           训练结果 → 提取策略信号
（创造力/同理心/幽默感/...）             （奖励方差/loss/算法类型）
        ↓                                       ↓
写回 system_prompt                      写回 system_prompt
[进化优化人格] 标签                      [RL策略优化] 标签
                                        + 更新 temperature/max_tokens
        ↓                                       ↓
LLM 回复时体现人格特质                   LLM 回复时使用优化后的参数
```

两者可同时使用：进化定"性格"，RL 调"策略"。

### 0.5 预设 AI 专家团队（启动自动创建）

系统启动时自动创建 9 个 AI 专家 Agent + 一个"AI 专家团队"群聊会话：

| # | 角色 | 专长领域 | RL 算法 | 进化代数 |
|---|------|----------|---------|----------|
| 1 | 程序员 | 全栈工程、系统设计、代码质量 | PPO 300步 | 30代 |
| 2 | 哲学家 | 存在主义、伦理困境、技术哲学 | REINFORCE 500步 | 40代 |
| 3 | 数学家 | 线性代数、概率论、形式化推导 | DQN 500步 | 50代 |
| 4 | 机器学习算法工程师 | XGBoost、特征工程、集成学习 | PPO 400步 | 35代 |
| 5 | 深度学习算法工程师 | Transformer、PyTorch、CV/NLP | PPO 500步 | 40代 |
| 6 | 强化学习算法工程师 | PPO/DQN/SAC、奖励设计 | PPO 1000步 | 50代 |
| 7 | C++工程师 | C++17/20、并发、零成本抽象 | DQN 400步 | 30代 |
| 8 | 大模型引擎推理工程师 | KV Cache、量化、并行推理 | PPO 500步 | 35代 |
| 9 | 前端工程师 | React 19、TypeScript、性能优化 | PPO 300步 | 30代 |

每个角色有独立的 system_prompt、进化配置和 RL 配置，可在前端"智能体"页面查看和修改。

### 1. 多智能体三阶段讨论引擎

用户发送消息后，系统自动执行三阶段流程：

1. **Phase 1 — 相关性判定**：每个智能体通过轻量 LLM 调用自判话题是否与自己的角色相关
2. **Phase 2 — 核心讨论**：相关智能体进行多轮深度讨论，可互相 @回应
3. **Phase 3 — 旁观者评论**：不相关智能体可选择发表跨界观点或 PASS

```
用户：「Go和Rust哪个适合写网关？」
[系统] 程序员 将参与讨论；产品经理, 设计师 旁观
[程序员] @产品经理 从工程角度分析 GC 对长连接的影响...
[产品经理] 补充视角：将技术选型转化为商业资产决策...
[设计师] 从视觉叙事角度看，eBPF 方案像抽象表现主义...
```

### 2. Per-Agent 独立配置

每个智能体根据自身角色独立配置能力：

```
AgentConfig:
  ├── llm: LLMOverride        # 独立的模型/温度/Key 配置
  ├── tool_ids: [...]         # 从全局工具池选择的工具
  ├── skill_ids: [...]        # 从全局技能池选择的技能
  ├── mcp_server_ids: [...]   # 关联的 MCP 服务器
  ├── evolution: EvoConfig    # 独立的进化参数
  └── rl: RLConfig            # 独立的 RL 训练参数
```

**三层架构**：全局注册表 → AgentConfig 筛选 → 运行时接线

### 3. SKILL.md 技能系统（OpenClaw 兼容）

技能使用 **SKILL.md 标准格式**，与 OpenClaw / AgentSkills 完全兼容：
- 同一个技能目录在 AgentForge 和 OpenClaw 中都能直接使用
- YAML frontmatter（name / description / metadata）+ Markdown 指令体
- 支持 OpenClaw 门控机制（requires.bins / requires.env / os）
- 技能指令自动注入到 Agent 的系统提示中

```bash
# 安装技能（SKILL.md 内容直接 POST）
curl -X POST localhost:8000/api/skills -d '{"content": "---\nname: my-skill\n...\n---\n..."}'

# 从路径安装
curl -X POST localhost:8000/api/skills/install-path -d '{"path": "./skills/code-review"}'

# 从在线 URL 安装（支持 GitHub 仓库或 raw 文件链接）
curl -X POST localhost:8000/api/skills/install-url -d '{"url": "https://github.com/user/skill-repo"}'

# 导出 SKILL.md 原文（可直接复制到 OpenClaw）
curl localhost:8000/api/skills/code-review | jq .raw
```

### 4. MCP 工具管理

- MCP 协议工具注册表（JSON Schema 参数校验）
- 全局工具池 + 按 Agent 筛选接线
- MCP 服务器注册（stdio / url 连接方式）
- 在线安装：输入 npm 包名自动配置为 stdio 模式（`npx -y <package>`）

```bash
# 从 npm 在线安装 MCP 服务器
curl -X POST localhost:8000/api/mcp-servers/install-online \
  -d '{"package": "@modelcontextprotocol/server-filesystem", "args": "/path/to/dir"}'
```

### 5. 进化引擎（EvoForge）

- **智能体人格优化模式**：10 维人格基因（sigmoid → [0,1]），适应度 = 平衡性 + 多样性 - 极端值
- **进化结果闭环**：最优基因组自动映射为创造力/同理心/幽默感等人格特质，写回 Agent 的 system_prompt
- **经典基准模式**：球面函数优化
- 选择：锦标赛 / 轮盘赌 / 精英保留
- 交叉：单点 / 多点 / 均匀 / SBX / 子树交换
- 变异：高斯 / 均匀 / 位翻转 / 子树变异
- 种群谱系追踪 + **进化树 SVG 可视化**（红→绿颜色映射适应度）
- 基因热力图 + LTTB 降采样大数据集

### 6. 强化学习引擎（RLForge）

**真实训练**（NumPy 实现），非模拟：

| 算法 | 实现 |
|------|------|
| PPO | ActorCritic + GAE + PPO-Clip + mini-batch epochs + entropy bonus |
| DQN | ReplayBuffer + 目标网络 + ε-greedy 衰减 |
| REINFORCE | 简单策略梯度 + 价值基线 |

- CartPole 风格环境（4维状态，2动作）
- 2层 MLP 策略网络 + Adam 优化器
- 训练后自动保存 checkpoint（checkpoints/ 目录）
- **RL 结果写回 Agent**（与进化引擎闭环一致）：
  - 训练完成自动提取策略信号（奖励方差→temperature，loss→max_tokens，算法→风格描述）
  - 写入 `[RL策略优化]` 标签到 system_prompt + 更新 config.llm 参数
  - `_agent_reply` 使用 Agent 级 temperature（非硬编码）

## 记忆系统

三层记忆架构，已接入 Agent 聊天流程：

| 层 | 存储 | 用途 |
|---|------|------|
| 短期 | 内存 LRU（100 条/会话） | 最近对话上下文 |
| 长期 | SQLite（支持 TTL） | 跨会话持久记忆 |
| 向量 | fastembed 语义 embedding (384维) | 语义检索 |

- Agent 回复前检索相关记忆注入 prompt
- 用户消息和 Agent 回复自动存入短期+长期记忆
- 群聊中每个 Agent 独立记忆上下文

## Agentic RAG（知识库 + 联网搜索）

每个 Agent 独立拥有 ChromaDB 知识库，聊天时遵循 Agentic RAG 范式：

**三阶段流程：**
1. **记忆检索** — 从短期/长期/向量记忆检索对话历史
2. **Agentic 决策** — LLM 自主判断是否需要检索知识库或联网搜索
3. **生成回复** — 融合记忆+知识库+联网搜索+讨论记录

**技术栈：**
- ChromaDB 持久化存储，Per-Agent collection 隔离
- fastembed (BAAI/bge-small-en-v1.5) 384维真实语义 embedding
- DuckDuckGo 联网搜索（零外部依赖）

```bash
# 上传知识到 Agent
curl -X POST localhost:8000/api/agents/{id}/knowledge \
  -d '{"texts":["知识文档1","知识文档2"]}'

# 检索知识
curl "localhost:8000/api/agents/{id}/knowledge/search?q=关键词"
```
- 实时训练曲线：奖励 + 损失 + 对比图（Recharts 双 Y 轴）

## API 端点

### 智能体管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/agents` | 列出所有智能体 |
| POST | `/api/agents` | 创建智能体（含完整 config: LLM/技能/MCP/进化/RL，一步配齐） |
| GET | `/api/agents/{id}` | 获取智能体详情（含接线工具、技能、配置） |
| PATCH | `/api/agents/{id}` | 热更新智能体配置 |
| DELETE | `/api/agents/{id}` | 删除智能体 |
| POST | `/api/agents/{id}/evolution/start` | 启动 per-agent 进化 |
| POST | `/api/agents/{id}/rl/start` | 启动 per-agent RL 训练 |
| GET | `/api/agents/{id}/evolution/runs` | 获取 Agent 进化训练历史 |
| GET | `/api/agents/{id}/rl/runs` | 获取 Agent RL 训练历史 |

### 工具管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/tools` | 列出全局工具池 |
| POST | `/api/tools` | 注册工具（name, schema, description） |
| DELETE | `/api/tools/{name}` | 注销工具 |

### 技能管理（SKILL.md 格式）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/skills` | 列出已安装技能 |
| POST | `/api/skills` | 安装技能（提供 SKILL.md 内容） |
| POST | `/api/skills/install-path` | 从路径安装技能 |
| POST | `/api/skills/install-url` | 从在线 URL 安装技能（支持 GitHub） |
| GET | `/api/skills/{name}` | 获取技能详情（含 SKILL.md 原文） |
| DELETE | `/api/skills/{name}` | 卸载技能 |

### MCP 服务器管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/mcp-servers` | 列出已注册 MCP 服务器 |
| POST | `/api/mcp-servers` | 注册 MCP 服务器 |
| POST | `/api/mcp-servers/install-online` | 从 npm 在线安装 MCP 服务器 |
| DELETE | `/api/mcp-servers/{id}` | 注销 MCP 服务器 |

### 会话 & 通信

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/sessions` | 列出会话 |
| POST | `/api/sessions` | 创建会话（单聊/群聊，含 agent_ids 和 type） |
| GET | `/api/sessions/{id}/messages` | 获取消息历史 |
| DELETE | `/api/sessions/{id}` | 删除会话及其消息 |
| DELETE | `/api/sessions/{id}/messages/{mid}` | 删除单条消息 |
| GET | `/api/sessions/{id}/export` | 导出聊天记录（JSON，含会话/消息/Agent 信息） |
| GET/PUT | `/api/settings` | 读写全局 LLM 配置 |
| WS | `/ws` | WebSocket 实时通信 |

### 进化 & RL

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/evolution/start` | 启动进化引擎 |
| GET | `/api/evolution/{id}` | 查询进化状态（含进化树 + 热力图 + 逐代日志） |
| POST | `/api/evolution/{id}/cancel` | 取消进化 |
| POST | `/api/rl/start` | 启动 RL 训练 |
| GET | `/api/rl/{id}` | 查询训练状态（含逐步日志） |
| POST | `/api/rl/{id}/cancel` | 取消训练 |

## 测试

```bash
# 前端测试
cd frontend && npx vitest run

# 后端测试
python -m pytest tests/ -v

# 类型检查
cd frontend && npx tsc --noEmit
```

## 前端页面

| Tab | 功能 |
|-----|------|
| 对话 | 会话列表（单聊/群聊切换 + 删除确认 + 导出记录）+ 消息面板 + WebSocket 实时通信 |
| 智能体 | 卡片式管理（创建时一步配齐 LLM/技能/MCP/进化/RL，渐变头像/能力徽章/per-agent 配置），点击跳转对话 |
| 监控 | 消息流监控面板（统计条/类型筛选/自动滚动切换） |
| 仪表盘 | Agent 卡片网格 → 点击弹出训练记录（进化/RL 双 Tab）→ 左日志右图表分栏 + 每图放大按钮 |
| 设置 | 模型配置（多 Provider 卡片）+ MCP 服务（手动/在线 npm 安装）+ 技能管理（在线 URL/本地路径/文本安装） |

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `LLM_PROVIDER` | `openai` | LLM 服务商 |
| `LLM_MODEL` | - | 模型名称 |
| `LLM_API_KEY` | - | API 密钥 |
| `LLM_BASE_URL` | - | 自定义 API 地址 |
| `LLM_SYSTEM_PROMPT` | `You are a helpful AI assistant.` | 默认智能体提示词 |

## 技能开发

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
