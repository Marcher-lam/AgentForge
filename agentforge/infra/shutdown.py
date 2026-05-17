"""Graceful shutdown handler — SIGINT/SIGTERM."""

from __future__ import annotations

import signal
import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)


class GracefulShutdown:
    """Manages graceful shutdown of agents on SIGINT/SIGTERM."""
    def __init__(self) -> None:
        self._agents: list[Any] = []
        self._shutdown_requested = False
        self._callbacks: list[Callable[[], Any]] = []

    def register_agent(self, agent: Any) -> None:
        """Register an agent for shutdown ordering."""
        self._agents.append(agent)

    def on_shutdown(self, callback: Callable[[], Any]) -> None:
        """Register a callback to run during shutdown."""
        self._callbacks.append(callback)

    def install_handlers(self) -> None:
        """Install SIGINT and SIGTERM signal handlers."""
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def _handle_signal(self, signum: int, frame: Any) -> None:
        if self._shutdown_requested:
            return
        self._shutdown_requested = True
        logger.info("Shutdown signal received (%s), stopping agents...", signum)

    @property
    def shutdown_requested(self) -> bool:
        """Return True if a shutdown signal has been received."""
        return self._shutdown_requested

    async def shutdown_all(self) -> None:
        """Stop and destroy all registered agents in reverse order, then run callbacks."""
        for agent in reversed(self._agents):
            try:
                if hasattr(agent, "stop"):
                    await agent.stop()
                if hasattr(agent, "destroy"):
                    await agent.destroy()
            except Exception as e:
                logger.warning("Error shutting down agent: %s", e)

        for callback in self._callbacks:
            try:
                result = callback()
                if result is not None and hasattr(result, "__await__"):
                    await result
            except Exception as e:
                logger.warning("Error in shutdown callback: %s", e)
