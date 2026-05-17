# Delta Spec: Multi-Agent Discussion Engine

> Change: change-20260515-092930-multi-agent | Domain: multi_agent | Type: ADDED
> Status: Draft

> **NOTE**: This spec describes the ACTUAL multi-agent discussion engine implemented in
> `agentforge/server/app.py`. It is NOT multi-agent RL (MADDPG). The system orchestrates
> multiple LLMAgent instances in a 3-phase discussion workflow over WebSocket.

---

## Feature: 3-Phase Discussion Engine

```gherkin
Feature: 多 Agent 讨论引擎
  系统在 WebSocket 消息处理中实现 3 阶段多 Agent 讨论流程。

  Scenario: 单 Agent 直接回复
    Given session 中只有 1 个 agent
    When 收到用户消息
    Then SHALL 跳过讨论流程，直接调用 _agent_reply(agent, transcript, 0, True)
    And SHALL 广播 agent 回复

  Scenario: 多 Agent 进入讨论流程
    Given session 中有 >= 2 个 agent
    When 收到用户消息
    Then SHALL 执行 3 阶段讨论流程:
      Phase 1: Relevance Check（并行）
      Phase 2: Core Discussion（relevant agents, 多轮）
      Phase 3: Observer Commentary（observer agents, 1 轮）
```

## Feature: Phase 1 — Relevance Check

```gherkin
Feature: 话题相关性检查
  每个 Agent 并行判断用户话题是否与其角色相关。

  Scenario: 并行相关性判断
    Given session 中有 3 个 Agent
    When 收到用户消息 content
    Then SHALL 为每个 Agent 创建 asyncio.Task 调用 _check_relevance(agent, content)
    And 所有任务 SHALL 并行执行
    And 结果 SHALL 分为 relevant_ids 和 observer_ids 两组

  Scenario: 相关性判断逻辑
    Given Agent 的 system_prompt 和用户话题 topic
    When _check_relevance 调用 LLM
    Then SHALL 发送 prompt 要求 Agent 判断话题相关性
    And LLM temperature SHALL 为 0.0, max_tokens=8
    And 回答以 YES/"是"/"相关" 开头 SHALL 视为相关
    And LLM 调用异常时 SHALL 默认返回 True（保守策略）

  Scenario: 广播相关性状态
    Given 相关性检查完成
    When 分组为 relevant_ids 和 observer_ids
    Then SHALL 广播系统消息:
      "话题相关性：{relevant agents} 将参与讨论；{observer agents} 旁观"
```

## Feature: Phase 2 — Core Discussion

```gherkin
Feature: 核心 Agent 讨论
  相关 Agent 按轮流顺序进行多轮讨论。

  Scenario: 讨论轮数
    Given relevant_ids 中有 N 个 Agent
    Then max_rounds SHALL 为 min(3, max(2, N))
    And 有 2 个 Agent 时 SHALL 进行 2 轮
    And 有 3 个 Agent 时 SHALL 进行 3 轮
    And 有 5 个 Agent 时 SHALL 进行 3 轮（上限）

  Scenario: 第一轮发言（round_num=0）
    Given relevant Agent 参与讨论，round_num=0
    When _agent_reply 被调用
    Then instruction SHALL 要求 Agent 针对话题发表专业观点
    And 允许 @其他智能体讨论
    And 要求简洁有见地，不重复已有观点

  Scenario: 后续轮发言（round_num>0）
    Given relevant Agent 参与讨论，round_num>0
    When _agent_reply 被调用
    Then instruction SHALL 要求 Agent 看了其他人的发言后补充新观点
    And 如果没有补充 SHALL 输出 "PASS"

  Scenario: 提前终止
    Given 某轮中所有 relevant Agent 都输出 PASS 或空回复
    When spoke_this_round=False
    Then 讨论 SHALL 提前终止（break），不继续后续轮次

  Scenario: 轮间延迟
    Given 多个 relevant Agent 轮流发言
    When 一个 Agent 发言完成后
    Then SHALL 等待 asyncio.sleep(0.3) 再让下一个 Agent 发言
```

## Feature: Phase 3 — Observer Commentary

```gherkin
Feature: 旁观 Agent 评论
  不相关的 Agent 可选择性提供跨界视角。

  Scenario: 旁观 Agent 发言
    Given observer_ids 中的 Agent
    When Phase 3 执行
    Then SHALL 对每个 observer 调用 _agent_reply(agent, transcript, 99, False)
    And is_relevant=False 时 instruction SHALL 要求:
      "如果不属于你的专业领域，可以旁观并提供独特跨界视角（一两句话）"
    And temperature SHALL 为 0.7, max_tokens=128（限制篇幅）
    And 回复为 PASS 时 SHALL 不发言

  Scenario: 旁观者发言非强制
    Given observer Agent 返回空回复或 PASS
    When Phase 3 处理
    Then SHALL 不广播该 Agent 的消息
```

## Feature: Discussion Transcript

```gherkin
Feature: 讨论记录构建
  _build_transcript 函数格式化最近消息供 Agent 参考。

  Scenario: 格式化记录
    Given session 消息列表 messages
    When 调用 _build_transcript(messages, limit=20)
    Then SHALL 取最近 20 条消息
    And 每条格式为 "【{sender_name}】: {content}"
    And SHALL 用换行符连接

  Scenario: 记录累积
    Given 讨论 Phase 2 进行中
    When 每个 Agent 发言后
    Then 发言 SHALL 被追加到 state.messages[session_id]
    And 后续 Agent 的 transcript SHALL 包含之前所有发言
```

## Feature: NOT IMPLEMENTED (Future Enhancements)

```gherkin
Feature: 以下多 Agent 功能未实现
  当前实现为 LLM 讨论引擎，不包含多 Agent RL:

  Scenario: MADDPG 多 Agent RL — NOT IMPLEMENTED
    Given 当前多 Agent 讨论基于 LLM 文本生成
    Then 没有多 Agent 强化学习训练
    And 没有 centralized critic / distributed actor 架构

  Scenario: MultiAgentEnv — NOT IMPLEMENTED
    Given 当前 Environment 为单 Agent CartPole
    Then 没有 per-agent obs/reward/terminated 返回值
    And 没有 GridWorld 测试环境

  Scenario: PettingZoo 兼容 — NOT IMPLEMENTED
    Given 没有多 Agent 环境抽象
    Then 没有 PettingZoo ParallelEnv 包装器

  Scenario: 共享经验池 — NOT IMPLEMENTED
    Given 当前没有多 Agent RL 训练
    Then 没有共享 ReplayBuffer
    And 没有 agent_aware 采样策略
```
