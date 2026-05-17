# Delta Spec: Skill System

> Change: change-20260515-091942-capability | Domain: skill | Type: MODIFIED
> Status: Updated 2026-05-16 to reflect actual implementation

---

## Feature: SKILL.md Skill Registry

```gherkin
Feature: SKILL.md 格式技能注册表
  技能使用 SKILL.md 标准格式（YAML frontmatter + Markdown 指令体），与 OpenClaw 兼容。

  Scenario: 技能目录结构
    Given skills/ 目录
    Then 每个技能 SHALL 为 skills/{name}/SKILL.md 目录结构

  Scenario: 技能解析
    Given 一个 SKILL.md 文件
    When 解析
    Then SHALL 提取 frontmatter 中的 name, description, version, tags
    And SHALL 提取 Markdown body 作为 instructions

  Scenario: 技能列表 API
    When GET /api/skills
    Then SHALL 返回所有已安装技能列表
    And 每条 SHALL 包含 name, description, instructions_length, source_path
```

## Feature: Skill Installation

```gherkin
Feature: 技能安装（三种方式）
  支持从文本、本地路径、在线 URL 三种方式安装技能。

  Scenario: 从 SKILL.md 文本安装
    When POST /api/skills { "content": "---\nname: my-skill\n---\n..." }
    Then SHALL 解析 SKILL.md 内容
    And SHALL 写入 skills/{name}/SKILL.md
    And SHALL 立即可用于 Agent 配置

  Scenario: 从本地路径安装
    When POST /api/skills/install-path { "path": "/path/to/SKILL.md" }
    Then SHALL 从路径加载 SKILL.md
    And SHALL 检查依赖要求 (check_requirements)
    And SHALL 安装到 skills/ 目录

  Scenario: 从在线 URL 安装
    When POST /api/skills/install-url { "url": "https://github.com/user/skill-repo" }
    Then SHALL 自动识别 URL 类型：
      | URL 类型 | 处理方式 |
      | GitHub 仓库 | 尝试 /SKILL.md 和 /skills/SKILL.md 路径 |
      | Raw 文件直链 | 直接 fetch 内容 |
    And SHALL 下载 SKILL.md 内容并安装

  Scenario: GitHub 仓库 URL 自动解析
    Given URL 为 "https://github.com/owner/repo"
    Then SHALL 尝试以下路径（按序）：
      1. https://raw.githubusercontent.com/owner/repo/main/SKILL.md
      2. https://raw.githubusercontent.com/owner/repo/main/skills/SKILL.md
    And 第一个成功的响应 SHALL 被使用

  Scenario: 安装失败处理
    Given URL 无法访问或内容不是有效 SKILL.md
    Then SHALL 返回 {"error": "..."} 错误信息
```

## Feature: Per-Agent Skill Selection

```gherkin
Feature: 按 Agent 选择技能
  每个 Agent 可从全局技能池中选择要使用的技能。

  Scenario: Agent 配置中的 skill_ids
    Given Agent 有 config.skill_ids = ["code-review", "web-search"]
    When Agent 初始化
    Then SHALL 从全局技能注册表加载指定技能
    And 技能指令 SHALL 注入 Agent 系统提示

  Scenario: 前端 Agent 编辑弹窗技能选择
    Given 用户在智能体页面点击编辑 Agent
    Then SHALL 从 GET /api/skills 加载全局技能列表
    And SHALL 显示复选框多选界面
    And 保存时 SHALL 写入 config.skill_ids
```

## Feature: Skill Uninstall

```gherkin
Feature: 技能卸载
  Scenario: 删除技能
    When DELETE /api/skills/{name}
    Then SHALL 从 skills/ 目录删除技能文件夹
```
