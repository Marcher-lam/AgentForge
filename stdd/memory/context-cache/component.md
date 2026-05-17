# Context Tier 2: Component Topology (~1000 tokens)

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
# State machine
AgentState: CREATED→INITIALIZED→RUNNING⇄STOPPED→DESTROYED
AgentBase: init(), run(), stop(), destroy(), events.on/off/emit()

# Bus
InProcessMessageBus: subscribe(topic, handler)→sub_id, publish(topic, msg),
                     request(topic, msg, timeout)→msg, respond(correlation_id, msg)
WebSocketMessageBus: start_server(host, port), connect(url), ws_publish/ws_subscribe

# Protocols (defined, not all implemented)
MessageBus: ✅  |  ToolRegistry: ❌  |  SkillRegistry: ❌  |  MemoryStore: ❌
```

## RL-Engine API Surface
```python
# Training
DQNTrainer(env, DQNConfig).train(max_steps) → result
PPOTrainer(env, PPOConfig).train(max_steps) → result
save_checkpoint(model, optimizer, path) / load_checkpoint(...)

# Data
Transition(obs, action, reward, next_obs, terminated, truncated, info)
ReplayBuffer(capacity).push(Transition).sample(batch_size)
RolloutBuffer().push(obs, action, reward, value, log_prob, done).compute_gae(gamma, lam)

# Networks
MLP(input_dim, output_dim, hidden=[128,128])
DuelingQNetwork(input_dim, output_dim, hidden)
ActorCriticNetwork(input_dim, action_dim, hidden)
```

## EvoForge API Surface
```python
# Engine
EvolutionEngine(fitness_fn, selection_fn, crossover_fn, mutation_fn).evolve(population)→Population

# Genomes
RealGenome(genes=np.ndarray, bounds=[(lo,hi),...])
BinaryGenome(genes=np.ndarray(bool))
TreeGenome(root=TreeNode)

# Fitness
SimpleFitness(fn), WeightedMultiObjective(objectives, weights), PenaltyFunction(constraint, factor)

# Operators
tournament_selection, roulette_selection, elite_selection, rank_selection
gaussian_mutation, uniform_mutation, polynomial_mutation, bitflip_mutation
sbx_crossover, multi_point_crossover
```

## Known Bugs & Gaps
- P0: websocket.py:54 subscribe KeyError
- P1: asyncio/anyio 混用 (12 vs 3 usage points)
- crossover.py 57% coverage | termination CC=12
- MemoryStore Protocol ≠ three-layer memory design
