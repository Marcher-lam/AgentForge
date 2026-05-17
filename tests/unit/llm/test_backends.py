"""Unit tests for LLM backends (mock HTTP)."""

from __future__ import annotations

import json
import sys
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agentforge.llm.protocol import (
    LLMMessage,
    LLMRequest,
    LLMResponse,
    ToolDefinition,
)


def _setup_openai_mock():
    mock_mod = MagicMock()
    mock_mod.AsyncOpenAI = MagicMock
    sys.modules.setdefault("openai", mock_mod)
    sys.modules.setdefault("openai.resources", MagicMock())
    sys.modules.setdefault("openai.resources.chat", MagicMock())
    sys.modules.setdefault("openai.resources.chat.completions", MagicMock())
    return mock_mod


def _setup_anthropic_mock():
    mock_mod = MagicMock()
    mock_mod.AsyncAnthropic = MagicMock
    sys.modules.setdefault("anthropic", mock_mod)
    return mock_mod


class TestOpenAIBackend:
    def _make_mock_response(self, content="Hello", tool_calls=None, usage=None, finish_reason="stop"):
        choice = MagicMock()
        choice.message.content = content
        choice.message.tool_calls = tool_calls
        choice.finish_reason = finish_reason
        resp = MagicMock()
        resp.choices = [choice]
        resp.usage = usage or MagicMock(prompt_tokens=10, completion_tokens=5)
        return resp

    @pytest.mark.asyncio
    async def test_complete_basic(self):
        mock_resp = self._make_mock_response(content="Hi there!")

        mock_client_class = MagicMock()
        mock_instance = mock_client_class.return_value
        mock_instance.chat.completions.create = AsyncMock(return_value=mock_resp)

        with patch.dict(sys.modules, {"openai": MagicMock(AsyncOpenAI=mock_client_class)}):
            from agentforge.llm.openai_backend import OpenAIBackend
            backend = OpenAIBackend(model="gpt-4o-mini", api_key="test-key")
            backend._client = mock_instance

            request = LLMRequest(messages=[LLMMessage(role="user", content="Hello")])
            result = await backend.complete(request)

        assert result.content == "Hi there!"
        assert result.finish_reason == "stop"
        assert result.usage.prompt_tokens == 10

    @pytest.mark.asyncio
    async def test_complete_with_tool_calls(self):
        tc = MagicMock()
        tc.id = "call_123"
        tc.function.name = "get_weather"
        tc.function.arguments = '{"city": "Shanghai"}'
        mock_resp = self._make_mock_response(content=None, tool_calls=[tc])

        mock_client_class = MagicMock()
        mock_instance = mock_client_class.return_value
        mock_instance.chat.completions.create = AsyncMock(return_value=mock_resp)

        with patch.dict(sys.modules, {"openai": MagicMock(AsyncOpenAI=mock_client_class)}):
            from agentforge.llm.openai_backend import OpenAIBackend
            backend = OpenAIBackend(api_key="test-key")
            backend._client = mock_instance

            tools = [ToolDefinition(name="get_weather", description="Get weather", parameters={"type": "object"})]
            request = LLMRequest(messages=[LLMMessage(role="user", content="Weather?")], tools=tools)
            result = await backend.complete(request)

        assert result.tool_calls is not None
        assert result.tool_calls[0].name == "get_weather"
        assert result.tool_calls[0].arguments == '{"city": "Shanghai"}'

    @pytest.mark.asyncio
    async def test_format_messages(self):
        mock_client_class = MagicMock()
        with patch.dict(sys.modules, {"openai": MagicMock(AsyncOpenAI=mock_client_class)}):
            from agentforge.llm.openai_backend import OpenAIBackend
            backend = OpenAIBackend(api_key="test-key")

            request = LLMRequest(messages=[
                LLMMessage(role="user", content="Hello"),
                LLMMessage(role="assistant", content="Hi"),
            ])
            msgs = backend._format_messages(request)
            assert len(msgs) == 2
            assert msgs[0]["role"] == "user"
            assert msgs[1]["role"] == "assistant"

    @pytest.mark.asyncio
    async def test_format_messages_with_tool_call_id(self):
        mock_client_class = MagicMock()
        with patch.dict(sys.modules, {"openai": MagicMock(AsyncOpenAI=mock_client_class)}):
            from agentforge.llm.openai_backend import OpenAIBackend
            backend = OpenAIBackend(api_key="test-key")

            request = LLMRequest(messages=[
                LLMMessage(role="tool", content="result", tool_call_id="tc_1"),
            ])
            msgs = backend._format_messages(request)
            assert msgs[0]["tool_call_id"] == "tc_1"


