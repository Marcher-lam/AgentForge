# Delta Spec: MCP Server Management

> Change: change-20260515-091942-capability | Domain: mcp | Type: MODIFIED
> Status: Updated 2026-05-16 to reflect actual implementation

---

## Feature: MCP Server CRUD

```gherkin
Feature: MCP 服务器管理
  支持手动注册和在线安装 MCP 服务器。

  Scenario: 手动注册 MCP 服务器
    When POST /api/mcp-servers { server_id, name, connection_type, command/url }
    Then SHALL 创建 MCPServerConfig 并存储
    And connection_type SHALL 支持 stdio 和 sse 两种模式

  Scenario: 列出 MCP 服务器
    When GET /api/mcp-servers
    Then SHALL 返回所有已注册服务器列表

  Scenario: 注销 MCP 服务器
    When DELETE /api/mcp-servers/{server_id}
    Then SHALL 从存储中移除
```

## Feature: MCP Online Install (npm)

```gherkin
Feature: 从 npm 在线安装 MCP 服务器
  支持输入 npm 包名自动配置并注册 MCP 服务器。

  Scenario: npm 包安装
    When POST /api/mcp-servers/install-online { "package": "@scope/name" }
    Then SHALL 自动配置为 stdio 模式
    And command SHALL 为 "npx -y {package}"
    And server_id SHALL 从包名自动生成（非法字符替换为 _）

  Scenario: 带参数安装
    When POST /api/mcp-servers/install-online { "package": "pkg", "args": "/path" }
    Then command SHALL 为 "npx -y pkg /path"

  Scenario: 工具名称探测
    When 安装 npm 包后
    Then SHALL 尝试运行命令（超时 10 秒）
    And SHALL 从输出中解析工具名称
    And 解析到的工具名 SHALL 存入 tool_names 字段

  Scenario: 安装失败容忍
    Given npm 包不存在或命令执行失败
    Then SHALL 仍然注册服务器（tool_names 为空）
    And SHALL 返回 {"status": "ok", "tool_names": []}
```

## Feature: Per-Agent MCP Selection

```gherkin
Feature: 按 Agent 选择 MCP 服务器
  每个 Agent 可从全局 MCP 服务器池中选择要使用的服务器。

  Scenario: Agent 配置中的 mcp_server_ids
    Given Agent 有 config.mcp_server_ids = ["server-1", "server-2"]
    When Agent 初始化
    Then SHALL 从全局 MCP 注册表加载指定服务器的工具
    And 工具 SHALL 注册到 Agent 的工具表中

  Scenario: 前端 Agent 编辑弹窗 MCP 选择
    Given 用户在智能体页面点击编辑 Agent
    Then SHALL 从 GET /api/mcp-servers 加载全局服务器列表
    And SHALL 显示复选框多选界面
    And 保存时 SHALL 写入 config.mcp_server_ids
```
