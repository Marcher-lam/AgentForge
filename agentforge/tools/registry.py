"""Simple in-memory tool registry."""

from __future__ import annotations

from typing import Any, Callable


class SimpleToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, tuple[Callable, dict[str, Any]]] = {}

    def register(self, name: str, handler: Callable, schema: dict[str, Any]) -> None:
        """Register a tool with its handler and JSON Schema definition."""
        self._tools[name] = (handler, schema)

    def unregister(self, name: str) -> None:
        """Remove a tool by name."""
        self._tools.pop(name, None)

    def get(self, name: str) -> tuple[Callable, dict[str, Any]] | None:
        """Return (handler, schema) for a tool, or None if not found."""
        return self._tools.get(name)

    def list_tools(self) -> list[str]:
        """Return all registered tool names."""
        return list(self._tools.keys())
