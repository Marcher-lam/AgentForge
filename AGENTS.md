# STDD Copilot - AI Agent Instructions

> Version: 1.0 | Last Updated: 2026-05-15

## Overview

STDD Copilot (Spec + Test Driven Development) 是一个融合了 SDD 和 TDD 最佳实践的 AI 辅助开发框架。

## 核心原则

1. **Spec-First**: 需求规格是 Source of Truth
2. **Test-Driven**: Ralph Loop 5步 TDD 循环
3. **Delta Specs**: 增量式变更管理
4. **5-Level Defense**: 防跑偏机制

## 可用命令

在支持的 AI Code 终端（Claude Code, Qwen Code, Cursor 等）中使用以下斜杠命令：

| 命令 | 说明 |
|------|------|
| `/stdd:init` | 初始化 STDD 工作区 |
| `/stdd:new` | 创建新变更提案 |
| `/stdd:explore` | 探索需求 |
| `/stdd:ff` | 快速生成 |
| `/stdd:continue` | 继续工作 |
| `/stdd:apply` | 执行 TDD 循环 |
| `/stdd:verify` | 验证实现 |
| `/stdd:archive` | 归档变更 |
| `/stdd:graph *` | Graph 引擎 |

## 工作流程

```
/stdd:new → /stdd:apply → /stdd:archive
```

详见: https://github.com/Marcher-lam/STDD-COPILOT
