"""FastAPI application — full backend with multi-agent, settings, evolution, RL."""

from __future__ import annotations

import asyncio
import json
import math
import os
import re
import subprocess
import tempfile
import urllib.request
import urllib.error
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from agentforge.agent.llm_agent import LLMAgent
from agentforge.bus.inprocess import InProcessMessageBus
from agentforge.llm import create_backend
from agentforge.llm.protocol import LLMBackend, LLMMessage, LLMRequest
from agentforge.skills.registry import SkillRegistry
from agentforge.skills.skill_md import SkillMD, load_skill as load_skill_md
from agentforge.tools.mcp_registry import MCPToolRegistry
from agentforge.tools.registry import SimpleToolRegistry
from agentforge.types.config import AgentConfig, EvolutionConfig, LLMOverride, MCPServerConfig, RLConfig
from agentforge.types.errors import SkillNotFoundError
from agentforge.memory.manager import MemoryManager
from agentforge.memory.knowledge_base import ChromaKnowledgeBase
from agentforge.memory.chat_memory import ChatMemory


class ConnectionManager:
    def __init__(self) -> None:
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket) -> None:
        if ws in self.active:
            self.active.remove(ws)

    async def broadcast(self, data: dict) -> None:
        for ws in list(self.active):
            try:
                await ws.send_json(data)
            except Exception:
                self.disconnect(ws)


class EvolutionRun:
    """Tracks an active evolution run and streams stats via broadcast."""

    def __init__(self, run_id: str, config: dict, broadcast_fn, agent_id: str | None = None, on_complete=None) -> None:
        self.run_id = run_id
        self.config = config
        self.broadcast_fn = broadcast_fn
        self.agent_id = agent_id
        self.on_complete = on_complete
        self.status = "idle"
        self.history: list[dict] = []
        self.gene_tree: dict | None = None
        self.current_generation = 0
        self._task: asyncio.Task | None = None
        self.heatmap: dict | None = None

    def start(self) -> None:
        self.status = "running"
        self._task = asyncio.create_task(self._run())

    def cancel(self) -> None:
        self.status = "cancelled"
        if self._task:
            self._task.cancel()

    async def _run(self) -> None:
        from agentforge.evoforge.engine.evolution import EvolutionEngine
        from agentforge.evoforge.engine.population import Population, Individual
        from agentforge.evoforge.engine.termination import TerminationCriteria
        from agentforge.evoforge.engine.callbacks import Callback, GenerationStats
        import numpy as np

        cfg = self.config
        dim = cfg.get("genome_dim", 10)
        pop_size = cfg.get("population_size", 50)
        max_gen = cfg.get("max_generations", 50)
        mut_rate = cfg.get("mutation_rate", 0.1)
        mode = cfg.get("mode", "agent")  # "agent" = optimize agent params, "sphere" = classic benchmark

        run_ref = self

        if mode == "agent":
            # Agent prompt parameter optimization
            # Gene semantics: [temperature_scale, creativity, conciseness, formality,
            #   technical_depth, empathy, assertiveness, humor, detail_level, brevity]
            # Fitness = multi-objective: balance, expressiveness, no extremes
            def fitness_fn(individuals: list) -> list[float]:
                results = []
                for ind in individuals:
                    g = np.array(ind.genome.genes if hasattr(ind.genome, "genes") else ind.genome)
                    # Encode 10 agent personality traits in [0, 1] range
                    traits = 1.0 / (1.0 + np.exp(-g))  # sigmoid to [0,1]

                    # Reward balanced profiles (not all 0 or all 1)
                    balance = -np.abs(np.mean(traits) - 0.5) * 2  # peak at mean=0.5

                    # Reward diversity across traits
                    diversity = np.std(traits) * 2

                    # Penalize extreme values (any trait near 0 or 1)
                    extremes = -np.sum(np.maximum(0, traits - 0.9) + np.maximum(0, 0.1 - traits)) * 3

                    # Reward moderate correlation between certain trait pairs
                    if len(traits) >= 8:
                        coherence = -abs(traits[2] - (1 - traits[8])) * 0.5  # conciseness vs detail
                    else:
                        coherence = 0

                    fitness = balance + diversity + extremes + coherence
                    results.append(fitness)
                return results
        else:
            # Classic sphere function benchmark
            def fitness_fn(individuals: list) -> list[float]:
                results = []
                for ind in individuals:
                    g = ind.genome.genes if hasattr(ind.genome, "genes") else np.array(ind.genome)
                    results.append(-float(np.sum(g ** 2)))
                return results

        class StreamCallback(Callback):
            def on_generation_end(self, stats: GenerationStats, population) -> None:
                entry = {
                    "generation": stats.generation,
                    "best_fitness": stats.best_fitness,
                    "mean_fitness": stats.mean_fitness,
                    "std_fitness": stats.std_fitness,
                    "diversity": stats.diversity,
                }
                run_ref.history.append(entry)
                run_ref.current_generation = stats.generation

                # Build gene tree from population lineage
                nodes = []
                edges = []
                for ind in population.individuals:
                    fitness_val = ind.fitness if ind.fitness is not None else 0
                    nodes.append({
                        "id": str(ind.id),
                        "generation": ind.generation,
                        "fitness": round(fitness_val, 4),
                    })
                    for pid in ind.parents:
                        edges.append({"source": str(pid), "target": str(ind.id)})

                run_ref.gene_tree = {
                    "nodes": nodes[-min(100, len(nodes)):],  # cap at 100 nodes for UI
                    "edges": edges[-min(200, len(edges)):],
                }

                # Compute heatmap: bin gene values into a 2D grid
                all_genes = []
                for ind in population.individuals:
                    g = ind.genome.genes if hasattr(ind.genome, "genes") else np.array(ind.genome)
                    all_genes.append(np.asarray(g))
                if all_genes:
                    gene_matrix = np.array(all_genes)  # shape: (pop_size, dim)
                    n_bins = 10
                    value_min = float(gene_matrix.min())
                    value_max = float(gene_matrix.max())
                    value_range = value_max - value_min if value_max != value_min else 1.0
                    grid = np.zeros((dim, n_bins), dtype=int)
                    for gene_idx in range(min(dim, gene_matrix.shape[1])):
                        for val in gene_matrix[:, gene_idx]:
                            bin_idx = int((val - value_min) / value_range * (n_bins - 1))
                            bin_idx = max(0, min(n_bins - 1, bin_idx))
                            grid[gene_idx, bin_idx] += 1
                    run_ref.heatmap = {
                        "gene_dims": dim,
                        "individuals": len(population.individuals),
                        "values": grid.tolist(),
                    }

        engine = EvolutionEngine(
            fitness_fn=fitness_fn,
            mutation_rate=mut_rate,
            elite_size=cfg.get("elite_size", 2),
            termination=TerminationCriteria(max_generations=max_gen),
            callback=StreamCallback(),
            seed=cfg.get("seed", 42),
        )

        def genome_factory(rng):
            genes = rng.standard_normal(dim) * 0.5  # start near center
            from agentforge.evoforge.genomes.real import RealGenome
            return RealGenome(genes=genes, bounds=[(-5, 5)] * dim)

        rng = np.random.default_rng(cfg.get("seed", 42))
        population = Population.random(genome_factory, size=pop_size, rng=rng)
        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(None, engine.evolve, population)
            self.status = "completed"

            # Write best genome back to agent behavior
            if mode == "agent" and self.agent_id and population.individuals:
                import numpy as np
                best = max(population.individuals, key=lambda ind: ind.fitness if ind.fitness is not None else float("-inf"))
                best_genes = np.array(best.genome.genes if hasattr(best.genome, "genes") else best.genome)
                traits = 1.0 / (1.0 + np.exp(-best_genes))
                trait_names = ["创造力", "简洁性", "正式度", "技术深度", "同理心", "果断性", "幽默感", "细节偏好", "精简度", "亲和力"]
                trait_parts = []
                for i, name in enumerate(trait_names[:len(traits)]):
                    val = float(traits[i])
                    level = "高" if val > 0.7 else ("中" if val > 0.3 else "低")
                    trait_parts.append(f"{name}({level}:{val:.2f})")
                personality = "、".join(trait_parts)
                if self.on_complete:
                    self.on_complete(self.agent_id, personality)

        except asyncio.CancelledError:
            self.status = "cancelled"
        except Exception as e:
            self.status = f"error: {e}"

        if self.broadcast_fn:
            asyncio.ensure_future(self.broadcast_fn({
                "type": "evolution_done",
                "run_id": self.run_id,
                "status": self.status,
            }))


