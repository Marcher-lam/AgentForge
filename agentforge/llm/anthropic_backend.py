"""Anthropic Claude backend for LLM unified interface."""

from __future__ import annotations

import json
import os
from typing import Any

from agentforge.llm.protocol import (
    LLMBackend,
    LLMMessage,
    LLMRequest,
    LLMResponse,
    TokenUsage,
    ToolCall,
)


class AnthropicBackend:
    def __init__(self, model: str = "claude-sonnet-4-6", api_key: str | None = None) -> None:
        from anthropic import AsyncAnthropic

        self._client = AsyncAnthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))
        self._model = model

    async def complete(self, request: LLMRequest) -> LLMResponse:
        messages = self._format_messages(request)
        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "max_tokens": request.max_tokens,
        }
        system_content = self._extract_system(messages)
        if system_content:
            kwargs["system"] = system_content

        if request.tools:
            kwargs["tools"] = self._format_tools(request.tools)

        resp = await self._client.messages.create(**kwargs)

        tool_calls = None
        content_text = None
        for block in resp.content:
            if block.type == "text":
                content_text = block.text
            elif block.type == "tool_use":
                if tool_calls is None:
                    tool_calls = []
                tool_calls.append(
                    ToolCall(id=block.id, name=block.name, arguments=json.dumps(block.input))
                )

        return LLMResponse(
            content=content_text,
            tool_calls=tool_calls,
            usage=TokenUsage(
                prompt_tokens=resp.usage.input_tokens,
                completion_tokens=resp.usage.output_tokens,
            ),
            finish_reason=resp.stop_reason or "end_turn",
        )

    def _extract_system(self, messages: list[dict[str, Any]]) -> str | None:
        system_parts: list[str] = []
        for msg in messages:
            if msg["role"] == "system":
                system_parts.append(msg["content"])
        return " ".join(system_parts) if system_parts else None

    def _format_messages(self, request: LLMRequest) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for msg in request.messages:
            if msg.role == "system":
                continue
            d: dict[str, Any] = {"role": msg.role, "content": msg.content}
            if msg.tool_calls:
                d["content"] = [
                    {"type": "tool_use", "id": tc.id, "name": tc.name, "input": json.loads(tc.arguments)}
                    for tc in msg.tool_calls
                ]
            if msg.tool_call_id:
                d = {
                    "role": "user",
                    "content": [
                        {"type": "tool_result", "tool_use_id": msg.tool_call_id, "content": msg.content}
                    ],
                }
            result.append(d)
        return result

    def _format_tools(self, tools: list) -> list[dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.parameters,
            }
            for t in tools
        ]
