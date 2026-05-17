# Spec: Memory System

> Phase: 3 (Memory Layer) | Priority: P1 | Depends on: 00-core-types, 01-agent-lifecycle
> Type: ADDED
> Module: `agentforge/memory/`

---

## Overview

三层记忆系统：短期记忆（会话级 dict）、长期记忆（结构化存储）、向量检索（ChromaDB 嵌入）。通过 MemoryManager 门面类统一对外。

---

## Feature: ShortTermMemory

```gherkin
Feature: 短期记忆 - 基本读写
  作为 Agent
  我需要在同一会话内读写短期记忆
  以维持对话上下文

  Background:
    Given 一个 ShortTermMemory 实例
    And session_id 为 "session-001"

  Scenario: 存储记忆条目
    Given 一条内容 "用户询问了天气"
    When 我调用 memory.store("session-001", content, metadata={"type": "query"})
    Then 应返回生成的 UUID
    And 记忆条目应可被 retrieve

  Scenario: 检索记忆条目
    Given 一条记忆已存储，id 为 entry_id
    When 我调用 memory.retrieve("session-001", entry_id)
    Then 应返回 MemoryEntry:
      | field    | value              |
      | content  | "用户询问了天气"    |
      | metadata | {"type": "query"}  |

  Scenario: 检索不存在的条目
    Given 一个不存在的 UUID
    When 我调用 memory.retrieve("session-001", nonexistent_id)
    Then 应返回 None

  Scenario: 删除记忆条目
    Given 一条记忆已存储
    When 我调用 memory.delete("session-001", entry_id)
    Then 再次 retrieve 应返回 None
```

```gherkin
Feature: 短期记忆 - 会话隔离
  作为 Agent
  我需要不同会话的记忆互不可见
  以确保上下文隔离

  Scenario: 会话隔离
    Given 我在 "session-001" 存储了 "记忆A"
    And 我在 "session-002" 存储了 "记忆B"
    When 我在 "session-001" 中搜索所有记忆
    Then 应只包含 "记忆A"
    And 不应包含 "记忆B"

  Scenario: 清除会话记忆
    Given "session-001" 有 5 条记忆
    When 我调用 memory.clear("session-001")
    Then "session-001" 应无记忆
    And 其他会话不受影响
```

```gherkin
Feature: 短期记忆 - 容量限制
  作为 Memory 系统
  我需要限制短期记忆的容量
  以避免内存无限增长

  Scenario: 达到容量上限时淘汰最旧条目
    Given 短期记忆最大容量为 3
    And 已有 3 条记忆 [A, B, C]
    When 我存储第 4 条记忆 D
    Then 记忆 A 应被淘汰（最久未访问）
    And 记忆应变为 [B, C, D]

  Scenario: 访问刷新淘汰优先级
    Given 短期记忆最大容量为 3
    And 已有 3 条记忆 [A, B, C]
    When 我 retrieve 记忆 A
    And 存储第 4 条记忆 D
    Then 记忆 B 应被淘汰（A 被刷新后变为最新）
    And 记忆应变为 [A, C, D]
```

---

## Feature: LongTermMemory

```gherkin
Feature: 长期记忆 - 跨会话持久化
  作为 Agent
  我需要跨会话存储和检索长期记忆
  以积累持久知识

  Background:
    Given 一个 LongTermMemory 实例

  Scenario: 存储长期记忆
    When 我调用 memory.store(MemoryEntry(content="Python 使用缩进语法", metadata={"category": "knowledge"}))
    Then 应返回 UUID
    And 条目应持久化到磁盘

  Scenario: 跨会话检索
    Given 一条长期记忆在会话 A 中存储
    When 在会话 B 中 retrieve 同一条目
    Then 应返回该条目

  Scenario: 按元数据查询
    Given 多条长期记忆：
      | content          | metadata                     |
      | "Python 缩进"    | {"category": "knowledge"}    |
      | "完成重构"       | {"category": "task_history"} |
      | "Go goroutine"   | {"category": "knowledge"}    |
    When 我调用 memory.query(metadata_filter={"category": "knowledge"})
    Then 应返回 2 条结果（"Python 缩进" 和 "Go goroutine"）

  Scenario: 时间范围查询
    Given 记忆条目分布在 2026-01-01 到 2026-05-15
    When 我调用 memory.query(time_range=(start="2026-05-01", end="2026-05-15"))
    Then 应只返回 5 月的条目

  Scenario: 删除长期记忆
    Given 一条长期记忆已存储
    When 我调用 memory.delete(entry_id)
    Then 再次 retrieve 应返回 None
    And 磁盘上的数据应被移除
```

```gherkin
Feature: 长期记忆 - 过期机制
  作为 Memory 系统
  我需要支持记忆的 TTL 过期
  以自动清理过时信息

  Scenario: 记忆自动过期
    Given 一条长期记忆设置了 TTL=3600（1 小时）
    When 超过 1 小时后 retrieve 该条目
    Then 应返回 None
    And 过期条目应被自动清理

  Scenario: 无 TTL 的记忆永不过期
    Given 一条长期记忆未设置 TTL
    When 任意时间后 retrieve
    Then 应正常返回该条目
```

