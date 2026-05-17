# Context Tier 3: Active Changes (~2000 tokens)

## Active Change 1: change-20260516-memory-persistence
**Status**: Ready for Implementation
**Scope**: Three-layer memory system for AgentForge

Specs generated:
- specs/short-term-memory.md (LRU cache, 3 Feature, 9 Scenario)
- specs/long-term-memory.md (SQLite persistence + TTL, 3 Feature, 9 Scenario)
- specs/vector-memory.md (ChromaDB semantic search, 2 Feature, 6 Scenario)
- specs/memory-manager.md (unified facade + promote, 3 Feature, 7 Scenario)
- specs/memory-compression.md (time-window + summary, 2 Feature, 6 Scenario)

Design decisions:
- ShortTerm: OrderedDict LRU (in-memory, session-scoped)
- LongTerm: aiosqlite (single-file, TTL, metadata query)
- Vector: ChromaDB embedded (sentence-transformers, 384-dim)
- Manager: facade with promote (atomic, rollback on failure)
- Compression: pluggable strategy (time-window, summary)

Module structure: agentforge/memory/{short_term, long_term, vector_memory, manager, compression/}
Dependencies: aiosqlite, chromadb, sentence-transformers (new deps)
Tasks: 7 Phase, 30+ items, ~8h estimate

## Active Change 2: change-20260516-oauth2-frontend
**Status**: Ready for Implementation
**Scope**: OAuth2 PKCE auth for frontend

Specs generated:
- specs/oauth2-auth.md (PKCE flow, auth guard, token mgmt, logout, API intercept)

Key changes:
- Add react-router-dom (replace tab-based navigation)
- Auth atoms: userAtom, tokenAtom, isAuthenticatedAtom
- PKCE: crypto.getRandomValues + SHA-256 Base64URL
- Token: memory + sessionStorage, auto-refresh before 30s expiry
- Routes: /login (public), /callback (public), /* (AuthGuard)

Module: frontend/src/auth/{atoms, pkce, token, api, AuthGuard, LoginPage, OAuthCallback}
Dependencies: react-router-dom v7 (new dep)

## Active Change 3: change-20260516-reliable-delivery
**Status**: Fixed (needs archive)
**Scope**: Bug fix for message loss in InProcessMessageBus

Fix applied:
1. inprocess.py:76 — put_nowait + QueueFull:pass → await queue.put (backpressure)
2. inprocess.py:84-92 — per-message try/except (exception isolation)
Tests: 6 new tests, 228 total passed, 0 failed

## PRP: prp-20260516-evoforge-v2
**Status**: Planning Complete
**Scope**: Next-gen evolution engine

6 workstreams:
1. Termination strategy pattern (CC=12→5)
2. NSGA-II Pareto multi-objective
3. Parallel fitness evaluation (ProcessPoolExecutor)
4. Island migration model
5. Adaptive operator selection
6. Integration benchmarks

Estimate: 16h / 6 Phases

## Critical Path
1. Fix WS subscribe bug (P0 blocker)
2. Memory Persistence implementation (Phase 2)
3. OAuth2 frontend implementation
4. EvoForge v2 Phase 1 (termination refactor)
5. RL RewardFunction Protocol
