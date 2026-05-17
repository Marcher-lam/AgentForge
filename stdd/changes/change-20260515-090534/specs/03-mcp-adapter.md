# Spec: MCP Protocol Adapter

> Phase: 2 (Capability Layer) | Priority: P0 | Depends on: 00-core-types, 01-agent-lifecycle
> Type: ADDED
> Module: `agentforge/mcp/`

---

## Overview

MCP 协议适配层，实现工具的注册、发现、调用和结果解析。遵循 MCP specification 2025-03-26 和 JSON-RPC 2.0。

---

## Feature: 工具注册

```gherkin
Feature: 工具注册
  作为工具开发者
  我需要将工具注册到 ToolRegistry
  以便 Agent 可以发现和调用

  Background:
    Given 一个 MCPToolRegistry 实例

  Scenario: 注册新工具
    Given 一个 ToolDescriptor:
      | field        | value                              |
      | name         | "web_search"                       |
      | description  | "搜索互联网信息"                    |
      | input_schema | {"type": "object", "properties": {"query": {"type": "string"}}} |
    When 我调用 registry.register(descriptor)
    Then 工具 "web_search" 应出现在 registry 中
    And 调用 registry.list_tools() 应包含该工具

  Scenario: 工具带 handler 注册
    Given 一个 ToolDescriptor 和对应的 async handler
    When 我调用 registry.register(descriptor, handler)
    Then 后续调用 "web_search" 应路由到该 handler

  Scenario: 注册同名工具
    Given 工具 "web_search" 已注册
    When 我再次注册同名工具 "web_search"
    Then 应抛出 ToolAlreadyRegisteredError

  Scenario: 使用装饰器注册工具
    Given 一个 MCPToolRegistry 实例
    When 我使用 @registry.tool 装饰器注册函数
      ```python
      @registry.tool(name="calculator", description="计算数学表达式")
      异步函数 calculator(expression: str) -> float:
          return eval(expression)
      ```
    Then 工具 "calculator" 应自动注册
    And input_schema 应从函数签名自动推断
```

---

## Feature: 工具发现

