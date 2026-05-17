"""Unit tests for LLMAgent (mock LLM)."""

from __future__ import annotations

import json
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from agentforge.agent.llm_agent import LLMAgent
from agentforge.bus.inprocess import InProcessMessageBus
from agentforge.llm.protocol import LLMResponse, TokenUsage, ToolCall
from agentforge.tools.registry import SimpleToolRegistry


def _make_llm_response(content="Hello!", tool_calls=None) -> LLMResponse:
    return LLMResponse(
        content=content,
        tool_calls=tool_calls,
        usage=TokenUsage(prompt_tokens=10, completion_tokens=5),
        finish_reason="stop",
    )


class TestLLMAgentUnit:
    @pytest.mark.asyncio
    async def test_chat_basic(self):
        mock_llm = AsyncMock()
        mock_llm.complete.return_value = _make_llm_response("Hi from agent!")
        bus = InProcessMessageBus()
        agent = LLMAgent(bus=bus, llm=mock_llm, name="test_agent")

        result = await agent.chat("Hello")
        assert result == "Hi from agent!"
        mock_llm.complete.assert_called_once()

    @pytest.mark.asyncio
    async def test_chat_with_system_prompt(self):
        mock_llm = AsyncMock()
        mock_llm.complete.return_value = _make_llm_response("I am helpful")
        bus = InProcessMessageBus()
        agent = LLMAgent(bus=bus, llm=mock_llm, name="test_agent", system_prompt="Be helpful")

        await agent.chat("Hi")
        call_args = mock_llm.complete.call_args[0][0]
        assert call_args.messages[0].role == "system"
        assert call_args.messages[0].content == "Be helpful"

    @pytest.mark.asyncio
    async def test_chat_with_tool_call(self):
        tc = ToolCall(id="tc_1", name="calculator", arguments='{"expr": "2+2"}')
        mock_llm = AsyncMock()
        mock_llm.complete.side_effect = [
            _make_llm_response(content=None, tool_calls=[tc]),
            _make_llm_response(content="The answer is 4"),
        ]

        tools = SimpleToolRegistry()
        tools.register("calculator", lambda expr: str(eval(expr)), {
            "description": "Calculate expression",
            "parameters": {"type": "object", "properties": {"expr": {"type": "string"}}},
        })

        bus = InProcessMessageBus()
        agent = LLMAgent(bus=bus, llm=mock_llm, tools=tools, name="test_agent")

        result = await agent.chat("What is 2+2?")
        assert result == "The answer is 4"
        assert mock_llm.complete.call_count == 2

    @pytest.mark.asyncio
    async def test_unknown_tool_returns_error(self):
        tc = ToolCall(id="tc_1", name="nonexistent", arguments="{}")
        mock_llm = AsyncMock()
        mock_llm.complete.side_effect = [
            _make_llm_response(content=None, tool_calls=[tc]),
            _make_llm_response(content="I don't have that tool"),
        ]

        bus = InProcessMessageBus()
        agent = LLMAgent(bus=bus, llm=mock_llm, name="test_agent")

        result = await agent.chat("Use nonexistent tool")
        assert result == "I don't have that tool"

    @pytest.mark.asyncio
    async def test_init_and_destroy_lifecycle(self):
        mock_llm = AsyncMock()
        mock_llm.complete.return_value = _make_llm_response()
        bus = InProcessMessageBus()
        agent = LLMAgent(bus=bus, llm=mock_llm, name="lifecycle_test")

        await agent.init()
        assert agent.state.value == "initialized"

        await agent.run()
        assert agent.state.value == "running"

        await agent.stop()
        assert agent.state.value == "stopped"

        await agent.destroy()
        assert agent.state.value == "destroyed"

    @pytest.mark.asyncio
    async def test_history_truncation(self):
        mock_llm = AsyncMock()
        mock_llm.complete.return_value = _make_llm_response("ok")
        bus = InProcessMessageBus()
        agent = LLMAgent(bus=bus, llm=mock_llm, name="test_agent")

        for i in range(25):
            await agent.chat(f"Message {i}")

        call_args = mock_llm.complete.call_args[0][0]
        history_len = len(call_args.messages) - (1 if call_args.messages[0].role == "system" else 0)
        assert history_len <= 20

    @pytest.mark.asyncio
    async def test_tool_error_handling(self):
        def bad_tool(**kwargs):
            raise ValueError("Tool crashed")

        tc = ToolCall(id="tc_1", name="bad_tool", arguments="{}")
        mock_llm = AsyncMock()
        mock_llm.complete.side_effect = [
            _make_llm_response(content=None, tool_calls=[tc]),
            _make_llm_response(content="Tool failed"),
        ]

        tools = SimpleToolRegistry()
        tools.register("bad_tool", bad_tool, {
            "description": "A tool that crashes",
            "parameters": {"type": "object", "properties": {}},
        })

        bus = InProcessMessageBus()
        agent = LLMAgent(bus=bus, llm=mock_llm, tools=tools, name="test_agent")

        result = await agent.chat("Use bad tool")
        assert result == "Tool failed"