class TestAnthropicBackend:
    @pytest.mark.asyncio
    async def test_complete_basic(self):
        mock_resp = MagicMock()
        text_block = MagicMock()
        text_block.type = "text"
        text_block.text = "Hello from Claude"
        mock_resp.content = [text_block]
        mock_resp.usage = MagicMock(input_tokens=15, output_tokens=8)
        mock_resp.stop_reason = "end_turn"

        mock_client_class = MagicMock()
        mock_instance = mock_client_class.return_value
        mock_instance.messages.create = AsyncMock(return_value=mock_resp)

        with patch.dict(sys.modules, {"anthropic": MagicMock(AsyncAnthropic=mock_client_class)}):
            from agentforge.llm.anthropic_backend import AnthropicBackend
            backend = AnthropicBackend(api_key="test-key")
            backend._client = mock_instance

            request = LLMRequest(
                messages=[
                    LLMMessage(role="system", content="You are helpful"),
                    LLMMessage(role="user", content="Hi"),
                ]
            )
            result = await backend.complete(request)

        assert result.content == "Hello from Claude"
        assert result.usage.prompt_tokens == 15

    @pytest.mark.asyncio
    async def test_complete_with_tool_use(self):
        tool_block = MagicMock()
        tool_block.type = "tool_use"
        tool_block.id = "tu_456"
        tool_block.name = "search"
        tool_block.input = {"query": "python"}
        mock_resp = MagicMock()
        mock_resp.content = [tool_block]
        mock_resp.usage = MagicMock(input_tokens=20, output_tokens=10)
        mock_resp.stop_reason = "tool_use"

        mock_client_class = MagicMock()
        mock_instance = mock_client_class.return_value
        mock_instance.messages.create = AsyncMock(return_value=mock_resp)

        with patch.dict(sys.modules, {"anthropic": MagicMock(AsyncAnthropic=mock_client_class)}):
            from agentforge.llm.anthropic_backend import AnthropicBackend
            backend = AnthropicBackend(api_key="test-key")
            backend._client = mock_instance

            request = LLMRequest(messages=[LLMMessage(role="user", content="Search python")])
            result = await backend.complete(request)

        assert result.tool_calls is not None
        assert result.tool_calls[0].name == "search"
        assert json.loads(result.tool_calls[0].arguments) == {"query": "python"}

    @pytest.mark.asyncio
    async def test_extract_system(self):
        mock_client_class = MagicMock()
        with patch.dict(sys.modules, {"anthropic": MagicMock(AsyncAnthropic=mock_client_class)}):
            from agentforge.llm.anthropic_backend import AnthropicBackend
            backend = AnthropicBackend(api_key="test-key")

            system = backend._extract_system([
                {"role": "system", "content": "Be helpful"},
                {"role": "system", "content": "Be safe"},
                {"role": "user", "content": "Hi"},
            ])
            assert system == "Be helpful Be safe"

    @pytest.mark.asyncio
    async def test_extract_system_none(self):
        mock_client_class = MagicMock()
        with patch.dict(sys.modules, {"anthropic": MagicMock(AsyncAnthropic=mock_client_class)}):
            from agentforge.llm.anthropic_backend import AnthropicBackend
            backend = AnthropicBackend(api_key="test-key")

            system = backend._extract_system([
                {"role": "user", "content": "Hi"},
            ])
            assert system is None


