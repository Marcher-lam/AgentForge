# Archive: agent-core

> Archived: 2026-05-16 | Status: completed

## Changes Archived

| Change ID | Title | Type |
|-----------|-------|------|
| change-20260515-091942-core | Core Skeleton (Phase 1) | feature |
| change-20260515-091942-capability | Capability Layer (Phase 2) | feature |
| change-20260515-091942-memory | Memory Layer (Phase 3) | feature |

## Quality Metrics at Archive

- **Tests**: 95 passed, 0 failed
- **Coverage**: 97.5% (threshold: 85%)
- **Complexity**: avg CC 2.0, max CC 11 (publish), 1 hotspot
- **Modules**: agent/, bus/, types/, infra/ — 16 files, 707 lines
- **Specs merged**: types.md, agent-lifecycle.md, bus-inprocess.md, bus-websocket.md, mcp-adapter.md, skill-system.md, memory-system.md

## Key Decisions (from ADRs)

| ADR | Decision | Status |
|-----|----------|--------|
| ADR-1 | anyio as async runtime | VIOLATED (asyncio dominates) |
| ADR-2 | frozen dataclass + slots | IMPLEMENTED |
| ADR-3 | Protocol over ABC | IMPLEMENTED |
| ADR-4 | Bounded queue backpressure | MODIFIED (await-put) |
| ADR-5 | WS persistent subscriptions | NOT IMPLEMENTED |

## Bugs Fixed During Development

- websocket.py subscribe KeyError (P0) — _handle_client parsing order
- InProcessMessageBus message loss (P0) — put_nowait → await queue.put
- Exception isolation in _deliver — per-message try/except

## Lessons Learned

- ADR-1/implementation mismatch discovered late — ADRs must be validated against code
- WebSocket subscribe bug was caught by coverage gap analysis, not functional testing
- Party-mode review revealed the ADR-4 discrepancy between design (drop-oldest) and implementation (await-put)
