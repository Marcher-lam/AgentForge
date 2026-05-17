# Spec Guardian Suggestions — agent-core

> Generated: 2026-05-15 | Project: agent-core | Flags: --spec-guardian --fix

## Summary

- **0 Blocking** issues
- **3 Warnings** (2 conflicts documented, 1 impl leakage fixed)
- **3 False Positives** (BDD-004 — Then steps exist but obscured by embedded code blocks)

## Fixes Applied

| # | File | Rule | Fix |
|---|------|------|-----|
| 1 | `00-core-types.md:212` | IMPL-001 | `dataclass` → `数据类型` in acceptance criteria |
| 2 | `api-spec.yaml` | CONFLICT-001/002 | Added NOTE header documenting intentional AgentState/MessageType transport-layer mapping |

## Warnings (Accepted)

### CONFLICT-001: AgentState enum in api-spec.yaml
- **File**: `api-spec.yaml` vs `types.md`
- **Details**: api-spec uses `CREATED`+`INITIALIZED` while core types use `INIT`
- **Resolution**: Intentional — API layer splits the BDD INIT state into CREATED (pre-init) and INITIALIZED (post-init) for HTTP status granularity. Documented in api-spec.yaml header.

### CONFLICT-002: MessageType enum mismatch
- **File**: `api-spec.yaml` vs `00-core-types.md`
- **Details**: Core types define `[COMMAND,EVENT,QUERY,RESPONSE,ERROR]`, api-spec defines `[TEXT,JSON,BINARY,TOOL_CALL,TOOL_RESULT,SYSTEM,DELIVERY_FAILED]`
- **Resolution**: Intentional — API uses transport-oriented types while core types use semantic types. Mapping happens at the adapter layer. Documented in api-spec.yaml header.

## False Positives (No Action Needed)

### BDD-004: "Scenario may lack Then steps" (3 instances in 03-mcp-adapter.md)
- All 3 scenarios have `Then 应返回:` assertions followed by JSON code blocks
- Regex missed them due to embedded ` ```json ``` ` blocks between Then and assertion content
- **No fix needed** — scenarios are complete