class TestOllamaBackend:
    @pytest.mark.asyncio
    async def test_complete_basic(self):
        mock_http_response = MagicMock()
        mock_http_response.json.return_value = {
            "message": {"content": "Hello from Ollama"},
            "done": True,
            "prompt_eval_count": 12,
            "eval_count": 6,
        }
        mock_http_response.raise_for_status = MagicMock()

        mock_client_class = MagicMock()
        mock_instance = mock_client_class.return_value
        mock_instance.post = AsyncMock(return_value=mock_http_response)

        with patch("agentforge.llm.ollama_backend.httpx.AsyncClient", mock_client_class):
            from agentforge.llm.ollama_backend import OllamaBackend
            backend = OllamaBackend(model="llama3")
            backend._client = mock_instance

            request = LLMRequest(messages=[LLMMessage(role="user", content="Hi")])
            result = await backend.complete(request)

        assert result.content == "Hello from Ollama"
        assert result.usage.prompt_tokens == 12
        assert result.finish_reason == "stop"

    @pytest.mark.asyncio
    async def test_complete_with_tool_calls(self):
        mock_http_response = MagicMock()
        mock_http_response.json.return_value = {
            "message": {
                "content": None,
                "tool_calls": [
                    {"id": "tc_1", "function": {"name": "calc", "arguments": {"expr": "1+1"}}}
                ],
            },
            "done": True,
            "prompt_eval_count": 10,
            "eval_count": 5,
        }
        mock_http_response.raise_for_status = MagicMock()

        mock_client_class = MagicMock()
        mock_instance = mock_client_class.return_value
        mock_instance.post = AsyncMock(return_value=mock_http_response)

        with patch("agentforge.llm.ollama_backend.httpx.AsyncClient", mock_client_class):
            from agentforge.llm.ollama_backend import OllamaBackend
            backend = OllamaBackend(model="llama3")
            backend._client = mock_instance

            request = LLMRequest(messages=[LLMMessage(role="user", content="Calc")])
            result = await backend.complete(request)

        assert result.tool_calls is not None
        assert result.tool_calls[0].name == "calc"

    @pytest.mark.asyncio
    async def test_format_tools(self):
        with patch("agentforge.llm.ollama_backend.httpx.AsyncClient"):
            from agentforge.llm.ollama_backend import OllamaBackend
            backend = OllamaBackend()
            tools = [ToolDefinition(name="t", description="d", parameters={"type": "object"})]
            result = backend._format_tools(tools)
            assert result[0]["function"]["name"] == "t"


class TestCreateBackend:
    def test_factory_openai(self):
        mock_client_class = MagicMock()
        with patch.dict(sys.modules, {"openai": MagicMock(AsyncOpenAI=mock_client_class)}):
            from agentforge.llm import create_backend
            backend = create_backend("openai", api_key="test")
            assert backend.__class__.__name__ == "OpenAIBackend"

    def test_factory_anthropic(self):
        mock_client_class = MagicMock()
        with patch.dict(sys.modules, {"anthropic": MagicMock(AsyncAnthropic=mock_client_class)}):
            from agentforge.llm import create_backend
            backend = create_backend("anthropic", api_key="test")
            assert backend.__class__.__name__ == "AnthropicBackend"

    def test_factory_ollama(self):
        with patch("agentforge.llm.ollama_backend.httpx.AsyncClient"):
            from agentforge.llm import create_backend
            backend = create_backend("ollama")
            assert backend.__class__.__name__ == "OllamaBackend"

    def test_factory_unknown_raises(self):
        from agentforge.llm import create_backend
        with pytest.raises(ValueError, match="Unknown LLM provider"):
            create_backend("nonexistent")
