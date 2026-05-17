# EvoRL Code Style Guide (AST-Extracted)

> Generated: 2026-05-16 | Source: 34 Python source files + 23 test files (AST deep scan)

## Project Stats

| Metric | Value |
|--------|-------|
| Source files | 34 |
| Total lines | 1,428 |
| Classes | 41 |
| Functions (sync) | 95 |
| Functions (async) | 33 |
| Tests | 231 (103 async) |
| Protocols | 6 |
| Custom exceptions | 8 |

## Naming Conventions

| Element | Style | Example | Compliance |
|---------|-------|---------|------------|
| Class | PascalCase | `InProcessMessageBus`, `EvolutionEngine` | 100% (41/41) |
| Function/Method | snake_case | `compute_gae`, `tournament_selection` | 100% |
| Constant | UPPER_SNAKE | `VALID_TRANSITIONS`, `MAX_RETRIES` | - |
| Protocol | PascalCase | `MessageBus`, `ToolRegistry` | 6 defined |
| Enum | PascalCase | `AgentState`, `MessageType` | 2 defined |
| Dataclass | PascalCase (frozen+slots) | `Message`, `Transition` | 18 defined |
| Private | _prefix | `_deliver`, `_handle_client` | consistent |
| Test class | PascalCase+Test | `TestPubSub`, `TestDQNCartPoleE2E` | 67 classes |
| Test method | snake_case+test_ | `test_basic_pub_sub`, `test_dqn_trains` | consistent |

## Design Patterns

| Pattern | Classes | Count |
|---------|---------|-------|
| State Machine | AgentBase | 1 |
| Template Method | AgentBase, InProcessMessageBus, WebSocketMessageBus | 3 |
| Observer/Pub-Sub | InProcessMessageBus | 1 |
| Protocol/Interface | FitnessFunction, Genome, MessageBus, ToolRegistry, SkillRegistry, MemoryStore | 6 |
| Facade | AgentBase, InProcessMessageBus, EvolutionEngine, ... | 7 |
| Callback | Callback, StatsCollector, CompositeCallback, ... | 6 |
| Factory | Message | 1 |

## Async Conventions

- **Runtime**: asyncio (Queue/Future) + anyio (Lock) — mixed
- **Test marker**: `@pytest.mark.anyio` (103 uses — mandatory on async tests)
- **Lock**: `anyio.Lock()` (AgentBase only)
- **Queue**: `asyncio.Queue` (InProcessMessageBus)
- **Backpressure**: `await queue.put()` (not put_nowait — fixed in this session)
- **Warning**: asyncio/anyio 混用，违反 ADR-1

## Error Handling

- Custom hierarchy: `AgentForgeError → AgentError/BusError/ConfigError`
- Specific exceptions: `InvalidStateTransition`, `AgentInitFailed`, `RpcTimeout`, `SubscriptionNotFound`
- Pattern: raise early, no silent catch in production code
- Exception isolation in _deliver is intentional (per-message try/except)
- Test asserts: `pytest.raises(InvalidStateTransition)` (13 uses)

## Anti-Patterns Detected

| Type | Location | Severity |
|------|----------|----------|
| Silent catch (intentional) | bus/inprocess.py:74, 91 | acceptable (delivery isolation) |
| God class (borderline) | AgentBase (11 methods) | watch — 4 are abstract hooks |

## Type Annotations

- mypy --strict enabled
- 319 annotations across 34 files
- `from __future__ import annotations` in 23/34 files
- All abstract methods have return annotations
- 77 docstrings on functions/methods

## Import Order

```
1. __future__ imports (23 files)
2. Standard library (asyncio, json, uuid, os, logging, collections, enum, abc)
3. Third-party (anyio, numpy, torch, pytest, websockets, dataclasses)
4. Local (agentforge.*, rlforge.*)
```

## Test Conventions

- 231 total tests: 103 async (44.6%) + 128 sync
- `@pytest.mark.anyio` mandatory for async (103/103 compliant)
- 3-layer: unit (13 files) → integration (6 files) → e2e (4 files)
- Fixtures: `rng`, `ws_port`
- Assertion: raw `assert` (407) >> `pytest.raises` (13)
- File naming: `test_<module>.py`
- No xfail markers, 1 skip (WebSocket cross-process)

## Key API Signatures

```python
# Agent lifecycle
class AgentBase(ABC):
    state: AgentState  # property
    async def init() / run() / stop() / destroy()
    async def _on_init() / _on_run() / _on_stop() / _on_destroy()  # abstract

# Message Bus
bus.subscribe(topic, handler) -> sub_id
bus.publish(topic, msg)  # backpressure: await queue.put
bus.request(topic, msg, timeout) -> msg  # RPC
bus.respond(correlation_id, msg)

# Evolution
engine.evolve(population) -> Population
engine.generation / .history / .termination_reason
```
