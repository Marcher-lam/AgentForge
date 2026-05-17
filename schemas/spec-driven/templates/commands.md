# Commands: {{FEATURE_NAME}}

> CLI 命令参考 | 变更: {{CHANGE_ID}} | 日期: {{DATE}}

## 工作流命令

### 标准流程

```bash
# 1. 提出需求
/stdd:propose

# 2. 需求澄清
/stdd:clarify

# 3. 确认需求
/stdd:confirm

# 4. 生成 BDD 规格
/stdd:spec

# 5. 任务拆解
/stdd:plan

# 6. 实现任务
/stdd:apply

# 7. TDD 执行循环
/stdd:execute

# 8. 验证 & 提交
/stdd:verify
/stdd:commit
```

### 快捷流程

```bash
# 一键通扫
/stdd:turbo

# 快速前跳
/stdd:ff

# Bug 修复
/stdd:issue

# 头脑风暴
/stdd:brainstorm
```

---

## 当前变更命令

| 步骤 | 命令 | 状态 |
|------|------|------|
| 提案 | `/stdd:propose` | {{PROPOSE_STATUS}} |
| 澄清 | `/stdd:clarify` | {{CLARIFY_STATUS}} |
| 确认 | `/stdd:confirm` | {{CONFIRM_STATUS}} |
| 规格 | `/stdd:spec` | {{SPEC_STATUS}} |
| 计划 | `/stdd:plan` | {{PLAN_STATUS}} |
| 实现 | `/stdd:apply` | {{APPLY_STATUS}} |
| 执行 | `/stdd:execute` | {{EXECUTE_STATUS}} |
| 提交 | `/stdd:commit` | {{COMMIT_STATUS}} |

---

## 自定义命令

{{CUSTOM_COMMANDS}}

---

> 由 `/stdd:init` 生成 | 参考 SpecKit commands 模板
