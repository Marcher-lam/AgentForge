# Context Tier 1: Foundation (~500 tokens)

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

## Key Metrics
- 246 Python tests passed + 41 vitest = 287 total
- 93% Python coverage | APP Mass 0.278
- 16 change records | 25+ BDD spec files

## Constitution
- A2: TDD Blocking (tests required)
- A7: Security Blocking (no hardcoded secrets)
- A9: CI/CD Blocking (full test pass required)
