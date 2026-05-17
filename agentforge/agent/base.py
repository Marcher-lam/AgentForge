"""AgentBase ABC with state machine and concurrency protection."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from typing import Any

import anyio

from agentforge.agent.events import EventEmitter
from agentforge.types.errors import AgentInitFailed, InvalidStateTransition
from agentforge.types.state import AgentState, is_valid_transition


class AgentBase(ABC):
    """Abstract base class for agents with state machine and concurrency protection."""

    def __init__(self, agent_id: uuid.UUID | None = None, name: str = "") -> None:
        self.agent_id = agent_id or uuid.uuid4()
        self.name = name or self.__class__.__name__
        self._state = AgentState.CREATED
        self._lock = anyio.Lock()
        self.events = EventEmitter()

    @property
    def state(self) -> AgentState:
        """Return the current agent state."""
        return self._state

    async def _transition(self, target: AgentState) -> None:
        if not is_valid_transition(self._state, target):
            raise InvalidStateTransition(self._state.value, target.value)
        old = self._state
        self._state = target
        await self.events.emit("state_changed", old, target)

    async def init(self) -> None:
        """Transition to INITIALIZED and call user-defined _on_init."""
        async with self._lock:
            await self._transition(AgentState.INITIALIZED)
            try:
                await self._on_init()
            except Exception:
                self._state = AgentState.DESTROYED
                raise AgentInitFailed(f"Init failed for agent {self.agent_id}")

    async def run(self) -> None:
        """Transition to RUNNING and call user-defined _on_run."""
        async with self._lock:
            await self._transition(AgentState.RUNNING)
        await self._on_run()

    async def stop(self) -> None:
        """Transition to STOPPED and call user-defined _on_stop."""
        async with self._lock:
            await self._transition(AgentState.STOPPED)
        await self._on_stop()

    async def destroy(self) -> None:
        """Transition to DESTROYED and call user-defined _on_destroy."""
        async with self._lock:
            if self._state == AgentState.DESTROYED:
                return
            await self._transition(AgentState.DESTROYED)
        await self._on_destroy()

    @abstractmethod
    async def _on_init(self) -> None: ...

    @abstractmethod
    async def _on_run(self) -> None: ...

    @abstractmethod
    async def _on_stop(self) -> None: ...

    @abstractmethod
    async def _on_destroy(self) -> None: ...
