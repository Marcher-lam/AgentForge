# EvoRL User Acceptance Test (UAT) Scripts

> Generated: 2026-05-16 | Updated: 2026-05-18 | Scope: agent-core, evolution-engine, rl-engine, frontend-ui, coevolution, streaming, persistence
> Total Scenarios: 50 | Estimated Duration: 45 min

---

## 1. Agent-Core (agentforge)

### 1.1 Agent Lifecycle

**UAT-AC-01: Agent 完整生命周期**
- **Setup**: 启动 EvoRL REPL `python -m pytest tests/e2e/test_agent_lifecycle_e2e.py -v`
- **Steps**:
  1. Given 一个新创建的 Agent (state=CREATED)
  2. When 调用 `agent.init()`
  3. Then state 变为 INITIALIZED
  4. When 调用 `agent.run()`
  5. Then state 变为 RUNNING
  6. When 调用 `agent.stop()`
  7. Then state 变为 STOPPED
  8. When 调用 `agent.destroy()`
  9. Then state 变为 DESTROYED (终态)
- **Expected**: 状态按 CREATED→INITIALIZED→RUNNING→STOPPED→DESTROYED 顺序流转
- **Verify**: `✓ 全部 5 次状态转换成功`

**UAT-AC-02: 非法状态转换被拒绝**
- **Setup**: 同上
- **Steps**:
  1. Given 一个 CREATED 状态的 Agent
  2. When 尝试调用 `agent.run()` (跳过 init)
  3. Then 抛出 InvalidStateTransition 异常
- **Expected**: 不允许 CREATED→RUNNING 跳转
- **Verify**: `✓ 异常消息包含当前状态和目标状态`

**UAT-AC-03: 并发状态转换竞争**
- **Steps**:
  1. Given 一个 INITIALIZED 的 Agent
  2. When 两个协程同时调用 `agent.run()`
  3. Then 只有一个成功，另一个抛异常
- **Expected**: 状态转换是原子的
- **Verify**: `✓ 仅一个协程获得 RUNNING 状态`

### 1.2 Message Bus (InProcess)

**UAT-AC-04: 基本发布/订阅**
- **Steps**:
  1. Given 一个 InProcessMessageBus
  2. When 订阅 "agent.status" topic 并发布消息
  3. Then 订阅者收到消息
- **Expected**: 消息内容与发布的一致 (topic, payload, sender_id)
- **Verify**: `✓ 收到消息数量和内容匹配`

**UAT-AC-05: 通配符 topic 匹配**
- **Steps**:
  1. When 订阅 "agent.*" topic
  2. And 发布到 "agent.status" 和 "agent.heartbeat"
  3. Then 两条消息都收到
  4. And 发布到 "system.status" 不被接收
- **Expected**: `*` 匹配单层, `**` 匹配多层
- **Verify**: `✓ 通配符过滤正确`

**UAT-AC-06: RPC 请求/响应**
- **Steps**:
  1. Given 注册 responder 在 "rpc.query" topic
  2. When 调用 `bus.request("rpc.query", msg, timeout=5.0)`
  3. Then 在 5 秒内收到响应
- **Expected**: 超时未响应则抛 RpcTimeout
- **Verify**: `✓ 正常响应 < 5s, 超时场景 > 5s 抛异常`

**UAT-AC-07: 消息可靠投递 (无丢失)**
- **Steps**:
  1. Given 一个慢消费者 (handler sleep 0.1s)
  2. When 快速发送 10 条消息
  3. Then 全部 10 条消息被接收 (0% 丢失)
- **Expected**: 背压机制保证不丢消息
- **Verify**: `✓ 10/10 消息送达`

### 1.3 WebSocket Bus

**UAT-AC-08: 跨进程发布/订阅**
- **Steps**:
  1. Given 启动 WebSocket server (port 8080)
  2. When 客户端连接并订阅 "ws.test"
  3. And 另一客户端发布消息到 "ws.test"
  4. Then 订阅客户端收到消息
