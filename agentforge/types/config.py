from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class LLMOverride:
    provider_profile: str | None = None
    provider: str | None = None
    model: str | None = None
    base_url: str | None = None
    api_key: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None


@dataclass
class EvolutionConfig:
    mode: str = "agent"
    population_size: int = 50
    max_generations: int = 50
    mutation_rate: float = 0.1
    elite_size: int = 2
    genome_dim: int = 10
    seed: int = 42


@dataclass
class RLConfig:
    algorithm: str = "PPO"
    total_steps: int = 200
    learning_rate: float = 0.001
    seed: int = 42


@dataclass
class MCPServerConfig:
    server_id: str
    name: str
    description: str = ""
    connection_type: str = "stdio"
    command: str = ""
    url: str = ""
    tool_names: list[str] = field(default_factory=list)
    enabled: bool = True


@dataclass
class AgentConfig:
    llm: LLMOverride | None = None
    tool_ids: list[str] = field(default_factory=list)
    skill_ids: list[str] = field(default_factory=list)
    mcp_server_ids: list[str] = field(default_factory=list)
    evolution: EvolutionConfig | None = None
    rl: RLConfig | None = None
