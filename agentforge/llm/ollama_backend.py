"""Ollama local backend for LLM unified interface."""

from __future__ import annotations

import json
from typing import Any

import httpx

from agentforge.llm.protocol import (
    LLMBackend,
    LLMMessage,
    LLMRequest,
    LLMResponse,
    TokenUsage,
    ToolCall,
)


class OllamaBackend:
    def __init__(self, model: str = "llama3", base_url: str = "http://localhost:11434") -> None:
        self._client = httpx.AsyncClient(base_url=base_url, timeout=120.0)
        self._model = model

    async def complete(self, request: LLMRequest) -> LLMResponse:
        messages = self._format_messages(request)
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens,
            },
        }
        if request.tools:
            payload["tools"] = self._format_tools(request.tools)

        resp = await self._client.post("/api/chat", json=payload)
        resp.raise_for_status()
        data = resp.json()

        tool_calls = None
        if data.get("message", {}).get("tool_calls"):
            tool_calls = [
                ToolCall(
                    id=tc.get("id", ""),
                    name=tc["function"]["name"],
                    arguments=json.dumps(tc["function"]["arguments"]),
                )
                for tc in data["message"]["tool_calls"]
            ]

        return LLMResponse(
            content=data.get("message", {}).get("content"),
            tool_calls=tool_calls,
            usage=TokenUsage(
                prompt_tokens=data.get("prompt_eval_count", 0) or 0,
                completion_tokens=data.get("eval_count", 0) or 0,
            ),
            finish_reason="stop" if data.get("done") else "incomplete",
        )

    def _format_messages(self, request: LLMRequest) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for msg in request.messages:
            d: dict[str, Any] = {"role": msg.role, "content": msg.content}
            if msg.tool_calls:
                d["tool_calls"] = [
                    {
                        "function": {
                            "name": tc.name,
                            "arguments": json.loads(tc.arguments) if isinstance(tc.arguments, str) else tc.arguments,
                        }
                    }
                    for tc in msg.tool_calls
                ]
            if msg.tool_call_id:
                d["tool_call_id"] = msg.tool_call_id
            result.append(d)
        return result

    def _format_tools(self, tools: list) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in tools
        ]
