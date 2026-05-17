# EvoRL Context Export — Single File Bundle

> Exported: 2026-05-16 | Total ~3100 tokens | For new session bootstrapping
> Usage: Load this file first in a new session to restore full project context.

---

# ═══ TIER 1: FOUNDATION ═══

## Tech Stack
- Python 3.12 (agentforge, rlforge) | TypeScript 6 (frontend)
- PyTorch (RL training) | NumPy (evolution) | React 19 + Jotai + Tailwind
- anyio/asyncio (async runtime) | websockets (cross-process)
- structlog (logging) | pytest + anyio (Python tests) | vitest + Playwright (frontend)

## Project Structure
```
agentforge/       Agent framework (types, agent, bus, infra, evoforge)
rlforge/          RL engine (algorithms/dqn, algorithms/ppo, buffers, networks, envs)
frontend/         React UI (chat, grid, monitor, dashboard)
tests/            30 Python test files (unit/integration/e2e)
stdd/             STDD methodology artifacts (changes, specs, vision)
```

## Conventions
- BDD Gherkin specs (Given/When/Then, SHALL/MUST/SHOULD)
- `@pytest.mark.anyio` on all async Python tests
- Jotai atoms for frontend state, no Context/Redux
- frozen dataclass (slots=True) for immutable types
- Protocol (runtime_checkable) for module interfaces
- mypy --strict type checking
- STDD pipeline: proposal → specs → design → tasks → implementation

## Key Metrics (2026-05-16)
- 228 Python tests passed + 9 skipped + 41 vitest = 269 total
- 93% Python coverage | APP Mass 0.278
- 16 change records | 25+ BDD spec files

## Constitution
- A2: TDD Blocking (tests required)
- A7: Security Blocking (no hardcoded secrets)
- A9: CI/CD Blocking (full test pass required)

---

# ═══ TIER 2: COMPONENT TOPOLOGY ═══

## Module Dependency Graph
```
types ←── agent ←── bus
  ↑         ↑        ↑
  └─────────┴────────┘
       infra (independent)

rlforge standalone (imports nothing from agentforge)
evoforge inside agentforge/evoforge/
frontend standalone (connects via WebSocket)
```

## Agent-Core API Surface
```python
AgentState: CREATED→INITIALIZED→RUNNING⇄STOPPED→DESTROYED
AgentBase: init(), run(), stop(), destroy(), events.on/off/emit()
InProcessMessageBus: subscribe(topic, handler)→sub_id, publish(topic, msg),
                     request(topic, msg, timeout)→msg, respond(correlation_id, msg)
WebSocketMessageBus: start_server(host, port), connect(url), ws_publish/ws_subscribe
Protocols: MessageBus ✅ | ToolRegistry ❌ | SkillRegistry ❌ | MemoryStore ❌
```

## RL-Engine API Surface
```python
DQNTrainer(env, DQNConfig).train(max_steps) → result
PPOTrainer(env, PPOConfig).train(max_steps) → result
ReplayBuffer(capacity).push(Transition).sample(batch_size)
RolloutBuffer().push(obs, action, reward, value, log_prob, done).compute_gae(gamma, lam)
MLP(input_dim, output_dim, hidden=[128,128])
DuelingQNetwork(input_dim, output_dim, hidden)
ActorCriticNetwork(input_dim, action_dim, hidden)
```

## EvoForge API Surface
```python
EvolutionEngine(fitness_fn, selection_fn, crossover_fn, mutation_fn).evolve(pop)→Population
RealGenome(genes=np.ndarray, bounds=[(lo,hi),...])
BinaryGenome(genes=np.ndarray(bool))
SimpleFitness(fn), WeightedMultiObjective(objectives, weights), PenaltyFunction(constraint, factor)
tournament/roulette/elite/rank_selection | gaussian/uniform/polynomial/bitflip_mutation
sbx/multi_point_crossover
```

## Known Bugs & Gaps
- P0: websocket.py:54 subscribe KeyError
- P1: asyncio/anyio 混用 (12 vs 3 usage points)
- crossover.py 57% coverage | termination CC=12
- MemoryStore Protocol ≠ three-layer memory design

---

# ═══ TIER 3: ACTIVE CHANGES ═══

## change-20260516-memory-persistence [Ready for Implementation]
Three-layer memory: ShortTerm(LRU) + LongTerm(SQLite+TTL) + Vector(ChromaDB)
Module: agentforge/memory/ | New deps: aiosqlite, chromadb, sentence-transformers
5 spec files, 14 Features, 37 Scenarios | 7 Phases, ~8h

## change-20260516-oauth2-frontend [Ready for Implementation]
OAuth2 PKCE + react-router-dom + AuthGuard + token auto-refresh
Module: frontend/src/auth/ | New dep: react-router-dom v7
1 spec file, 5 Features, 12 Scenarios | 9 Phases, ~8.5h

## change-20260516-reliable-delivery [Fixed, needs archive]
Bug fix: put_nowait→await queue.put + per-message exception isolation
6 new tests, 228 total passed

## prp-20260516-evoforge-v2 [Planning Complete]
NSGA-II + Parallel Eval + Island Migration + Adaptive Operators + Termination Refactor
~16h / 6 Phases

## Critical Path
1. Fix WS subscribe bug (P0) → 2. Memory Impl → 3. OAuth2 → 4. EvoForge v2 → 5. RL RewardFunction
