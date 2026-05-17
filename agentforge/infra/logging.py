"""structlog configuration for AgentForge."""

from __future__ import annotations

import logging
from typing import Any

import structlog


def configure_logging(level: str = "INFO") -> None:
    """Configure structlog with console or JSON output based on level."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer() if level == "DEBUG" else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    logging.basicConfig(format="%(message)s", level=getattr(logging, level.upper()))


def get_agent_logger(agent_id: str, topic: str | None = None) -> Any:
    """Return a structlog logger bound to the given agent_id and optional topic."""
    logger = structlog.get_logger("agentforge")
    bound = logger.bind(agent_id=agent_id)
    if topic:
        bound = bound.bind(topic=topic)
    return bound
