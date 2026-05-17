# Delta Spec: MCP Protocol Adapter

> Change: change-20260515-091942-capability | Domain: mcp | Type: ADDED
> Status: Draft

---

## Feature: Tool Registration

```gherkin
Feature: 工具注册与发现
  开发者 SHALL 可将工具注册到 MCPToolRegistry 并被 Agent 发现。

  Scenario: 注册新工具
    Given 一个 ToolDescriptor(name="web_search", input_schema={"type":"object","properties":{"query":{"type":"string"}},"required":["query"]})
    And 一个 async handler
    When 调用 registry.register(descriptor, handler)
    Then "web_search" SHALL 出现在 registry.list_tools() 中

  Scenario: 装饰器注册工具
    Given 使用 @registry.tool 装饰器
    When 装饰一个 异步函数 web_search(query: str) -> dict 函数
    Then input_schema SHALL 从函数签名自动推断
    And 工具 SHALL 自动注册

  Scenario: 同步 handler 自动包装
    Given 一个 def sync_tool(x: int) -> int 同步函数
    When 通过装饰器或 register 注册
    Then SHALL 自动用 异步框架.to_thread 包装为 async
    And 调用时 SHALL 正常工作

  Scenario: 注册同名工具
    Given "web_search" 已注册
    When 再次注册同名工具
    Then SHALL 抛出 ToolAlreadyRegisteredError
```

## Feature: Tool Invocation

```gherkin
Feature: 工具调用
  Agent SHALL 可通过 MCP 协议调用工具。

  Scenario: 成功调用工具
    Given "web_search" 已注册，handler 返回 {"results": ["r1"]}
    When 调用 registry.call_tool("web_search", {"query": "test"})
    Then SHALL 返回 ToolCallResult(is_error=False, result={"results": ["r1"]})

  Scenario: 流式工具调用
    Given "stream_gen" 已注册，handler 为 async generator yield 3 个结果
    When 调用流式工具
    Then SHALL 返回 AsyncGenerator
    And 用户 SHALL 可 async for 遍历 3 个结果

  Scenario: 调用不存在的工具
    When 调用 registry.call_tool("nonexistent", {})
    Then SHALL 返回 ToolCallResult(is_error=True, error={"code":-32601})

  Scenario: 严格 schema 校验
    Given "web_search" 的 input_schema 要求 query 为 string
    When 调用 registry.call_tool("web_search", {"query":123,"extra":"field"})
    Then SHALL 返回 ToolCallResult(is_error=True, error={"code":-32602})
    And 错误信息 SHALL 提及多余字段 "extra"

  Scenario: handler 异常隔离
    Given "bad_tool" 的 handler 抛出 ValueError
    When 调用 registry.call_tool("bad_tool", {})
    Then SHALL 返回 ToolCallResult(is_error=True, error={"code":-32603})
    And registry SHALL NOT 崩溃
```

## Feature: JSON-RPC 2.0

```gherkin
Feature: JSON-RPC 协议处理
  MCP 适配层 SHALL 正确处理 JSON-RPC 2.0 消息。

  Scenario: tools/list 响应
    Given registry 有 2 个已注册工具
    When 收到 {"jsonrpc":"2.0","id":"1","method":"tools/list"}
    Then SHALL 返回符合 MCP spec 的响应，包含 2 个 tool 描述

  Scenario: tools/call 响应
    When 收到 {"jsonrpc":"2.0","id":"2","method":"tools/call","params":{"name":"web_search","arguments":{"query":"test"}}}
    Then SHALL 返回 {"jsonrpc":"2.0","id":"2","result":{"content":[{"type":"text","text":"搜索结果"}]}}

  Scenario: 非法 JSON
    When 收到非法 JSON 字符串
    Then SHALL 返回 {"jsonrpc":"2.0","id":null,"error":{"code":-32700,"message":"Parse error"}}
```

## Feature: Remote MCP Transport

```gherkin
Feature: 远程 MCP Server 连接
  系统 SHALL 支持 stdio、SSE、WebSocket 三种传输层。

  Scenario: stdio 传输连接
    Given 远程 MCP Server 通过 stdio 通信
    When 建立连接
    Then SHALL 通过 stdin/stdout 发送/接收 JSON-RPC 消息

  Scenario: SSE 传输连接
    Given 远程 MCP Server 通过 SSE 通信
    When 建立连接
    Then SHALL 通过 HTTP SSE 接收服务端消息

  Scenario: WebSocket 传输连接
    Given 远程 MCP Server 通过 WebSocket 通信
    When 建立连接
    Then SHALL 通过 WebSocket 双向收发消息

  Scenario: 连接失败
    Given 远程 Server 不可达
    When 尝试连接
    Then SHALL 抛出 MCPConnectionError
```

## Feature: MCP Initialize Handshake

```gherkin
Feature: MCP initialize 握手
  客户端与服务端 SHALL 进行能力协商。

  Scenario: initialize 请求
    When 收到 initialize 请求(protocolVersion="2025-03-26")
    Then SHALL 返回 server capabilities 和 serverInfo

  Scenario: 版本不兼容
    When 客户端 protocolVersion 不匹配
    Then SHALL 返回错误提示版本不兼容
```
