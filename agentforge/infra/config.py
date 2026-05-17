"""Configuration loading from pyproject.toml and environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class WebSocketConfig:
    """WebSocket server host and port configuration."""
    host: str = "0.0.0.0"
    port: int = 8080


@dataclass
class LLMConfig:
    """LLM backend configuration."""
    provider: str = "openai"
    model: str = ""
    temperature: float = 0.7
    max_tokens: int = 2048
    api_key: str = ""
    base_url: str = ""


@dataclass
class AgentForgeConfig:
    """Top-level application configuration."""
    log_level: str = "INFO"
    websocket: WebSocketConfig = field(default_factory=WebSocketConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)


def load_config(project_root: Path | str | None = None) -> AgentForgeConfig:
    """Load configuration from AGENTFORGE_* environment variables."""
    config = AgentForgeConfig()
    env_overrides: dict[str, str] = {}

    for key, value in os.environ.items():
        if key.startswith("AGENTFORGE_"):
            config_key = key[len("AGENTFORGE_"):].lower()
            env_overrides[config_key] = value

    if "log_level" in env_overrides:
        config.log_level = env_overrides["log_level"]
    if "websocket_host" in env_overrides:
        config.websocket.host = env_overrides["websocket_host"]
    if "websocket_port" in env_overrides:
        config.websocket.port = int(env_overrides["websocket_port"])

    if "llm_provider" in env_overrides:
        config.llm.provider = env_overrides["llm_provider"]
    if "llm_model" in env_overrides:
        config.llm.model = env_overrides["llm_model"]
    if "llm_temperature" in env_overrides:
        config.llm.temperature = float(env_overrides["llm_temperature"])
    if "llm_max_tokens" in env_overrides:
        config.llm.max_tokens = int(env_overrides["llm_max_tokens"])
    if "llm_api_key" in env_overrides:
        config.llm.api_key = env_overrides["llm_api_key"]
    if "llm_base_url" in env_overrides:
        config.llm.base_url = env_overrides["llm_base_url"]

    return config