- **Expected**: 跨进程通信正常
- **Verify**: `✓ 跨进程消息一致`

**UAT-AC-09: Subscribe 帧不崩溃 (回归测试)**
- **Steps**:
  1. Given WebSocket server 运行中
  2. When 客户端发送 `{"subscribe": true, "topic": "test"}` (无 message 字段)
  3. Then 服务端不崩溃, 正常注册订阅
- **Expected**: subscribe 帧不再触发 KeyError
- **Verify**: `✓ 订阅成功, 服务端 _client_subs 包含 sub_id`

---

## 2. Evolution-Engine (evoforge)

### 2.1 基本进化流程

**UAT-EV-01: OneMax 优化收敛**
- **Steps**:
  1. Given Population(N=50, genome=BinaryGenome, length=20)
  2. When 运行进化 50 代, 适应度=OneMax
  3. Then 最优个体的适应度 ≥ 18 (目标20)
- **Expected**: 二进制基因组趋向全1
- **Verify**: `python -m pytest tests/integration/test_evoforge_integration.py::TestOneMax -v`

**UAT-EV-02: Sphere 函数优化**
- **Steps**:
  1. Given Population(N=100, genome=RealGenome, dim=10)
  2. When 运行进化 100 代, 适应度=Sphere
  3. Then 最优适应度比初始改善 > 50%
- **Expected**: 连续优化收敛
- **Verify**: `python -m pytest tests/integration/test_evoforge_integration.py::TestSphere -v`

**UAT-EV-03: 种子可复现性**
- **Steps**:
  1. Given seed=42
  2. When 运行两次进化 (相同参数)
  3. Then 两次的最优适应度完全一致
- **Expected**: 确定性进化
- **Verify**: `python -m pytest tests/integration/test_evoforge_integration.py::TestReproducibility -v`

### 2.2 终止策略

**UAT-EV-04: 适应度阈值终止**
- **Steps**:
  1. Given 终止条件: fitness_threshold=19.0
  2. 当运行 OneMax 进化
  3. 那么在适应度达到 19 时自动停止
  4. 且 `engine.termination_reason == "FITNESS_THRESHOLD"`
- **Verify**: `✓ generation < max_generations 提前停止`

**UAT-EV-05: 最大代数终止**
- **Steps**:
  1. Given 终止条件: max_generations=10
  2. 当运行进化
  3. 那么在第 10 代后停止
  4. 且 `engine.generation == 10`
- **Verify**: `✓ 严格在第10代停止`

### 2.3 适应度函数

**UAT-EV-06: 简单适应度评估**
- **Steps**:
  1. 当使用 SimpleFitness(func=sum)
  2. 则评估 [1,2,3] 返回 6.0
- **Verify**: `✓ 结果正确`

**UAT-EV-07: 多目标加权**
- **Steps**:
  1. 当使用 WeightedMultiObjective(weights=[0.6, 0.4])
  2. 则评估 [10.0, 20.0] 返回 14.0
- **Verify**: `✓ 0.6×10 + 0.4×20 = 14.0`

**UAT-EV-08: 边界裁剪**
- **Steps**:
  1. 当使用 BoundaryClip(bounds=[(0,1)])
  2. 且基因值 [−0.5, 1.5]
  3. 则裁剪为 [0.0, 1.0]
- **Verify**: `✓ 基因值在边界内`

### 2.4 基因组操作

**UAT-EV-09: RealGenome 交叉/变异**
- **Steps**:
  1. 给定两个 RealGenome 父体
  2. 当 uniform_crossover
  3. 则子代基因来自两个父体
  4. 当 gaussian_mutation(sigma=0.1)
  5. 则子代基因小幅变化
- **Verify**: `✓ 子代有效, 变异幅度合理`

**UAT-EV-10: BinaryGenome 操作**
- **Steps**:
  1. 给定两个 BinaryGenome 父体
  2. 当 single_point_crossover
  3. 则子代基因在交叉点前后来自不同父体
  4. 当 bitflip_mutation(rate=0.1)
  5. 则约 10% 的 bit 被翻转
