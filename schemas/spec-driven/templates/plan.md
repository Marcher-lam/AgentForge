# Plan: {{FEATURE_NAME}}

> 设计文档 | 变更: {{CHANGE_ID}} | 日期: {{DATE}}

## 概述

{{OVERVIEW}}

---

## 技术方案

### 架构决策

| 决策 | 选择 | 原因 | 备选方案 |
|------|------|------|----------|
| {{decision_1}} | {{choice_1}} | {{reason_1}} | {{alt_1}} |
| {{decision_2}} | {{choice_2}} | {{reason_2}} | {{alt_2}} |

### 文件变更清单

| 操作 | 文件路径 | 说明 |
|------|----------|------|
| 新增 | `src/{{path}}.ts` | {{description}} |
| 修改 | `src/{{existing_path}}.ts` | {{change_description}} |
| 新增 | `src/__tests__/{{test_path}}.test.ts` | {{test_description}} |

### 依赖关系

```
{{file_a}} ──► {{file_b}} ──► {{file_c}}
     │
     └──► {{file_d}}
```

---

## 风险评估

| 风险 | 概率 | 影响 | 缓解方案 |
|------|------|------|----------|
| {{risk_1}} | {{probability}} | {{impact}} | {{mitigation}} |

---

## 实现顺序

> 详细实现顺序参见 `IMPLEMENTATION_ORDER.md`

Phase 1 (基础层) → Phase 2 (核心层) → Phase 3 (适配层) → Phase 4 (入口层)

---

> 由 `/stdd:plan` 生成 | 参考 SpecKit plan 模板
