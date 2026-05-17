# Delta Spec: Memory System

> Change: change-20260515-091942-memory | Domain: memory | Type: ADDED
> Status: Draft

---

## Feature: Short-Term Memory

```gherkin
Feature: 短期记忆 (会话级 LRU)
  Agent SHALL 在同一会话内读写短期记忆，容量 100，LRU 淘汰。

  Scenario: 存储和检索
    Given 短期记忆 session_id="s1"
    When 存储 ("用户询问了天气", metadata={"type":"query"})
    Then 返回 UUID
    When 检索该 UUID
    Then SHALL 返回 MemoryEntry(content="用户询问了天气")

  Scenario: 会话隔离
    Given session "s1" 存储了 "记忆A"
    And session "s2" 存储了 "记忆B"
    When 在 "s1" 中搜索
    Then SHALL 仅包含 "记忆A"

  Scenario: LRU 淘汰
    Given 容量为 3，已有 [A, B, C]
    When 存储第 4 条 D
    Then A SHALL 被淘汰（最久未访问）

  Scenario: 访问刷新优先级
    Given 容量为 3，已有 [A, B, C]
    When retrieve A
    And 存储第 4 条 D
    Then B SHALL 被淘汰（A 被刷新）

  Scenario: 清除会话
    When 调用 memory.clear("s1")
    Then "s1" SHALL 无记忆
    And 其他会话不受影响
```

## Feature: Long-Term Memory

```gherkin
Feature: 长期记忆 (SQLite 持久化)
  Agent SHALL 跨会话存储和检索长期记忆。

  Scenario: 跨会话检索
    Given session A 存储长期记忆 "Python 用缩进"
    When session B 检索同一条目
    Then SHALL 成功返回

  Scenario: 按元数据查询
    Given 多条长期记忆 metadata.category 为 "knowledge" 和 "task_history"
    When 查询 metadata_filter={"category":"knowledge"}
    Then SHALL 仅返回 category="knowledge" 的条目

  Scenario: 时间范围查询
    When 查询 time_range=(start="2026-05-01", end="2026-05-15")
    Then SHALL 仅返回该时间范围内的条目

  Scenario: TTL 过期主动清理
    Given 一条长期记忆 TTL=3600
    When 超过 1 小时
    Then 后台定时任务 SHALL 清理该条目
    And retrieve SHALL 返回 None

  Scenario: 持久化跨重启
    Given 存储一条长期记忆
    When 应用重启
    Then 该条目 SHALL 仍可通过 retrieve 获取
```

## Feature: Vector Memory

```gherkin
Feature: 向量记忆 (ChromaDB 语义检索)
  Agent SHALL 可通过语义相似度检索记忆。

  Scenario: 自动嵌入存储
    When 存储 "Python asyncio 是事件循环模型"
    Then content SHALL 被自动嵌入为向量
    And 存入 ChromaDB collection

  Scenario: 语义搜索 top-k
    Given 已存储 "asyncio 事件循环", "Go goroutine", "JS Promise", "Rust ownership"
    When 搜索 "异步编程模型", top_k=2
    Then SHALL 返回 2 条最相关结果
    And SHALL 包含 "asyncio 事件循环"

  Scenario: 搜索结果含相似度分数
    When 搜索任意 query
    Then 每个结果 SHALL 附带 distance/score
    And 结果 SHALL 按相似度降序排列

  Scenario: 余弦相似度度量
    Given ChromaDB 配置使用余弦相似度
    When 计算向量距离
    Then SHALL 使用余弦相似度（非 L2）

  Scenario: 可配置嵌入模型
    Given 配置嵌入模型为 "all-MiniLM-L6-v2"
    When 存储记忆
    Then SHALL 使用该模型生成嵌入
    When 切换为 OpenAI embedding
    Then SHALL 使用 OpenAI API 生成嵌入
```

## Feature: MemoryManager

```gherkin
Feature: MemoryManager 统一门面
  Agent SHALL 通过 MemoryManager 统一操作三层记忆。

  Scenario: 智能路由存储
    When 调用 manager.store(content, type=SHORT_TERM)
    Then SHALL 存储到 ShortTermMemory
    When 调用 manager.store(content, type=LONG_TERM)
    Then SHALL 存储到 LongTermMemory
    When 调用 manager.store(content, type=VECTOR)
    Then SHALL 自动嵌入并存入 ChromaDB

  Scenario: 统一搜索
    When 调用 manager.search("query", top_k=5)
    Then SHALL 同时搜索三层
    And 合并结果按相关性排序
    And 每条结果 SHALL 标注来源层 (short_term / long_term / vector)

  Scenario: 原子 promote
    Given 短期记忆中有一条目
    When 调用 manager.promote(entry_id, to=LONG_TERM)
    Then 条目 SHALL 复制到 LongTermMemory
    And 短期记忆中原条目保留
    When promote 过程失败
    Then SHALL 回滚，两边数据不变

  Scenario: promote 到向量层
    Given 长期记忆中有一条目
    When 调用 manager.promote(entry_id, to=VECTOR)
    Then 条目 SHALL 被嵌入并存入 ChromaDB
```