- **Verify**: `✓ 交叉和变异正确`

**UAT-EV-11: TreeGenome 表达式评估**
- **Steps**:
  1. 给定 TreeGenome 代表 "x + 2"
  2. 当 evaluate({x: 3})
  3. 则结果 == 5.0
- **Verify**: `✓ 表达式求值正确`

---

## 3. RL-Engine (rlforge)

### 3.1 DQN 训练

**UAT-RL-01: DQN CartPole 训练收敛**
- **Steps**:
  1. 给定 DQNTrainer + CartPole-v1 环境
  2. 当训练 1000 步
  3. 则平均回报比初始改善
- **Verify**: `python -m pytest tests/e2e/test_cartpole_train_e2e.py::TestDQNCartPoleE2E -v`

**UAT-RL-02: DQN 配置验证**
- **Steps**:
  1. 给定 DQNConfig(lr=0.001, gamma=0.99, epsilon=0.1)
  2. 则配置正确加载
  3. 且边界值被拒绝 (lr ≤ 0, gamma > 1)
- **Verify**: `✓ 有效配置通过, 无效配置抛异常`

**UAT-RL-03: DQN Checkpoint 保存/加载**
- **Steps**:
  1. 给定训练过的 DQNTrainer
  2. 当 save_checkpoint(path)
  3. And 创建新 trainer 并加载 checkpoint
  4. Then 模型权重一致
- **Verify**: `✓ 保存/加载 roundtrip 正确`

### 3.2 PPO 训练

**UAT-RL-04: PPO CartPole 训练收敛**
- **Steps**:
  1. 给定 PPOTrainer + CartPole-v1
  2. 当训练 500 步
  3. 则平均回报改善
- **Verify**: `python -m pytest tests/e2e/test_cartpole_train_e2e.py::TestPPOCartPoleE2E -v`

**UAT-RL-05: PPO GAE 计算**
- **Steps**:
  1. 给定 transitions + rewards + values
  2. 当 compute_gae(gamma=0.99, lambda=0.95)
  3. 则 advantage 值合理 (无 NaN/Inf)
- **Verify**: `✓ GAE 输出形状和值域正确`

### 3.3 Buffer 操作

**UAT-RL-06: ReplayBuffer 采样**
- **Steps**:
  1. 给定 ReplayBuffer(capacity=100)
  2. 当添加 150 个 transition
  3. 则 buffer 大小 == 100 (FIFO 淘汰)
  4. 当采样 batch_size=32
  5. 则返回 32 个随机 transition
- **Verify**: `✓ FIFO 淘汰和随机采样正确`

**UAT-RL-07: RolloutBuffer GAE**
- **Steps**:
  1. 给定 RolloutBuffer
  2. 当添加完整 episode 的 transitions
  3. 则 compute_returns_and_advantages() 计算正确
- **Verify**: `✓ returns 和 advantages 无 NaN`

### 3.4 网络和类型

**UAT-RL-08: MLP 前向传播**
- **Steps**:
  1. 给定 MLP(layers=[64, 32], output_dim=4)
  2. 当输入 shape=(batch, state_dim)
  3. 则输出 shape=(batch, 4)
- **Verify**: `✓ 输出维度正确`

**UAT-RL-09: Transition 数据结构**
- **Steps**:
  1. 当创建 Transition(state, action, reward, next_state, done)
  2. 则字段完整可访问
  3. 且 frozen=True 不可修改
- **Verify**: `✓ 数据完整性和不可变性`

---

## 4. Frontend-UI

### 4.1 Chat Panel

**UAT-FE-01: 发送消息**
- **前置条件**: 前端 dev server 运行中 (`npm run dev`)
- **步骤**:
  1. 打开 Chat 页面
  2. 在输入框输入 "Hello Agent"
  3. 点击发送按钮 (或按 Enter)
  4. Then 消息出现在聊天窗口
- **预期**: 消息气泡显示 "Hello Agent", 输入框清空
- **验证**: `✓ 消息可见, 输入框为空`