```gherkin
Feature: 工具发现
  作为 Agent
  我需要列出和搜索可用工具
  以便找到合适的工具完成任务

  Scenario: 列出所有工具
    Given registry 中有 5 个已注册工具
    When 我调用 registry.list_tools()
    Then 应返回包含 5 个 ToolDescriptor 的列表

  Scenario: 按 JSON-RPC methods/list 列出工具
    Given registry 中有已注册工具
    When 收到 JSON-RPC 请求 {"method": "tools/list", "id": "1"}
    Then 应返回符合 MCP spec 的响应
      ```json
      {
        "jsonrpc": "2.0",
        "id": "1",
        "result": {
          "tools": [
            {"name": "web_search", "description": "搜索网页", "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}}}}
          ]
        }
      }
      ```
```

---

## Feature: 工具调用

```gherkin
Feature: 工具调用
  作为 Agent
  我需要通过 MCP 协议调用工具
  以执行具体操作

  Background:
    Given 工具 "web_search" 已注册，handler 返回 {"results": ["result1"]}

  Scenario: 成功调用工具
    When 我调用 registry.call_tool("web_search", {"query": "Python asyncio"})
    Then 应返回 ToolCallResult:
      | field    | value                    |
      | is_error | False                    |
      | result   | {"results": ["result1"]} |

  Scenario: 通过 JSON-RPC tools/call 调用
    When 收到 JSON-RPC 请求:
      ```json
      {
        "jsonrpc": "2.0",
        "id": "2",
        "method": "tools/call",
        "params": {"name": "web_search", "arguments": {"query": "test"}}
      }
      ```
    Then 应返回:
      ```json
      {
        "jsonrpc": "2.0",
        "id": "2",
        "result": {"content": [{"type": "text", "text": "搜索结果内容"}]}
      }
      ```

  Scenario: 调用不存在的工具
    When 我调用 registry.call_tool("nonexistent", {})
    Then 应返回 ToolCallResult:
      | field    | value                              |
      | is_error | True                               |
      | error    | {"code": -32601, "message": "Method not found"}  |

  Scenario: 工具 handler 抛出异常
    Given 工具 "bad_tool" 的 handler 抛出 ValueError
    When 我调用 registry.call_tool("bad_tool", {})
    Then 应返回 ToolCallResult:
      | field    | value                              |
      | is_error | True                               |
      | error    | {"code": -32603, "message": "Internal error"}  |
    And 不应导致 registry 崩溃

  Scenario: 工具参数校验失败
    Given 工具 "web_search" 的 input_schema 要求 query 为 string
    When 我调用 registry.call_tool("web_search", {"query": 123})
    Then 应返回 ToolCallResult:
      | field    | value                              |
      | is_error | True                               |
      | error    | {"code": -32602, "message": "Invalid params"}  |
```

---

## Feature: JSON-RPC 2.0 协议处理

```gherkin
Feature: JSON-RPC 消息解析
  作为 MCP 适配层
  我需要正确处理 JSON-RPC 2.0 消息
  以确保协议兼容性

  Scenario: 解析合法请求
    Given 一条合法的 JSON-RPC 请求
    When 我调用 parse_request(json_str)
    Then 应返回解析后的 request 对象

  Scenario: 解析非法 JSON
    Given 一段非法 JSON 字符串
    When 我调用 parse_request(bad_json)
    Then 应返回 JSON-RPC 错误响应:
      | code   | message            |
      | -32700 | Parse error        |

  Scenario: 缺少必要字段
    Given JSON 缺少 "jsonrpc" 字段
    When 我调用 parse_request(json_str)
    Then 应返回 JSON-RPC 错误响应:
      | code   | message                 |
      | -32600 | Invalid Request         |

  Scenario: 未知方法
    Given JSON-RPC method 为 "unknown/method"
    When 我调用 handle_request(request)
    Then 应返回 JSON-RPC 错误响应:
      | code   | message                 |
      | -32601 | Method not found        |
```

```gherkin
Feature: 批量请求处理
  作为 MCP 适配层
  我需要支持 JSON-RPC 批量请求
  以提高通信效率

  Scenario: 处理批量请求
    Given 一个包含 3 个请求的 JSON-RPC batch
    When 我调用 handle_batch(requests)
    Then 应返回包含 3 个响应的 batch
    And 响应顺序与请求对应

  Scenario: 空批量请求
    Given 一个空数组 []
    When 我调用 handle_batch([])
    Then 应返回 Invalid Request 错误
```

---

## Feature: MCP 协议能力协商

```gherkin
Feature: initialize/capabilities 握手
  作为 MCP 适配层
  我需要支持客户端-服务端能力协商
  以确保双方功能兼容

  Scenario: initialize 握手
    When 收到 initialize 请求:
      ```json
      {
        "method": "initialize",
        "params": {
          "protocolVersion": "2025-03-26",
          "capabilities": {},
          "clientInfo": {"name": "test-client", "version": "1.0"}
        }
      }
    ```
    Then 应返回:
      ```json
      {
        "protocolVersion": "2025-03-26",
        "capabilities": {"tools": {"listChanged": true}},
        "serverInfo": {"name": "agentforge-mcp", "version": "0.1.0"}
      }
      ```

  Scenario: 协议版本不兼容
    When 客户端 protocolVersion 为 "2024-01-01"
    Then 应返回错误，提示版本不兼容
```

---

## Acceptance Criteria

- [ ] 所有 JSON-RPC 响应包含 `jsonrpc: "2.0"` 和 `id` 字段
- [ ] 错误响应遵循 JSON-RPC 2.0 错误码规范
- [ ] 工具调用参数校验基于 input_schema (JSON Schema)
- [ ] handler 异常不泄漏到协议层（统一转为 ToolCallResult is_error=True）
- [ ] 装饰器注册自动推断 input_schema
- [ ] 支持 MCP spec 2025-03-26 的 initialize/tools/list/tools/call 方法
