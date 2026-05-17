# Spec: {{FEATURE_NAME}}

> BDD 规格文档 | 变更: {{CHANGE_ID}} | 日期: {{DATE}}

## Feature: {{FEATURE_NAME}}

**作为** {{ROLE}}
**我想要** {{CAPABILITY}}
**以便** {{VALUE}}

---

## Scenarios

### Scenario 1: {{SCENARIO_NAME}} (happy_path)

```gherkin
Given {{PRECONDITION}}
When {{ACTION}}
Then {{EXPECTED_RESULT}}
```

**测试映射**: `src/__tests__/{{feature}}.spec.ts` → `should {{scenario_name}}`

---

### Scenario 2: {{EDGE_CASE_NAME}} (edge_case)

```gherkin
Given {{EDGE_PRECONDITION}}
When {{EDGE_ACTION}}
Then {{EDGE_EXPECTED_RESULT}}
```

---

### Scenario 3: {{ERROR_CASE_NAME}} (error_path)

```gherkin
Given {{ERROR_PRECONDITION}}
When {{ERROR_ACTION}}
Then {{ERROR_HANDLING}}
```

---

## 覆盖矩阵

| 需求点 | Scenario | 类型 | 状态 |
|--------|----------|------|------|
| {{requirement_1}} | Scenario 1 | happy_path | ✅ |
| {{requirement_2}} | Scenario 2 | edge_case | ✅ |
| {{requirement_3}} | Scenario 3 | error_path | ✅ |

---

## 红线检查

- [ ] 无实现细节（无类名、表名、API URL）
- [ ] 所有 Then 描述用户可观察结果
- [ ] 所有数值使用具体数字
- [ ] 每个 In Scope 功能点有对应 Scenario

---

> 由 `/stdd:spec` 生成 | 参考 SpecKit spec 模板