**UAT-FE-02: 接收 Agent 回复**
- **步骤**:
  1. Given Agent 已连接
  2. When Agent 回复消息
  3. Then 回复出现在聊天窗口
  4. And 回复有 Agent 标识
- **预期**: 区分用户消息和 Agent 回复
- **验证**: `✓ 消息有不同颜色/头像`

**UAT-FE-03: WebSocket 断线提示**
- **步骤**:
  1. Given WebSocket 已连接
  2. When 断开网络连接
  3. Then 显示断线提示
  4. When 恢复连接
  5. Then 提示消失, 自动重连
- **预期**: 用户有网络状态感知
- **验证**: `✓ 断线/重连 UI 反馈正确`

**UAT-FE-03a: 群聊创建**
- **步骤**:
  1. 点击 "+ 新建" 按钮
  2. 切换到 "群聊" 模式
  3. 选择 2 个或更多智能体
  4. 点击 "创建群聊"
  5. Then 新会话出现在列表，带紫色 "群聊" 标签
- **预期**: 群聊中多 Agent 自动进行三阶段讨论
- **验证**: `✓ 群聊标签正确显示，多 Agent 多轮讨论正常`

**UAT-FE-03b: 删除对话记录**
- **步骤**:
  1. 鼠标悬停在会话列表中某条会话上
  2. 点击删除图标（垃圾桶）
  3. 显示 "确认"/"取消" 按钮
  4. 点击 "确认"
  5. Then 会话从列表中消失
- **预期**: 会话及其消息被完全删除
- **验证**: `✓ 会话不再出现在列表中`

**UAT-FE-03c: 导出聊天记录**
- **步骤**:
  1. 打开一个有消息的会话
  2. 点击聊天顶部 "导出记录" 按钮（或侧边栏 hover 时的下载图标）
  3. Then 浏览器下载 JSON 文件
  4. 打开 JSON 文件验证内容
- **预期**: JSON 包含 session 元数据、Agent 列表、完整消息历史
- **验证**: `✓ JSON 文件包含 session/messages/agents/exported_at/total_messages`

**UAT-FE-03d: 创建智能体时一步配齐**
- **步骤**:
  1. 打开智能体页面，点击「+ 创建智能体」
  2. 填写名称和系统提示词
  3. 选择 LLM Provider 和模型
  4. 勾选需要的技能和 MCP 服务器
  5. 开启进化引擎，设置模式/种群/代数
  6. 开启 RL 训练，设置算法/步数
  7. 点击「创建智能体」
  8. Then 新 Agent 出现在卡片网格中，状态为在线
- **预期**: 创建后 Agent 已绑定所有配置，无需二次编辑
- **验证**: `✓ 点击卡片查看详情，LLM/技能/MCP/进化/RL 配置均正确`

### 4.2 Dashboard（仪表盘 V2）

**UAT-FE-04: Agent 卡片网格显示**
- **步骤**:
  1. Given 3 个 Agent 在线
  2. When 打开仪表盘
  3. Then 显示 3 个 Agent 卡片（响应式网格）
  4. And 每个卡片显示头像、名称、在线状态、系统提示摘要
  5. And 每个卡片有"进化引擎"和"强化学习"标签
- **预期**: 实时反映 Agent 状态
- **验证**: `✓ Agent 卡片数量和状态正确`

**UAT-FE-05: 点击卡片弹出训练记录**
- **步骤**:
  1. When 点击 Agent 卡片
  2. Then 弹出模态窗口（max-w-5xl）
  3. And 窗口有"进化引擎"和"强化学习"两个 Tab
  4. When 选择"进化引擎"Tab
  5. Then 显示该 Agent 的进化训练历史列表
- **预期**: 每条记录显示状态、代数、最优适应度
- **验证**: `✓ 弹窗正常打开，训练记录列表加载`

**UAT-FE-06: 训练记录左右分栏**
- **步骤**:
  1. Given 至少有一条已完成的训练记录
  2. When 点击展开该记录
  3. Then 左侧（45%）显示可滚动日志表格
  4. And 右侧（55%）显示 Recharts 图表
  5. And 顶部显示配置摘要卡片
