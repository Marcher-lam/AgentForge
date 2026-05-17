"""Event emitter for agent state changes."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable


class EventEmitter:
    """Simple pub/sub event emitter supporting both sync and async handlers."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[Callable[..., Any]]] = defaultdict(list)

    def on(self, event: str, handler: Callable[..., Any]) -> None:
        """Register a handler for the given event."""
        self._handlers[event].append(handler)

    def off(self, event: str, handler: Callable[..., Any]) -> None:
        """Remove a previously registered handler for the given event."""
        self._handlers[event] = [h for h in self._handlers[event] if h is not handler]

    async def emit(self, event: str, *args: Any, **kwargs: Any) -> None:
        """Invoke all handlers for the given event, awaiting async ones."""
        for handler in self._handlers.get(event, []):
            result = handler(*args, **kwargs)
            if result is not None and hasattr(result, "__await__"):
                await result
