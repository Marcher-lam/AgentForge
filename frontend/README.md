# AgentForge Frontend

React 19 + TypeScript + Vite + TailwindCSS + Recharts

## 启动

```bash
npm install
npx vite --host 0.0.0.0 --port 5173
```

## 页面结构

| Tab | 组件 | 功能 |
|-----|------|------|
| 对话 | `App.tsx` (chat tab) | 会话列表（单聊/群聊切换 + 删除确认 + 导出记录）+ 消息面板 + WebSocket 实时通信 |
| 智能体 | `grid/AgentGrid.tsx` | 卡片式管理 + 创建时一步配齐（LLM/技能/MCP/进化/RL）+ 编辑弹窗 + 下载空模板 + JSON 知识文件上传到 Milvus 专属知识库 |
| 监控 | `monitor/MonitorPage.tsx` | 消息流监控（统计条/类型筛选/自动滚动） |
| 仪表盘 | `dashboard/DashboardPage.tsx` | Agent 卡片网格 → 点击弹出训练记录（左右分栏：日志+图表）+ 放大按钮 |
| 设置 | `settings/SettingsPage.tsx` | 模型配置（多 Provider 卡片）/ MCP 服务（手动+在线 npm 安装）/ 技能管理（在线 URL+路径+文本安装） |

## 关键依赖

| 包 | 用途 |
|----|------|
| React 19 | UI 框架 |
| Jotai | 状态管理（atoms/index.ts） |
| Recharts | 数据可视化（折线图/面积图/双 Y 轴） |
| TailwindCSS | 样式 |
| LTTB | 大数据集降采样（utils/lttb.ts） |

## 类型定义

`types/api.ts` 包含所有后端 API 对应的 TypeScript 类型：
- `AgentSummary` — 智能体信息（含 config/tools/skills）
- `AgentConfig` — 每智能体独立配置（LLM/工具/技能/MCP/进化/RL）
- `LLMProfile` — LLM Provider 卡片（多厂商多模型）
- `LLMOverride` — Per-Agent LLM 参数（含 RL 优化后的 temperature/max_tokens）
- `EvolutionConfig` — 进化配置（mode/population/mutation 等参数）
- `RLConfig` — RL 配置（algorithm/steps/lr 等参数）
- `EvolutionDashboardData` — 进化训练详情（适应度曲线/进化树/热力图）
- `TrainingDashboardData` — RL 训练详情（奖励/损失曲线）
- `MCPServerSummary` — MCP 服务器信息
- `OpenClawSkillSummary` — SKILL.md 格式技能（OpenClaw 兼容）
- `MonitorMessage` — Agent 间通信消息监控

## 进化 & RL 训练影响 Agent 行为

**进化引擎** → 改 Agent 的"人格"：
- 训练完成后最优基因组映射为 10 维人格特质（创造力/同理心/幽默感/...）
- 自动写回 Agent 的 system_prompt，追加 `[进化优化人格]` 标签
- 前端仪表盘可查看进化树 SVG 和适应度曲线

**RL 引擎** → 改 Agent 的"策略参数"：
- 训练完成后提取策略信号（奖励方差→temperature，loss→max_tokens，算法→风格描述）
- 自动写回 Agent 的 config.llm 参数 + system_prompt `[RL策略优化]` 标签
- 前端仪表盘可查看奖励/损失训练曲线

## 测试

```bash
npx vitest run          # 运行测试
npx tsc --noEmit        # 类型检查
```