- **预期**: 进化日志显示代数/最优/均值/标准差/多样性；RL 日志显示步数/奖励/损失
- **验证**: `✓ 日志表格和图表同时正确渲染`

**UAT-FE-07: 图表放大功能**
- **步骤**:
  1. Given 训练记录已展开
  2. When 点击任意图表的"⤢ 放大"按钮
  3. Then 弹出全屏 ZoomOverlay（max-w-5xl）
  4. And 图表以更大高度渲染（500px）
  5. When 点击遮罩或关闭按钮
  6. Then 关闭全屏视图
- **预期**: 放大后图表清晰可读
- **验证**: `✓ 放大和关闭交互正常`

### 4.3 Settings（设置页 V2）

**UAT-FE-08: 多 Provider LLM 卡片**
- **步骤**:
  1. When 打开设置 → 模型配置 Tab
  2. Then 显示 Provider 卡片网格
  3. When 点击"+ 添加 Provider"
  4. Then 弹出创建表单（名称/厂商/接口地址/API Key）
  5. When 填写并创建
  6. Then 新卡片出现在网格中
- **预期**: 每张卡片可展开编辑、添加模型
- **验证**: `✓ Provider CRUD 完整`

**UAT-FE-09: MCP 在线安装**
- **步骤**:
  1. When 打开设置 → MCP 服务 Tab
  2. When 点击"+ 添加服务器" → 选择"从 npm 在线安装"
  3. When 输入 npm 包名并点击"在线安装"
  4. Then MCP 服务器自动注册（stdio 模式）
- **预期**: 显示安装结果（含探测到的工具数）
- **验证**: `✓ MCP 服务器出现在列表中`

**UAT-FE-10: Skill 在线安装**
- **步骤**:
  1. When 打开设置 → 技能管理 Tab
  2. When 点击"+ 安装技能" → 选择"从在线安装"
  3. When 输入 GitHub 仓库 URL 并点击"在线安装"
  4. Then 技能自动下载并安装
- **预期**: 安装后出现在技能列表中
- **验证**: `✓ 技能名称和描述正确显示`

### 4.4 Monitor

**UAT-FE-11: 训练指标实时图表**
- **步骤**:
  1. Given RL 训练进行中
  2. When 打开 Monitor 页面
  3. Then 显示 reward 曲线图
  4. And 数据点实时更新
- **预期**: 图表每秒更新新数据点
- **验证**: `✓ 曲线实时滚动, 无卡顿`

**UAT-FE-12: LTTB 降采样**
- **步骤**:
  1. Given 10000 个数据点
  2. When 图表宽度只能显示 500 点
  3. Then 使用 LTTB 算法降采样
  4. And 保留视觉特征 (峰值和谷值)
- **预期**: 图表保持关键特征, 不丢失趋势
- **验证**: `✓ 降采样后峰值误差 < 5%`

---

## 5. 集成验收 (Cross-Module)

**UAT-INT-01: Agent → Bus → Agent 通信**
- **步骤**:
  1. Given Agent A 和 Agent B 通过 InProcessBus 连接
  2. When A 发布消息到 "task.result"
  3. Then B 在 100ms 内收到
- **验证**: `python -m pytest tests/integration/test_agent_bus_integration.py -v`

**UAT-INT-02: Evolution → Dashboard 训练记录**
- **步骤**:
  1. Given Agent 配置了进化引擎参数
  2. When 调用 POST /api/agents/{id}/evolution/start
  3. Then 进化运行完成
  4. When 打开仪表盘 → 点击 Agent 卡片 → 进化引擎 Tab
  5. Then 显示训练历史列表
  6. When 展开记录
  7. Then 左侧显示逐代日志（代数/最优/均值/标准差/多样性）
  8. And 右侧显示适应度曲线 + 面积图 + 进化树
- **验证**: `✓ 前端实时反映后端训练状态`

