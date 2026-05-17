# Spec Guardian Suggestions — frontend-ui

> Generated: 2026-05-15T21:57:00.337064 | Mode: --spec-guardian --fix

## Fixes Applied

| # | File | Fix |
|---|------|-----|
| 1 | `chat-panel.md` | Added Connection Resilience feature (4 scenarios: disconnect prompt, auto-reconnect, retry-failed, offline message catchup) |

## Accepted Warnings (No Fix Needed)

7 IMPL-001 warnings for UI library names (ECharts, Framer Motion, LTTB, WebSocket).
These are **technology selection declarations** in frontend specs, not implementation leakage.
Frontend specs legitimately name rendering libraries as they define the visual contract.

## Validation Result

- **0 Blocking**
- **7 Warnings** (UI library names — acceptable)
- **0 Suggestions**
- **Status: PASS**