class RLTrainingRun:
    """Real RL training using rlforge — not simulated."""

    def __init__(self, run_id: str, config: dict, broadcast_fn, agent_id: str | None = None, on_complete=None) -> None:
        self.run_id = run_id
        self.config = config
        self.broadcast_fn = broadcast_fn
        self.agent_id = agent_id
        self.on_complete = on_complete
        self.status = "idle"
        self.metrics: dict[str, list[dict]] = {"reward": [], "loss": []}
        self.current_step = 0
        self.algorithm = config.get("algorithm", "PPO")
        self._task: asyncio.Task | None = None

    def start(self) -> None:
        self.status = "running"
        self._task = asyncio.create_task(self._run())

    def cancel(self) -> None:
        self.status = "cancelled"
        if self._task:
            self._task.cancel()

    async def _run(self) -> None:
        from agentforge.rlforge.trainer import RLTrainer, TrainingConfig

        algo_map = {"PPO": "PPO", "DQN": "DQN", "REINFORCE": "REINFORCE", "A2C": "REINFORCE"}
        algo = algo_map.get(self.algorithm, "PPO")

        config = TrainingConfig(
            algorithm=algo,
            total_steps=self.config.get("total_steps", 200),
            lr=self.config.get("learning_rate", 0.001),
            seed=self.config.get("seed", 42),
        )
        trainer = RLTrainer(config)
        run_ref = self

        def on_step(metric):
            run_ref.metrics["reward"].append({"x": metric.step, "y": round(metric.reward, 3)})
            run_ref.metrics["loss"].append({"x": metric.step, "y": round(abs(metric.loss), 3)})
            run_ref.current_step = metric.step

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: trainer.train(callback=on_step))
            self.status = "completed"
            # Save checkpoint after training
            try:
                from agentforge.rlforge.checkpoint import save_checkpoint
                import os
                ckpt_dir = os.path.join(os.getcwd(), "checkpoints")
                os.makedirs(ckpt_dir, exist_ok=True)
                ckpt_path = os.path.join(ckpt_dir, f"rl_{self.run_id[:8]}.json")
                save_checkpoint(trainer, ckpt_path)
            except Exception:
                pass
            # Write strategy back to agent (mirrors evolution writeback)
            if self.on_complete and self.agent_id:
                try:
                    strategy = self._extract_strategy()
                    self.on_complete(self.agent_id, strategy)
                except Exception:
                    pass
        except asyncio.CancelledError:
            self.status = "cancelled"
        except Exception as e:
            self.status = f"error: {e}"

        if self.broadcast_fn:
            await self.broadcast_fn({
                "type": "rl_done",
                "run_id": self.run_id,
                "status": self.status,
            })

    def _extract_strategy(self) -> dict:
        """Extract agent strategy params from RL training results."""
        import numpy as np

        rewards = [m["y"] for m in self.metrics.get("reward", [])]
        losses = [m["y"] for m in self.metrics.get("loss", [])]

        # Reward trend → conversation style tendency
        improvement = 0.0
        if len(rewards) >= 10:
            third = max(1, len(rewards) // 3)
            early = sum(rewards[:third]) / third
            late = sum(rewards[-third:]) / third
            improvement = late - early

        # Reward stability → temperature mapping
        # High variance = exploratory = high temperature
        # Low variance = stable = low temperature
        temperature = 0.7
        if len(rewards) >= 5:
            half = max(1, len(rewards) // 2)
            reward_std = float(np.std(rewards[-half:]))
            temperature = 0.3 + min(0.7, reward_std / 10)

        # Algorithm traits → strategy description
        algo_traits = {
            "PPO": {"style": "平衡型", "detail": "兼顾探索与利用，回复全面均衡"},
            "DQN": {"style": "经验型", "detail": "基于历史经验做决策，回复稳健可靠"},
            "REINFORCE": {"style": "探索型", "detail": "策略梯度驱动，回复富有创意和变化"},
        }
        trait = algo_traits.get(self.algorithm, algo_traits["PPO"])

        # Convergence → max_tokens mapping
        # Converged (low late loss) = concise = low max_tokens
        # Not converged = more expression space = high max_tokens
        max_tokens = 512
        if len(losses) >= 5:
            third = max(1, len(losses) // 3)
            late_loss = sum(losses[-third:]) / third
            max_tokens = int(256 + min(768, late_loss * 50))

        return {
            "temperature": round(temperature, 2),
            "max_tokens": max_tokens,
            "improvement": round(improvement, 2),
            "algorithm": self.algorithm,
            "style": trait["style"],
            "detail": trait["detail"],
            "reward_trend": "上升" if improvement > 0 else "稳定",
        }


class AppState:
    def __init__(self) -> None:
        self.bus = InProcessMessageBus()
        self.manager = ConnectionManager()
        self.agents: dict[str, LLMAgent] = {}
        self.sessions: list[dict] = []
        self.messages: dict[str, list[dict]] = {}
        self.llm_config: dict = {
            "provider": "openai",
            "model": "",
            "base_url": "",
            "api_key": "",
            "temperature": 0.7,
            "max_tokens": 2048,
        }
        self.evolution_runs: dict[str, EvolutionRun] = {}
        self.rl_runs: dict[str, RLTrainingRun] = {}
        self.tools_registry = MCPToolRegistry()
        skills_dir = os.path.join(os.getcwd(), "skills")
        self.skills_registry = SkillRegistry(skills_dir=skills_dir)
        self.mcp_servers: dict[str, MCPServerConfig] = {}
        self.agent_configs: dict[str, AgentConfig] = {}
        # Unified memory system
        self.memory = MemoryManager()
        # Per-session compact timeline memory (replaces raw short-term for context)
        self.chat_memory = ChatMemory()
        # Periodic cleanup of expired long-term entries (every 5 minutes)
        async def _memory_cleanup_loop():
            while True:
                await asyncio.sleep(300)
                try:
                    deleted = await self.memory.cleanup_expired()
                    if deleted:
                        logger.info("memory_cleanup", deleted=deleted)
                except Exception:
                    pass
        asyncio.create_task(_memory_cleanup_loop())
        # Per-agent knowledge base (ChromaDB + sentence-transformers)
        self.knowledge = ChromaKnowledgeBase()
        # Multi-provider LLM profiles: { "id": { id, name, provider, base_url, api_key, models } }
        self.llm_profiles: dict[str, dict[str, Any]] = {}
        # Default LLM profile from environment (always created as starting point)
        _default_id = "default"
        _default_provider = os.environ.get("LLM_PROVIDER", "openai")
        _default_model = os.environ.get("LLM_MODEL", "")
        _default_base_url = os.environ.get("LLM_BASE_URL", "")
        _default_api_key = os.environ.get("LLM_API_KEY", "")
        self.llm_profiles[_default_id] = {
            "id": _default_id,
            "name": f"默认 ({_default_provider})",
            "provider": _default_provider,
            "base_url": _default_base_url,
            "api_key": _default_api_key,
            "models": [_default_model] if _default_model else [],
        }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Built-in tool / skill handler registries ─────────────────
_BUILTIN_HANDLERS: dict[str, Any] = {}
_BUILTIN_SKILL_HANDLERS: dict[str, Any] = {}


def _resolve_tool_handler(name: str, body: dict) -> Any:
    handler_type = body.get("handler_type", "echo")
    if handler_type == "echo":
        return lambda params: {"echo": params}
    if handler_type == "builtin" and name in _BUILTIN_HANDLERS:
        return _BUILTIN_HANDLERS[name]
    return lambda params: {"result": params}


def _resolve_skill_handler(name: str, body: dict) -> Any:
    handler_type = body.get("handler_type", "echo")
    if handler_type == "echo":
        return lambda ctx: {"skill": name, "context": ctx}
    if handler_type == "builtin" and name in _BUILTIN_SKILL_HANDLERS:
        return _BUILTIN_SKILL_HANDLERS[name]
    return lambda ctx: {"skill": name, "context": ctx}


def _parse_agent_config(data: dict) -> AgentConfig:
    llm_data = data.get("llm")
    llm = LLMOverride(**{k: v for k, v in llm_data.items() if v is not None}) if llm_data else None
    evo_data = data.get("evolution")
    evolution = EvolutionConfig(**evo_data) if evo_data else None
    rl_data = data.get("rl")
    rl = RLConfig(**rl_data) if rl_data else None
    return AgentConfig(
        llm=llm,
        tool_ids=data.get("tool_ids", []),
        skill_ids=data.get("skill_ids", []),
        mcp_server_ids=data.get("mcp_server_ids", []),
        evolution=evolution,
        rl=rl,
    )


def _create_llm_for_agent(override: LLMOverride | None, global_cfg: dict, profiles: dict[str, dict] | None = None):
    if override is None:
        kwargs: dict = {}
        for k in ("model", "api_key", "base_url"):
            if global_cfg.get(k):
                kwargs[k] = global_cfg[k]
        return create_backend(global_cfg["provider"], **kwargs)

    # Resolve from profile if provider_profile is set
    profile = None
    if override.provider_profile and profiles:
        profile = profiles.get(override.provider_profile)
    elif not override.provider_profile and not override.model and profiles:
        # Auto-fallback to default profile when no explicit selection
        profile = profiles.get("default")

    if profile:
        provider = profile.get("provider", "openai")
        kwargs = {}
        if override.model:
            kwargs["model"] = override.model
        elif profile.get("models"):
            kwargs["model"] = profile["models"][0]
        for key, pkey in [("base_url", "base_url"), ("api_key", "api_key")]:
            val = getattr(override, key)
            if val:
                kwargs[key] = val
            elif profile.get(pkey):
                kwargs[key] = profile[pkey]
        return create_backend(provider, **kwargs)

    # Fallback: inline override
    provider = override.provider or global_cfg["provider"]
    kwargs = {}
    for attr, key in [("model", "model"), ("api_key", "api_key"), ("base_url", "base_url")]:
        val = getattr(override, attr)
        if val is not None:
            kwargs[key] = val
        elif global_cfg.get(key):
            kwargs[key] = global_cfg[key]
    return create_backend(provider, **kwargs)


def _wire_agent_tools(tool_ids: list[str], global_registry: MCPToolRegistry) -> SimpleToolRegistry:
    agent_tools = SimpleToolRegistry()
    for tid in tool_ids:
        if tid in global_registry._tools:
            tool_def = global_registry._tools[tid]
            schema = {"description": tool_def.get("description", ""), "parameters": tool_def.get("input_schema", {})}
            agent_tools.register(tid, tool_def["handler"], schema)
    return agent_tools


def _wire_agent_skills(skill_ids: list[str], global_skills: SkillRegistry) -> SkillRegistry:
    """Create a filtered SkillRegistry view containing only the selected skills."""
    agent_skills = SkillRegistry(skills_dir=global_skills.skills_dir)
    for sid in skill_ids:
        try:
            skill = global_skills.get(sid)
            agent_skills.install(skill)
        except SkillNotFoundError:
            pass
    return agent_skills


def _wire_mcp_tools(
    mcp_ids: list[str],
    mcp_servers: dict[str, MCPServerConfig],
    global_tools: MCPToolRegistry,
    agent_tools: SimpleToolRegistry,
) -> None:
    for sid in mcp_ids:
        server = mcp_servers.get(sid)
        if not server or not server.enabled:
            continue
        for tool_name in server.tool_names:
            if tool_name in global_tools._tools:
                tool_def = global_tools._tools[tool_name]
                schema = {"description": tool_def.get("description", ""), "parameters": tool_def.get("input_schema", {})}
                agent_tools.register(tool_name, tool_def["handler"], schema)


async def _check_relevance(agent, topic: str) -> bool:
    """Lightweight LLM call: does this agent find the topic relevant to its role?"""
    from agentforge.llm.protocol import LLMMessage, LLMRequest
    prompt = (
        f"你的角色：「{agent.name}」\n"
        f"角色专长：{agent.system_prompt[:200]}\n"
        f"用户话题：「{topic}」\n\n"
        f"严格判断：这个话题是否属于你的**核心专业领域**？\n"
        f"- 必须是只有你这个角色才能给出专业回答的话题才算 YES\n"
        f"- 泛社交（打招呼/闲聊/自我介绍）→ NO\n"
        f"- 宽泛技术话题只有最直接相关的角色回答，其他角色 → NO\n"
        f"- 如果换一个同样专业的角色也能回答 → NO\n"
        f"- 宁可漏答也不要抢答别人的专业领域\n\n"
        f"只回答 YES 或 NO。"
    )
    try:
        resp = await agent.llm.complete(LLMRequest(
            messages=[LLMMessage(role="user", content=prompt)],
            temperature=0.0, max_tokens=8,
        ))
        answer = (resp.content or "").strip().upper()
        return answer.startswith("YES") or "是" in answer
    except Exception:
        return True


def _get_agent_temperature(agent) -> float:
    """Read agent-specific temperature (RL-optimized or default 0.7)."""
    # Check if agent has a config with RL-optimized temperature
    config = getattr(agent, "_agent_config", None)
    if config and getattr(config, "llm", None) and config.llm.temperature is not None:
        return config.llm.temperature
    return 0.7


async def _web_search(query: str, top_k: int = 3) -> list[dict]:
    """Search the web via DuckDuckGo HTML (zero external deps)."""
    import urllib.parse
    results = []
    try:
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
        import re
        snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</a>', html, re.DOTALL)
        titles = re.findall(r'class="result__a"[^>]*>(.*?)</a>', html, re.DOTALL)
        for i in range(min(top_k, len(titles))):
            title = re.sub(r"<[^>]+>", "", titles[i]).strip()
            snippet = re.sub(r"<[^>]+>", "", snippets[i]).strip() if i < len(snippets) else ""
            if title:
                results.append({"title": title, "snippet": snippet[:300]})
    except Exception:
        pass
    return results


async def _agent_reply(agent, transcript: str, round_num: int, is_relevant: bool, memory: MemoryManager | None = None, knowledge: ChromaKnowledgeBase | None = None, chat_memory: ChatMemory | None = None, session_id: str = "") -> str:
    """Agentic RAG: agent autonomously decides whether to search knowledge base, web, or both."""
    from agentforge.llm.protocol import LLMMessage, LLMRequest

    if is_relevant:
        if round_num == 0:
            instruction = (
                f"你是「{agent.name}」，以下是一场讨论的记录。\n"
                f"请针对话题发表你的专业观点。用你自己的风格说话，自然、拟人、有个性。\n"
                f"你可以直接回复用户，也可以@其他智能体讨论。\n"
                f"如果你觉得问题不属于你的专业领域，但知道谁更适合回答，可以说：'这个问题我不太确定，@XXX 你应该更清楚'。\n"
                f"如果你觉得需要其他专家补充视角，可以主动@他们参与讨论。\n"
                f"要求：简洁有见地，不要重复已有观点，保持你角色的说话风格和口头禅。"
            )
        else:
            instruction = (
                f"你是「{agent.name}」，讨论已经进行了一段时间。\n"
                f"看了其他人的发言，如果你有新观点、补充、或想回应某人，请发言。\n"
                f"你也可以@其他还未发言的专家来补充视角。\n"
                f"如果没什么要补充的，只输出「PASS」。保持你的角色风格。"
            )
    else:
        instruction = (
            f"你是「{agent.name}」，这个话题不属于你的核心专业领域。\n"
            f"如果你确实有非常独特的跨界视角（必须是你这个角色才有的角度），简短说一两句。\n"
            f"否则只输出「PASS」。不要强行蹭话题。"
        )

    # ── Phase 1: Memory recall (hot: ChatMemory timeline + cold: vector) ──
    memory_context = ""
    user_query = ""  # shared with Phase 2 RAG

    # Hot layer: current session's compact timeline (≤800 chars)
    if chat_memory and session_id:
        memory_context = chat_memory.get_context(session_id, agent.name, str(agent.agent_id), budget=800)

    # Cold layer: cross-session semantic search (≤300 chars)
    cold_context = ""
    if memory and transcript:
        try:
            for line in reversed(transcript.split("\n")):
                if line.startswith("[You]") or line.startswith("User:") or line.startswith("【You】"):
                    user_query = line.split(":", 1)[-1].strip()[:150]
                    break
            if not user_query:
                user_query = transcript.split("\n")[-1][:100] if transcript else ""

            results = await memory.search(
                agent_id=str(agent.agent_id), query=user_query,
                levels=["vector"], top_k=2,
            )
            if results:
                snippets = []
                total_len = 0
                for r in results[:2]:
                    snippet = f"- {r.entry.content[:120]}"
                    if total_len + len(snippet) > 300:
                        break
                    snippets.append(snippet)
                    total_len += len(snippet)
                if snippets:
                    cold_context = "\n--- 历史相关记忆 ---\n" + "\n".join(snippets)
        except Exception:
            pass

    memory_context = memory_context + cold_context

    # ── Phase 2: Agentic RAG — LLM decides retrieval strategy ──
    rag_context = ""
    try:
        # Use user's original question, not the last agent reply
        rag_query = user_query if user_query else (transcript.split("\n")[-1][:150] if transcript else "")
        rag_prompt = (
            f"你是检索决策器。分析用户消息，判断是否需要检索。\n"
            f"用户消息：{rag_query}\n"
            f"你的角色：{agent.name}（{agent.system_prompt[:100]}）\n\n"
            f"只输出一个字母：\n"
            f"A=需要检索知识库（专业知识/技术细节/历史数据）\n"
            f"B=需要联网搜索（最新信息/新闻/实时数据）\n"
            f"C=两者都需要\n"
            f"D=不需要检索"
        )
        rag_resp = await agent.llm.complete(LLMRequest(
            messages=[LLMMessage(role="user", content=rag_prompt)],
            temperature=0.0, max_tokens=4,
        ))
        decision = (rag_resp.content or "D").strip().upper()[:1]

        if decision in ("A", "C") and knowledge:
            kb_results = knowledge.search(str(agent.agent_id), rag_query, top_k=3)
            if kb_results:
                kb_text = "\n".join([f"- [{r['score']:.2f}] {r['content'][:200]}" for r in kb_results])
                rag_context += f"\n\n--- 知识库检索结果 ---\n{kb_text}"

        if decision in ("B", "C"):
            web_results = await _web_search(rag_query, top_k=3)
            if web_results:
                web_text = "\n".join([f"- {r['title']}: {r['snippet']}" for r in web_results])
                rag_context += f"\n\n--- 联网搜索结果 ---\n{web_text}"
    except Exception:
        pass

    # ── Phase 3: Generate with full context ──
    try:
        resp = await agent.llm.complete(LLMRequest(
            messages=[
                LLMMessage(role="system", content=agent.system_prompt),
                LLMMessage(role="user", content=f"{instruction}{memory_context}{rag_context}\n\n--- 讨论记录 ---\n{transcript}\n\n--- 你的发言 ---"),
            ],
            temperature=_get_agent_temperature(agent), max_tokens=512 if is_relevant else 64,
        ))
        reply = (resp.content or "").strip()
        if reply.upper() in ("PASS", "PASS。", "PASS。", "pass"):
            return ""
        if memory:
            try:
                # Vector: only for substantive replies (semantic index for cross-session)
                if len(reply) > 100:
                    await memory.store("vector", str(agent.agent_id), key=f"vec_{round_num}", value=reply[:400])
            except Exception:
                pass
        # Record to ChatMemory timeline (shared + per-agent)
        if chat_memory and session_id:
            chat_memory.record_agent_reply(
                session_id=session_id,
                agent_id=str(agent.agent_id),
                agent_name=agent.name,
                reply=reply,
            )
        # Knowledge base: only store user-uploaded knowledge, not chat replies
        return reply
    except Exception as e:
        return f"[Error] {e}"


def _build_transcript(messages: list[dict], limit: int = 10, max_chars: int = 3000) -> str:
    """Format recent messages as a discussion transcript with char budget."""
    lines: list[str] = []
    total_chars = 0
    for msg in reversed(messages[-limit:]):
        sender = msg.get("sender_name", "?")
        content = msg.get("content", "")
        line = f"【{sender}】: {content}"
        if total_chars + len(line) > max_chars:
            # Truncate this message to fit budget
            remaining = max_chars - total_chars
            if remaining > 50:
                lines.insert(0, f"【{sender}】: {content[:remaining]}...")
            break
        lines.insert(0, line)
        total_chars += len(line)
    return "\n".join(lines)


def _make_agent_msg(session_id: str, agent_id: str, agent_name: str, content: str) -> dict:
    return {
        "message_id": str(uuid.uuid4()),
        "session_id": session_id,
        "sender_type": "AGENT",
        "sender_id": agent_id,
        "sender_name": agent_name,
        "content": content,
        "content_type": "TEXT",
        "created_at": _now(),
    }


def create_app() -> FastAPI:
    app = FastAPI(title="AgentForge API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    state = AppState()

    # ── Settings ──────────────────────────────────────────
    @app.get("/api/settings")
    async def get_settings() -> dict:
        cfg = dict(state.llm_config)
        cfg["api_key"] = "***" if cfg.get("api_key") else ""
        return cfg

    @app.put("/api/settings")
    async def update_settings(body: dict) -> dict:
        for k in ("provider", "model", "base_url", "api_key", "temperature", "max_tokens"):
            if k in body:
                state.llm_config[k] = body[k]
        return {"status": "ok"}

    # ── Agents ────────────────────────────────────────────
    @app.get("/api/agents")
    async def list_agents() -> list[dict]:
        return [
            {
                "agent_id": aid,
                "name": ag.name,
                "avatar_url": None,
                "status": "ONLINE",
                "last_message_preview": None,
                "capabilities": ["chat", "tool_use"],
                "system_prompt": ag.system_prompt,
            }
            for aid, ag in state.agents.items()
        ]

    @app.post("/api/agents")
    async def create_agent(body: dict) -> dict:
        name = body.get("name", f"agent-{len(state.agents) + 1}")
        system_prompt = body.get("system_prompt", "You are a helpful AI assistant.")
        config_data = body.get("config", {})
        agent_config = _parse_agent_config(config_data)
        agent_id = str(uuid.uuid4())

        llm = _create_llm_for_agent(agent_config.llm, state.llm_config, state.llm_profiles)
        agent_tools = _wire_agent_tools(agent_config.tool_ids, state.tools_registry)
        agent_skills = _wire_agent_skills(agent_config.skill_ids, state.skills_registry)
        _wire_mcp_tools(agent_config.mcp_server_ids, state.mcp_servers, state.tools_registry, agent_tools)

        agent = LLMAgent(
            bus=state.bus,
            llm=llm,
            tools=agent_tools,
            name=name,
            system_prompt=system_prompt,
            agent_id=uuid.UUID(agent_id),
        )
        agent.skills = agent_skills
        agent._agent_config = agent_config
        await agent.init()
        await agent.run()
        state.agents[agent_id] = agent
        state.agent_configs[agent_id] = agent_config
        try:
            state.knowledge.ensure_collection(agent_id)
        except Exception:
            pass
        return {
            "agent_id": agent_id,
            "name": name,
            "status": "ONLINE",
            "system_prompt": system_prompt,
            "config": config_data,
        }

    @app.delete("/api/agents/{agent_id}")
    async def delete_agent(agent_id: str) -> dict:
        agent = state.agents.pop(agent_id, None)
        if agent:
            await agent.stop()
            await agent.destroy()
        return {"status": "ok"}

    @app.get("/api/agents/{agent_id}")
    async def get_agent(agent_id: str) -> dict:
        agent = state.agents.get(agent_id)
        if not agent:
            return {"error": "not found"}
        config = state.agent_configs.get(agent_id)
        config_dict: dict = {}
        if config:
            config_dict = {
                "tool_ids": config.tool_ids,
                "skill_ids": config.skill_ids,
                "mcp_server_ids": config.mcp_server_ids,
            }
            if config.llm:
                from dataclasses import asdict
                config_dict["llm"] = {k: v for k, v in asdict(config.llm).items() if v is not None}
            if config.evolution:
                from dataclasses import asdict
                config_dict["evolution"] = asdict(config.evolution)
            if config.rl:
                from dataclasses import asdict
                config_dict["rl"] = asdict(config.rl)
        return {
            "agent_id": agent_id,
            "name": agent.name,
            "status": "ONLINE",
            "system_prompt": agent.system_prompt,
            "config": config_dict,
            "tools": agent.tools.list_tools() if hasattr(agent.tools, "list_tools") else [],
            "skills": [s.name for s in agent.skills.list_skills()] if hasattr(agent, "skills") and agent.skills else [],
        }

    @app.patch("/api/agents/{agent_id}")
    async def update_agent(agent_id: str, body: dict) -> dict:
        agent = state.agents.get(agent_id)
        if not agent:
            return {"error": "not found"}
        if "name" in body and body["name"]:
            agent.name = body["name"]
        if "system_prompt" in body and body["system_prompt"]:
            agent.system_prompt = body["system_prompt"]
        new_config = _parse_agent_config(body.get("config", {}))
        state.agent_configs[agent_id] = new_config
        agent_tools = _wire_agent_tools(new_config.tool_ids, state.tools_registry)
        _wire_mcp_tools(new_config.mcp_server_ids, state.mcp_servers, state.tools_registry, agent_tools)
        agent.tools = agent_tools
        return {"status": "ok"}

    @app.post("/api/agents/{agent_id}/evolution/start")
    async def start_agent_evolution(agent_id: str) -> dict:
        config = state.agent_configs.get(agent_id)
        if not config or not config.evolution:
            return {"error": "agent has no evolution config"}
        from dataclasses import asdict
        evo_cfg = asdict(config.evolution)
        run_id = str(uuid.uuid4())

        def on_evo_complete(aid: str, personality: str) -> None:
            agent = state.agents.get(aid)
            if agent:
                original = agent.system_prompt or ""
                tag_start = "\n[进化优化人格]"
                base = original.split(tag_start)[0].strip() if tag_start in original else original
                agent.system_prompt = f"{base}\n{tag_start} 基于进化算法优化，你的人格特质为：{personality}。请在回复中自然体现这些特质。 [/进化优化人格]"

        run = EvolutionRun(run_id, evo_cfg, state.manager.broadcast, agent_id=agent_id, on_complete=on_evo_complete)
        state.evolution_runs[run_id] = run
        run.start()
        return {"run_id": run_id, "status": "running", "agent_id": agent_id}

    @app.post("/api/agents/{agent_id}/rl/start")
    async def start_agent_rl(agent_id: str) -> dict:
        config = state.agent_configs.get(agent_id)
        if not config or not config.rl:
            return {"error": "agent has no RL config"}
        from dataclasses import asdict
        rl_cfg = asdict(config.rl)
        run_id = str(uuid.uuid4())

        def on_rl_complete(aid: str, strategy: dict) -> None:
            agent = state.agents.get(aid)
            if not agent:
                return

            # 1. Update Agent's LLM parameters
            cfg = state.agent_configs.get(aid)
            if cfg and cfg.llm:
                cfg.llm.temperature = strategy["temperature"]
                cfg.llm.max_tokens = strategy["max_tokens"]

            # 2. Write strategy hint to system_prompt (mirrors evolution writeback)
            original = agent.system_prompt or ""
            tag_start = "\n[RL策略优化]"
            base = original.split(tag_start)[0].strip() if tag_start in original else original
            strategy_text = (
                f"基于{strategy['algorithm']}强化学习训练优化"
                f"（奖励趋势：{strategy['reward_trend']}，"
                f"风格：{strategy['style']}），"
                f"你的对话策略为{strategy['detail']}。"
                f"请在回复中自然体现这一策略。"
            )
            agent.system_prompt = f"{base}\n{tag_start} {strategy_text} [/RL策略优化]"

        run = RLTrainingRun(run_id, rl_cfg, state.manager.broadcast, agent_id=agent_id, on_complete=on_rl_complete)
        state.rl_runs[run_id] = run
        run.start()
        return {"run_id": run_id, "status": "running", "agent_id": agent_id}

    @app.get("/api/agents/{agent_id}/evolution/runs")
    async def list_agent_evolution_runs(agent_id: str) -> list[dict]:
        runs = [r for r in state.evolution_runs.values() if r.agent_id == agent_id]
        return [
            {
                "run_id": r.run_id,
                "status": r.status,
                "current_generation": r.current_generation,
                "max_generations": r.config.get("max_generations", 0),
                "mode": r.config.get("mode", "agent"),
                "best_fitness": r.history[-1]["best_fitness"] if r.history else None,
                "created_at": r.run_id,
            }
            for r in runs
        ]

    @app.get("/api/agents/{agent_id}/rl/runs")
    async def list_agent_rl_runs(agent_id: str) -> list[dict]:
        runs = [r for r in state.rl_runs.values() if r.agent_id == agent_id]
        return [
            {
                "run_id": r.run_id,
                "status": r.status,
                "algorithm": r.algorithm,
                "current_step": r.current_step,
                "total_steps": r.config.get("total_steps", 0),
                "last_reward": r.metrics["reward"][-1]["y"] if r.metrics["reward"] else None,
                "last_loss": r.metrics["loss"][-1]["y"] if r.metrics["loss"] else None,
            }
            for r in runs
        ]

    # ── Tools CRUD ────────────────────────────────────────
    @app.get("/api/tools")
    async def list_tools() -> list[dict]:
        return state.tools_registry.list_tools()

    @app.post("/api/tools")
    async def register_tool(body: dict) -> dict:
        name = body["name"]
        input_schema = body.get("input_schema", {})
        output_schema = body.get("output_schema")
        description = body.get("description", "")
        handler = _resolve_tool_handler(name, body)
        state.tools_registry.register_tool(name, handler, input_schema, output_schema, description)
        return {"status": "ok", "name": name}

    @app.delete("/api/tools/{name}")
    async def unregister_tool(name: str) -> dict:
        state.tools_registry.unregister_tool(name)
        return {"status": "ok"}

    # ── Skills (SKILL.md native format, OpenClaw compatible) ──
    @app.get("/api/skills")
    async def list_skills() -> list[dict]:
        """List all installed skills. Each skill is a SKILL.md directory."""
        return [
            {
                "name": s.name,
                "description": s.description,
                "instructions_length": len(s.instructions),
                "source_path": s.source_path,
            }
            for s in state.skills_registry.list_skills()
        ]

    @app.post("/api/skills")
    async def install_skill(body: dict) -> dict:
        """Install a skill from SKILL.md content.

        The content must be valid SKILL.md format (YAML frontmatter + body).
        The skill is written to skills/{name}/SKILL.md and is immediately
        usable in both AgentForge and OpenClaw.
        """
        content = body.get("content", "")
        if not content:
            return {"error": "empty content — provide SKILL.md text in 'content' field"}

        skill = state.skills_registry.install_from_text(content)
        if not skill:
            return {"error": "invalid SKILL.md: must have 'name' in frontmatter"}
        return {"status": "ok", "name": skill.name, "description": skill.description}

    @app.post("/api/skills/install-path")
    async def install_skill_from_path(body: dict) -> dict:
        """Install a skill from a local file path or directory containing SKILL.md."""
        path = body.get("path", "")
        skill = load_skill_md(path)
        if not skill:
            return {"error": f"no valid SKILL.md found at {path}"}
        eligible, missing = skill.check_requirements()
        if not eligible:
            return {"error": f"requirements not met: {missing}"}
        installed_path = state.skills_registry.install(skill)
        return {"status": "ok", "name": skill.name, "description": skill.description, "path": installed_path}

    @app.post("/api/skills/install-url")
    async def install_skill_from_url(body: dict) -> dict:
        """Install a skill from a URL (GitHub repo or direct SKILL.md URL)."""
        url = body.get("url", "").strip()
        if not url:
            return {"error": "url is required"}

        raw_urls: list[str] = []

        # GitHub repo URL patterns
        gh_repo = re.match(r"https?://github\.com/([^/]+)/([^/]+)/?(?:tree/([^/]+)(?:/(.*))?)?$", url)
        if gh_repo:
            owner, repo = gh_repo.group(1), gh_repo.group(2)
            branch = gh_repo.group(3) or "main"
            subpath = gh_repo.group(4) or ""
            base = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}"
            if subpath:
                raw_urls.append(f"{base}/{subpath}/SKILL.md")
            else:
                raw_urls.append(f"{base}/SKILL.md")
                raw_urls.append(f"{base}/skills/SKILL.md")
        else:
            # Direct URL (raw file, gist, etc.)
            raw_urls.append(url)

        content = None
        errors = []
        for attempt_url in raw_urls:
            try:
                req = urllib.request.Request(attempt_url, headers={"User-Agent": "AgentForge/1.0"})
                with urllib.request.urlopen(req, timeout=15) as resp:
                    if resp.status == 200:
                        content = resp.read().decode("utf-8")
                        break
            except Exception as e:
                errors.append(f"{attempt_url}: {e}")

        if not content:
            return {"error": f"failed to fetch SKILL.md from URL. Tried: {errors}"}

        skill = state.skills_registry.install_from_text(content)
        if not skill:
            return {"error": "fetched content is not valid SKILL.md (must have 'name' in frontmatter)"}
        return {"status": "ok", "name": skill.name, "description": skill.description}

    @app.get("/api/skills/{name}")
    async def get_skill(name: str) -> dict:
        """Get a skill's full details including the raw SKILL.md content."""
        try:
            skill = state.skills_registry.get(name)
        except SkillNotFoundError:
            return {"error": "not found"}
        return {
            "name": skill.name,
            "description": skill.description,
            "instructions": skill.instructions,
            "metadata": skill.metadata,
            "source_path": skill.source_path,
            "raw": skill.to_text(),
        }

    @app.delete("/api/skills/{name}")
    async def uninstall_skill(name: str) -> dict:
        """Remove a skill directory from disk."""
        state.skills_registry.uninstall(name)
        return {"status": "ok"}

    # ── MCP Servers CRUD ──────────────────────────────────
    @app.get("/api/mcp-servers")
    async def list_mcp_servers() -> list[dict]:
        return [
            {"server_id": sid, **{k: v for k, v in cfg.__dict__.items() if k != "server_id"}}
            for sid, cfg in state.mcp_servers.items()
        ]

    @app.post("/api/mcp-servers")
    async def register_mcp_server(body: dict) -> dict:
        cfg = MCPServerConfig(
            server_id=body["server_id"],
            name=body["name"],
            description=body.get("description", ""),
            connection_type=body.get("connection_type", "stdio"),
            command=body.get("command", ""),
            url=body.get("url", ""),
            tool_names=body.get("tool_names", []),
        )
        state.mcp_servers[cfg.server_id] = cfg
        return {"status": "ok", "server_id": cfg.server_id}

    @app.delete("/api/mcp-servers/{server_id}")
    async def unregister_mcp_server(server_id: str) -> dict:
        state.mcp_servers.pop(server_id, None)
        return {"status": "ok"}

    @app.post("/api/mcp-servers/install-online")
    async def install_mcp_online(body: dict) -> dict:
        """Install an MCP server from an online source (npm package).

        Accepts { "package": "@scope/name" } or { "package": "name", "args": "..." }.
        Auto-detects tools by running `npx <package> --help` briefly, or registers
        with the package as a stdio command for lazy discovery.
        """
        package = body.get("package", "").strip()
        if not package:
            return {"error": "package is required"}

        args = body.get("args", "").strip()
        server_id = body.get("server_id", "") or re.sub(r"[^a-z0-9_-]", "_", package.lower())
        name = body.get("name", "") or package

        command = f"npx -y {package}"
        if args:
            command += f" {args}"

        # Try to discover tool names by running briefly
        tool_names: list[str] = []
        try:
            proc = subprocess.run(
                command.split(), capture_output=True, text=True, timeout=10,
                env={**os.environ, "NO_COLOR": "1"},
            )
            # Parse tool names from JSON-RPC or help output
            output = proc.stdout + proc.stderr
            for line in output.splitlines():
                # Look for tool-like names in output
                if '"name"' in line:
                    m = re.search(r'"name"\s*:\s*"([^"]+)"', line)
                    if m:
                        t = m.group(1)
                        if t not in tool_names:
                            tool_names.append(t)
        except Exception:
            pass

        cfg = MCPServerConfig(
            server_id=server_id,
            name=name,
            description=body.get("description", f"MCP server from npm: {package}"),
            connection_type="stdio",
            command=command,
            url="",
            tool_names=tool_names[:50],
        )
        state.mcp_servers[server_id] = cfg
        return {"status": "ok", "server_id": server_id, "tool_names": tool_names[:50]}

    # ── LLM Provider Profiles ─────────────────────────────
    @app.get("/api/llm-profiles")
    async def list_llm_profiles() -> list[dict]:
        """List all LLM provider profiles (api_key masked)."""
        return [
            {**p, "api_key": "***" if p.get("api_key") else ""}
            for p in state.llm_profiles.values()
        ]

    @app.post("/api/llm-profiles")
    async def create_llm_profile(body: dict) -> dict:
        profile_id = body.get("id") or str(uuid.uuid4())[:8]
        profile = {
            "id": profile_id,
            "name": body.get("name", "New Provider"),
            "provider": body.get("provider", "openai"),
            "base_url": body.get("base_url", ""),
            "api_key": body.get("api_key", ""),
            "models": body.get("models", []),
        }
        state.llm_profiles[profile_id] = profile
        return {"status": "ok", **profile}

    @app.put("/api/llm-profiles/{profile_id}")
    async def update_llm_profile(profile_id: str, body: dict) -> dict:
        existing = state.llm_profiles.get(profile_id)
        if not existing:
            return {"error": "not found"}
        for k in ("name", "provider", "base_url", "api_key", "models"):
            if k in body:
                existing[k] = body[k]
        return {"status": "ok", **existing}

    @app.delete("/api/llm-profiles/{profile_id}")
    async def delete_llm_profile(profile_id: str) -> dict:
        state.llm_profiles.pop(profile_id, None)
        return {"status": "ok"}

    # ── Sessions ──────────────────────────────────────────
    @app.get("/api/sessions")
    async def list_sessions() -> list[dict]:
        return state.sessions

    @app.post("/api/sessions")
    async def create_session(body: dict | None = None) -> dict:
        body = body or {}
        agent_ids = body.get("agent_ids")
        if not agent_ids:
            agent_ids = list(state.agents.keys())[:1]
        session_id = str(uuid.uuid4())
        session = {
            "session_id": session_id,
            "type": body.get("type", "ONE_VS_ONE"),
            "name": body.get("name", f"Chat {len(state.sessions) + 1}"),
            "agent_ids": agent_ids,
            "unread_count": 0,
            "last_message": None,
            "created_at": _now(),
            "updated_at": _now(),
        }
        state.sessions.append(session)
        state.messages[session_id] = []
        return session

    @app.get("/api/sessions/{session_id}/messages")
    async def get_messages(session_id: str) -> list[dict]:
        return state.messages.get(session_id, [])

    @app.delete("/api/sessions/{session_id}")
    async def delete_session(session_id: str) -> dict:
        state.sessions = [s for s in state.sessions if s["session_id"] != session_id]
        state.messages.pop(session_id, None)
        return {"status": "ok", "deleted": session_id}

    @app.delete("/api/sessions/{session_id}/messages/{message_id}")
    async def delete_message(session_id: str, message_id: str) -> dict:
        msgs = state.messages.get(session_id, [])
        state.messages[session_id] = [m for m in msgs if m["message_id"] != message_id]
        return {"status": "ok", "deleted": message_id}

    # ── Session Members (Group Chat) ─────────────────────
    @app.get("/api/sessions/{session_id}/members")
    async def get_session_members(session_id: str) -> dict:
        session = next((s for s in state.sessions if s["session_id"] == session_id), None)
        if not session:
            return {"error": "session not found"}
        members = []
        for aid in session.get("agent_ids", []):
            ag = state.agents.get(aid)
            if ag:
                members.append({"agent_id": aid, "name": ag.name, "status": "ONLINE"})
        return {"session_id": session_id, "members": members}

    @app.post("/api/sessions/{session_id}/members")
    async def add_session_member(session_id: str, body: dict) -> dict:
        session = next((s for s in state.sessions if s["session_id"] == session_id), None)
        if not session:
            return {"error": "session not found"}
        agent_id = body.get("agent_id")
        if not agent_id:
            return {"error": "agent_id is required"}
        if agent_id not in state.agents:
            return {"error": "agent not found"}
        if agent_id in session["agent_ids"]:
            return {"error": "agent already in session"}
        session["agent_ids"].append(agent_id)
        session["updated_at"] = _now()
        if len(session["agent_ids"]) > 1:
            session["type"] = "GROUP_BROADCAST"
        return {"status": "ok", "agent_ids": session["agent_ids"]}

    @app.delete("/api/sessions/{session_id}/members/{agent_id}")
    async def remove_session_member(session_id: str, agent_id: str) -> dict:
        session = next((s for s in state.sessions if s["session_id"] == session_id), None)
        if not session:
            return {"error": "session not found"}
        if agent_id not in session["agent_ids"]:
            return {"error": "agent not in session"}
        session["agent_ids"].remove(agent_id)
        session["updated_at"] = _now()
        if len(session["agent_ids"]) <= 1:
            session["type"] = "ONE_VS_ONE"
        return {"status": "ok", "agent_ids": session["agent_ids"]}

    @app.get("/api/sessions/{session_id}/export")
    async def export_session(session_id: str) -> dict:
        session = next((s for s in state.sessions if s["session_id"] == session_id), None)
        if not session:
            return {"error": "session not found"}
        messages = state.messages.get(session_id, [])
        agent_names = []
        for aid in session.get("agent_ids", []):
            ag = state.agents.get(aid)
            if ag:
                agent_names.append({"agent_id": aid, "name": getattr(ag, "name", aid)})
        return {
            "session": session,
            "agents": agent_names,
            "messages": messages,
            "exported_at": _now(),
            "total_messages": len(messages),
        }

    # ── Knowledge Base (Per-Agent Milvus) ──────────────
    @app.post("/api/agents/{agent_id}/knowledge")
    async def add_knowledge(agent_id: str, body: dict) -> dict:
        texts = body.get("texts", [])
        if not texts:
            return {"error": "texts is required"}
        metas = body.get("metas")
        n = state.knowledge.add(agent_id, texts=texts, metas=metas)
        return {"status": "ok", "added": n, "total": state.knowledge.count(agent_id)}

    @app.post("/api/agents/{agent_id}/knowledge/upload-json")
    async def upload_knowledge_json(agent_id: str, file: UploadFile) -> dict:
        if not file.filename.lower().endswith(".json"):
            return {"error": "only .json files are supported"}
        raw = await file.read()
        try:
            payload = json.loads(raw.decode("utf-8"))
            n = state.knowledge.add_json(agent_id, payload)
        except Exception as e:
            return {"error": f"invalid knowledge json: {e}"}
        return {"status": "ok", "added": n, "total": state.knowledge.count(agent_id)}

    @app.get("/api/agents/{agent_id}/knowledge/search")
    async def search_knowledge(agent_id: str, q: str = "", top_k: int = 5) -> dict:
        if not q:
            return {"error": "q parameter required"}
        results = state.knowledge.search(agent_id, q, top_k=top_k)
        return {"results": results, "total_docs": state.knowledge.count(agent_id)}

    @app.get("/api/agents/{agent_id}/knowledge/stats")
    async def knowledge_stats(agent_id: str) -> dict:
        return {"agent_id": agent_id, "total_docs": state.knowledge.count(agent_id)}

    @app.delete("/api/agents/{agent_id}/knowledge")
    async def clear_knowledge(agent_id: str) -> dict:
        state.knowledge.delete_collection(agent_id)
        return {"status": "ok"}

    @app.get("/api/knowledge/template")
    async def knowledge_template() -> dict:
        """Return the knowledge JSON template with examples and field descriptions."""
        import pathlib
        tpl_path = pathlib.Path(__file__).resolve().parent.parent.parent / "schemas" / "knowledge-template.json"
        if tpl_path.exists():
            return json.loads(tpl_path.read_text(encoding="utf-8"))
        return {
            "_comment": "AgentForge 知识库 JSON 模板",
            "_schema_version": "1.0",
            "documents": [{"id": "", "text": "", "source": "", "title": "", "tags": []}],
        }

    # ── Evolution ─────────────────────────────────────────
    @app.post("/api/evolution/start")
    async def start_evolution(body: dict) -> dict:
        run_id = str(uuid.uuid4())
        run = EvolutionRun(run_id, body, state.manager.broadcast)
        state.evolution_runs[run_id] = run
        run.start()
        return {"run_id": run_id, "status": "running"}

    @app.post("/api/evolution/{run_id}/cancel")
    async def cancel_evolution(run_id: str) -> dict:
        run = state.evolution_runs.get(run_id)
        if run:
            run.cancel()
        return {"status": "cancelled"}

    @app.get("/api/evolution/{run_id}")
    async def get_evolution(run_id: str) -> dict:
        run = state.evolution_runs.get(run_id)
        if not run:
            return {"error": "not found"}
        best_pts = [{"x": h["generation"], "y": h["best_fitness"]} for h in run.history]
        mean_pts = [{"x": h["generation"], "y": h["mean_fitness"]} for h in run.history]
        std_pts = [{"x": h["generation"], "y": h["std_fitness"]} for h in run.history]
        return {
            "evolution_id": run.run_id,
            "current_generation": run.current_generation,
            "status": run.status,
            "mode": run.config.get("mode", "agent"),
            "population_size": run.config.get("population_size", 0),
            "max_generations": run.config.get("max_generations", 0),
            "mutation_rate": run.config.get("mutation_rate", 0),
            "elite_size": run.config.get("elite_size", 0),
            "fitness_curves": {"best": best_pts, "mean": mean_pts, "std": std_pts},
            "gene_tree": run.gene_tree,
            "heatmap": run.heatmap,
            "logs": run.history,
            "downsampled": False,
        }

    # ── RL Training ───────────────────────────────────────
    @app.post("/api/rl/start")
    async def start_rl(body: dict) -> dict:
        run_id = str(uuid.uuid4())
        run = RLTrainingRun(run_id, body, state.manager.broadcast)
        state.rl_runs[run_id] = run
        run.start()
        return {"run_id": run_id, "status": "running"}

    @app.post("/api/rl/{run_id}/cancel")
    async def cancel_rl(run_id: str) -> dict:
        run = state.rl_runs.get(run_id)
        if run:
            run.cancel()
        return {"status": "cancelled"}

    @app.get("/api/rl/{run_id}")
    async def get_rl(run_id: str) -> dict:
        run = state.rl_runs.get(run_id)
        if not run:
            return {"error": "not found"}
        return {
            "task_id": run.run_id,
            "algorithm": run.algorithm,
            "current_step": run.current_step,
            "current_episode": run.current_step,
            "status": run.status,
            "metrics": run.metrics,
            "hyperparameters": run.config,
            "total_steps": run.config.get("total_steps", 0),
            "learning_rate": run.config.get("learning_rate", 0),
            "logs": [
                {"step": int(rw["x"]), "reward": rw["y"], "loss": ls["y"] if ls else None}
                for rw, ls in zip(
                    run.metrics.get("reward", []),
                    run.metrics.get("loss", []),
                )
            ],
            "downsampled": False,
        }

    # ── WebSocket ─────────────────────────────────────────
    @app.websocket("/ws")
    async def websocket_endpoint(ws: WebSocket) -> None:
        await state.manager.connect(ws)
        try:
            while True:
                raw = await ws.receive_text()
                data = json.loads(raw)
                msg_type = data.get("type", "chat")

                if msg_type == "chat":
                    session_id = data.get("session_id", "")
                    content = data.get("content", "")
                    if not content:
                        continue

                    user_msg = {
                        "message_id": str(uuid.uuid4()),
                        "session_id": session_id,
                        "sender_type": "USER",
                        "sender_id": None,
                        "sender_name": "You",
                        "content": content,
                        "content_type": "TEXT",
                        "created_at": _now(),
                    }
                    state.messages.setdefault(session_id, []).append(user_msg)
                    await state.manager.broadcast({"type": "message", "data": user_msg})

                    session = next((s for s in state.sessions if s["session_id"] == session_id), None)
                    if not session:
                        continue

                    agent_ids = session.get("agent_ids", [])

                    # Store user message in memory for all agents in this session
                    try:
                        for aid in agent_ids:
                            await state.memory.store("short_term", aid, key=f"msg_{user_msg['message_id'][:8]}", value=f"User: {content[:300]}")
                        # Record user question to ChatMemory timeline
                        state.chat_memory.record(session_id, "用户", "问", content[:60])
                    except Exception:
                        pass
                    if not agent_ids:
                        continue

                    agents = [(aid, state.agents[aid]) for aid in agent_ids if aid in state.agents]
                    if not agents:
                        continue

                    # Single agent: direct reply, no discussion needed
                    if len(agents) == 1:
                        aid, agent = agents[0]
                        transcript = _build_transcript(state.messages.get(session_id, []))
                        reply = await _agent_reply(agent, transcript, 0, True, memory=state.memory, knowledge=state.knowledge, chat_memory=state.chat_memory, session_id=session_id)
                        if reply:
                            agent_msg = _make_agent_msg(session_id, aid, agent.name, reply)
                            state.messages.setdefault(session_id, []).append(agent_msg)
                            session["last_message"] = agent_msg
                            session["updated_at"] = _now()
                            await state.manager.broadcast({"type": "message", "data": agent_msg})
                        continue

                    # ── Check for @mentions ──
                    mentioned_ids: list[str] = []
                    for aid, agent in agents:
                        if f"@{agent.name}" in content:
                            mentioned_ids.append(aid)

                    if mentioned_ids:
                        # Direct mention mode: only mentioned agents reply, skip relevance check
                        status_msg = {
                            "type": "system",
                            "data": {
                                "message_id": str(uuid.uuid4()),
                                "session_id": session_id,
                                "sender_type": "SYSTEM",
                                "sender_id": None,
                                "sender_name": "系统",
                                "content": f"@提及：{', '.join(state.agents[aid].name for aid in mentioned_ids)} 被点名",
                                "content_type": "SYSTEM",
                                "created_at": _now(),
                            },
                        }
                        await state.manager.broadcast(status_msg)

                        for aid in mentioned_ids:
                            agent = state.agents.get(aid)
                            if not agent:
                                continue
                            transcript = _build_transcript(state.messages.get(session_id, []))
                            reply = await _agent_reply(agent, transcript, 0, True, memory=state.memory, knowledge=state.knowledge, chat_memory=state.chat_memory, session_id=session_id)
                            if reply:
                                agent_msg = _make_agent_msg(session_id, aid, agent.name, reply)
                                state.messages.setdefault(session_id, []).append(agent_msg)
                                session["last_message"] = agent_msg
                                session["updated_at"] = _now()
                                await state.manager.broadcast({"type": "message", "data": agent_msg})
                                await asyncio.sleep(0.3)
                        continue

                    # ── Phase 1: Relevance Check (parallel) ──
                    relevance_tasks = {aid: _check_relevance(agent, content) for aid, agent in agents}
                    relevance_results = {}
                    check_futures = {aid: asyncio.create_task(_check_relevance(agent, content)) for aid, agent in agents}
                    for aid, fut in check_futures.items():
                        relevance_results[aid] = await fut

                    relevant_ids = [aid for aid, rel in relevance_results.items() if rel]
                    observer_ids = [aid for aid, rel in relevance_results.items() if not rel]

                    # Fallback: if no agent is relevant (e.g. casual greeting), pick 1-2 closest
                    if not relevant_ids:
                        relevant_ids = [aid for aid, _ in agents[:2]]
                        observer_ids = [aid for aid, _ in agents[2:]]

                    # Broadcast relevance status
                    status_msg = {
                        "type": "system",
                        "data": {
                            "message_id": str(uuid.uuid4()),
                            "session_id": session_id,
                            "sender_type": "SYSTEM",
                            "sender_id": None,
                            "sender_name": "系统",
                            "content": f"话题相关性：{', '.join(state.agents[aid].name for aid in relevant_ids)} 将参与讨论" + (f"；{', '.join(state.agents[aid].name for aid in observer_ids)} 旁观" if observer_ids else ""),
                            "content_type": "SYSTEM",
                            "created_at": _now(),
                        },
                    }
                    await state.manager.broadcast(status_msg)

                    # ── Phase 2: Core Discussion (relevant agents, multi-round) ──
                    # Track who has spoken to avoid re-triggering
                    spoken_ids: set[str] = set()
                    max_rounds = min(3, max(2, len(relevant_ids)))
                    for round_num in range(max_rounds):
                        spoke_this_round = False
                        newly_mentioned: list[str] = []

                        for aid in relevant_ids:
                            if aid in spoken_ids and round_num > 0:
                                continue  # skip those who already spoke unless new round invites them
                            agent = state.agents.get(aid)
                            if not agent:
                                continue

                            transcript = _build_transcript(state.messages.get(session_id, []))
                            reply = await _agent_reply(agent, transcript, round_num, True, memory=state.memory, knowledge=state.knowledge, chat_memory=state.chat_memory, session_id=session_id)

                            if not reply:
                                continue

                            agent_msg = _make_agent_msg(session_id, aid, agent.name, reply)
                            state.messages.setdefault(session_id, []).append(agent_msg)
                            session["last_message"] = agent_msg
                            session["updated_at"] = _now()
                            spoke_this_round = True
                            spoken_ids.add(aid)

                            await state.manager.broadcast({"type": "message", "data": agent_msg})
                            await asyncio.sleep(0.3)

                            # Detect @mentions in this reply → invite those agents
                            for other_aid, other_agent in agents:
                                if other_aid not in relevant_ids and f"@{other_agent.name}" in reply:
                                    newly_mentioned.append(other_aid)

                        # Add newly @mentioned agents to the discussion for next rounds
                        if newly_mentioned:
                            for new_aid in newly_mentioned:
                                if new_aid not in relevant_ids:
                                    relevant_ids.append(new_aid)
                                    if new_aid in observer_ids:
                                        observer_ids.remove(new_aid)

                        if not spoke_this_round:
                            break

                    # ── Phase 2.5: @mention chain — agents mentioned by others get to respond ──
                    chain_depth = 0
                    while chain_depth < 3:
                        chain_mentions: list[str] = []
                        # Check last batch of messages for new @mentions of agents who haven't spoken
                        recent = state.messages.get(session_id, [])
                        for msg in reversed(recent):
                            if msg.get("sender_type") != "AGENT":
                                continue
                            sender_id = msg.get("sender_id")
                            content = msg.get("content", "")
                            for other_aid, other_agent in agents:
                                if other_aid not in spoken_ids and f"@{other_agent.name}" in content:
                                    if other_aid not in chain_mentions:
                                        chain_mentions.append(other_aid)

                        if not chain_mentions:
                            break

                        for aid in chain_mentions:
                            agent = state.agents.get(aid)
                            if not agent:
                                continue

                            transcript = _build_transcript(state.messages.get(session_id, []))
                            reply = await _agent_reply(agent, transcript, 0, True, memory=state.memory, knowledge=state.knowledge, chat_memory=state.chat_memory, session_id=session_id)

                            if not reply:
                                continue

                            agent_msg = _make_agent_msg(session_id, aid, agent.name, reply)
                            state.messages.setdefault(session_id, []).append(agent_msg)
                            session["last_message"] = agent_msg
                            session["updated_at"] = _now()
                            spoken_ids.add(aid)

                            await state.manager.broadcast({"type": "message", "data": agent_msg})
                            await asyncio.sleep(0.3)

                        chain_depth += 1

                    # ── Phase 3: Observer Commentary (optional) ──
                    for aid in observer_ids:
                        agent = state.agents.get(aid)
                        if not agent:
                            continue

                        transcript = _build_transcript(state.messages.get(session_id, []))
                        reply = await _agent_reply(agent, transcript, 99, False, memory=state.memory, knowledge=state.knowledge, chat_memory=state.chat_memory, session_id=session_id)

                        if not reply:
                            continue

                        agent_msg = _make_agent_msg(session_id, aid, agent.name, reply)
                        state.messages.setdefault(session_id, []).append(agent_msg)
                        session["last_message"] = agent_msg
                        session["updated_at"] = _now()

                        await state.manager.broadcast({"type": "message", "data": agent_msg})

        except WebSocketDisconnect:
            state.manager.disconnect(ws)

    app.state.agentforge = state
    return app