**UAT-INT-03: RL 训练 → Dashboard 训练记录**
- **步骤**:
  1. Given Agent 配置了 RL 参数
  2. When 调用 POST /api/agents/{id}/rl/start
  3. Then RL 训练完成
  4. When 打开仪表盘 → 点击 Agent 卡片 → 强化学习 Tab
  5. Then 显示训练历史列表
  6. When 展开记录
  7. Then 左侧显示逐步日志（步数/奖励/损失）
  8. And 右侧显示奖励曲线 + 损失曲线 + 对比图
- **验证**: `✓ 端到端数据流通`

**UAT-INT-04: Skill 在线安装 → Agent 配置 → 运行**
- **步骤**:
  1. When POST /api/skills/install-url { "url": "https://..." }
  2. Then 技能安装成功
  3. When PATCH /api/agents/{id} { config.skill_ids: ["new-skill"] }
  4. Then Agent 配置更新成功
- **验证**: `✓ 在线安装的技能可立即分配给 Agent`

**UAT-INT-05: MCP npm 安装 → Agent 配置**
- **步骤**:
  1. When POST /api/mcp-servers/install-online { "package": "@scope/name" }
  2. Then MCP 服务器注册成功
  3. When PATCH /api/agents/{id} { config.mcp_server_ids: ["new-server"] }
  4. Then Agent 获得新工具
- **验证**: `✓ 在线安装的 MCP 服务器可立即分配给 Agent`

---

## 验收总结

| Module | Scenarios | Automated | Manual | Pass Criteria |
|--------|-----------|-----------|--------|---------------|
| agent-core | 9 | 9 | 0 | 全部 tests passed |
| evolution-engine | 11 | 11 | 0 | 全部 tests passed |
| rl-engine | 9 | 9 | 0 | 全部 tests passed |
| frontend-ui | 16 | 2 | 14 | UI 交互符合预期 |
| integration | 5 | 2 | 3 | 端到端数据流通 |
| **Total** | **50** | **33** | **17** | **50/50 通过** |

### 自动化验证命令

```bash
# Agent-Core (9 scenarios)
python -m pytest tests/unit/agent/ tests/unit/bus/ tests/unit/types/ tests/e2e/test_agent_lifecycle_e2e.py -v

# Evolution-Engine (11 scenarios)
python -m pytest tests/unit/evoforge/ tests/integration/test_evoforge_integration.py tests/e2e/test_evolve_cycle_e2e.py -v

# RL-Engine (9 scenarios)
python -m pytest tests/unit/rlforge/ tests/e2e/test_cartpole_train_e2e.py -v

# Frontend-UI (2 automated + 5 manual)
cd frontend && npx vitest run src/tests/lttb.test.ts -v

# Integration (2 automated)
python -m pytest tests/integration/ -v
```

### Manual Test Checklist (Frontend)

- [ ] UAT-FE-01: 发送消息成功
- [ ] UAT-FE-02: 接收 Agent 回复
- [ ] UAT-FE-03: 断线/重连提示
- [ ] UAT-FE-03a: 群聊创建（多 Agent 多轮讨论）
- [ ] UAT-FE-03b: 删除对话记录（会话 + 消息）
- [ ] UAT-FE-03c: 导出聊天记录（JSON 下载）
- [ ] UAT-FE-03d: 创建智能体时一步配齐（LLM/技能/MCP/进化/RL）
- [ ] UAT-FE-04: Agent 卡片网格正确显示
- [ ] UAT-FE-05: 点击卡片弹出训练记录
- [ ] UAT-FE-06: 训练记录左右分栏（日志+图表）
- [ ] UAT-FE-07: 图表放大功能
- [ ] UAT-FE-08: 多 Provider LLM 卡片 CRUD
- [ ] UAT-FE-09: MCP npm 在线安装
- [ ] UAT-FE-10: Skill URL 在线安装
- [ ] UAT-FE-11: 训练曲线实时更新
- [ ] UAT-FE-12: LTTB 降采样保留特征
