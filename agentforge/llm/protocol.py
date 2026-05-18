from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class ToolCall:
    id: str
    name: str
    arguments: str


@dataclass(frozen=True, slots=True)
class ToolDefinition:
    name: str
    description: str
    parameters: dict[str, Any]


@dataclass(frozen=True, slots=True)
class LLMMessage:
    role: str
    content: str
    tool_call_id: str | None = None
    tool_calls: list[ToolCall] | None = None


@dataclass(frozen=True, slots=True)
class TokenUsage:
    prompt_tokens: int
    completion_tokens: int


@dataclass(frozen=True, slots=True)
class LLMRequest:
    messages: list[LLMMessage]
    tools: list[ToolDefinition] | None = None
    temperature: float = 0.7
    max_tokens: int = 2048


@dataclass(frozen=True, slots=True)
class LLMResponse:
    content: str | None
    tool_calls: list[ToolCall] | None = None
    usage: TokenUsage = field(default_factory=lambda: TokenUsage(0, 0))
    finish_reason: str = "stop"


@runtime_checkable
class LLMBackend(Protocol):
    async def complete(self, request: LLMRequest) -> LLMResponse: ...
    def stream(self, request: LLMRequest) -> AsyncIterator[str]: ...
