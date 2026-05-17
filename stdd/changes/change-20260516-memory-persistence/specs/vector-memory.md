# Delta Spec: Vector Memory

> Change: change-20260516-memory-persistence | Domain: memory/vector | Type: ADDED
> Status: Draft

---

## Feature: 语义存储与检索

```gherkin
Feature: 向量记忆 - ChromaDB 语义检索
  系统 SHALL 提供基于向量嵌入的语义存储和 top-k 检索。

  Scenario: 存储向量记忆
    Given VectorMemory 实例，collection_name="test"
    When 调用 memory.store(session_id="s1", content="如何配置数据库连接", metadata={"domain":"config"})
    Then SHALL 返回生成的 UUID
    And 向量嵌入 SHALL 自动生成并存储

  Scenario: 语义相似搜索
    Given 已存储记忆 "如何配置数据库连接" 和 "前端页面布局方式"
    When 调用 memory.search(session_id="s1", query="数据库设置方法", top_k=2)
    Then 结果 SHALL 按语义相似度排序
    And "如何配置数据库连接" SHALL 排在更前面

  Scenario: top-k 结果限制
    Given 已存储 10 条向量记忆
    When 调用 memory.search(session_id="s1", query="测试查询", top_k=3)
    Then SHALL 返回最多 3 条结果

  Scenario: 空集合搜索
    Given VectorMemory 实例，无任何存储
    When 调用 memory.search(session_id="s1", query="任意查询", top_k=5)
    Then SHALL 返回空列表
```

## Feature: 会话隔离

```gherkin
Feature: 向量记忆会话隔离
  不同会话的向量记忆 SHALL 互不可见。

  Scenario: 向量记忆会话隔离
    Given "session-a" 存储了 "记忆A"
    And "session-b" 存储了 "记忆B"
    When 在 "session-a" 中搜索
    Then SHALL 仅包含 "记忆A" 的语义结果

  Scenario: 删除向量记忆
    Given 一条向量记忆已存储
    When 调用 memory.delete(session_id, entry_id)
    Then 再次搜索 SHALL 不包含该条目
```