---

## Feature: VectorMemory (ChromaDB)

```gherkin
Feature: 向量记忆 - 存储
  作为 Agent
  我需要将记忆存入向量数据库
  以支持语义检索

  Background:
    Given 一个 VectorMemory 实例（使用 ChromaDB）
    And 嵌入模型为 "all-MiniLM-L6-v2"

  Scenario: 存储带嵌入的记忆
    When 我调用 memory.store(MemoryEntry(content="Python 的 asyncio 是事件循环模型"))
    Then content 应被自动嵌入为向量
    And 向量维度应为 384（all-MiniLM-L6-v2 的维度）
    And 条目应存入 ChromaDB collection

  Scenario: 存储时提供自定义嵌入
    Given 我有一个预计算的 384 维向量
    When 我调用 memory.store(MemoryEntry(content="用户消息", embedding=my_vector))
    Then 应使用我提供的向量，不重新计算
```

```gherkin
Feature: 向量记忆 - 语义检索
  作为 Agent
  我需要通过语义相似度检索记忆
  以找到与当前上下文最相关的信息

  Scenario: 语义搜索返回 top-k 结果
    Given 向量库中有以下记忆:
      | content                          |
      | "Python asyncio 使用事件循环"     |
      | "Go goroutine 是轻量级线程"       |
      | "JavaScript Promise 处理异步"     |
      | "Rust ownership 保证内存安全"      |
    When 我调用 memory.search("异步编程模型", top_k=2)
    Then 应返回 2 条最相关的结果
    And 应包含 "Python asyncio 使用事件循环"
    And 应包含 "JavaScript Promise 处理异步"

  Scenario: 搜索结果包含相似度分数
    When 我调用 memory.search("test query", top_k=3)
    Then 每个结果应附带 distance/score 字段
    And 结果应按相似度降序排列

  Scenario: 空向量库搜索
    Given 向量库为空
    When 我调用 memory.search("anything", top_k=5)
    Then 应返回空列表，不抛异常

  Scenario: 搜索带元数据过滤
    Given 记忆条目有不同的 metadata.category
    When 我调用 memory.search("异步", top_k=5, metadata_filter={"category": "knowledge"})
    Then 应只在 category="knowledge" 的条目中搜索
```

```gherkin
Feature: 向量记忆 - Collection 管理
  作为框架管理者
  我需要管理 ChromaDB collection
  以控制存储生命周期

  Scenario: 创建 Collection
    Given 一个新的 VectorMemory 实例
    And collection_name 为 "agent-001-memory"
    When 实例初始化时
    Then ChromaDB 中应创建对应 collection
    And 如果 collection 已存在则复用

  Scenario: 删除 Collection
    When 我调用 memory.drop_collection()
    Then Collection 中所有数据应被清除
```

---

## Feature: MemoryManager 门面

```gherkin
Feature: MemoryManager 统一接口
  作为 Agent
  我需要通过统一的 MemoryManager 管理三层记忆
  以简化记忆操作

  Background:
    Given 一个 MemoryManager 实例
    And 它组合了 ShortTermMemory, LongTermMemory, VectorMemory

  Scenario: 智能存储（自动路由到合适的层）
    When 我调用 manager.store(content, memory_type=MemoryType.SHORT_TERM)
    Then 应存储到 ShortTermMemory
    When 我调用 manager.store(content, memory_type=MemoryType.LONG_TERM)
    Then 应存储到 LongTermMemory
    When 我调用 manager.store(content, memory_type=MemoryType.VECTOR)
    Then 应存储到 VectorMemory（自动嵌入）

  Scenario: 统一搜索
    When 我调用 manager.search("query", top_k=5)
    Then 应同时搜索三层记忆
    And 合并结果按相关性排序
    And 每条结果标注来源层（short_term / long_term / vector）

  Scenario: 提升记忆（短期 → 长期）
    Given 短期记忆中有一条高价值条目
    When 我调用 manager.promote(entry_id, to=MemoryType.LONG_TERM)
    Then 条目应从 ShortTermMemory 复制到 LongTermMemory
    And ShortTermMemory 中原条目保留

  Scenario: 提升记忆（长期 → 向量）
    Given 长期记忆中有一条需要语义检索的条目
    When 我调用 manager.promote(entry_id, to=MemoryType.VECTOR)
    Then 条目应被嵌入并存入 ChromaDB
```

---

## Acceptance Criteria

- [ ] ShortTermMemory 使用 LRU 策略淘汰（基于 `accessed_at`）
- [ ] LongTermMemory 持久化到磁盘（JSON/SQLite）
- [ ] VectorMemory 使用 ChromaDB，嵌入模型可配置
- [ ] 所有操作为 async，使用 异步框架
- [ ] MemoryManager 实现统一门面模式
- [ ] 向量维度由嵌入模型决定，不硬编码
- [ ] 搜索结果包含 source 字段标识来源层
