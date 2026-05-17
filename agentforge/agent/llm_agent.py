"""LLMAgent — AgentBase subclass with LLM, tools, and memory integration."""

from __future__ import annotations

import json
import uuid
from typing import Any

from agentforge.agent.base import AgentBase
from agentforge.agent.events import EventEmitter
from agentforge.bus.inprocess import InProcessMessageBus
from agentforge.llm.protocol import (
    LLMBackend,
    LLMMessage,
    LLMRequest,
    LLMResponse,
    ToolCall,
    ToolDefinition,
)
from agentforge.memory.short_term import ShortTermMemory
from agentforge.skills.registry import SkillRegistry
from agentforge.tools.registry import SimpleToolRegistry
from agentforge.types.message import Message, MessageType


class LLMAgent(AgentBase):
    def __init__(
        self,
        bus: InProcessMessageBus,
        llm: LLMBackend,
        tools: SimpleToolRegistry | None = None,
        skills: SkillRegistry | None = None,
        memory: ShortTermMemory | None = None,
        system_prompt: str = "",
        name: str = "llm_agent",
        **kwargs: Any,
    ) -> None:
        super().__init__(name=name, **kwargs)
        self.bus = bus
        self.llm = llm
        self.tools = tools or SimpleToolRegistry()
        self.skills = skills or SkillRegistry()
        self.memory = memory or ShortTermMemory()
        self.system_prompt = system_prompt
        self._history: list[LLMMessage] = []
        self._sub_ids: list[str] = []

    async def _on_init(self) -> None:
        sub = await self.bus.subscribe(
            f"agent.{self.name}.incoming",
            self._handle_message,
        )
        self._sub_ids.append(sub)

    async def _on_run(self) -> None:
        pass

    async def _on_stop(self) -> None:
        pass

    async def _on_destroy(self) -> None:
        for sid in self._sub_ids:
            await self.bus.unsubscribe(sid)
        self._sub_ids.clear()

    async def _handle_message(self, msg: Message) -> None:
        user_text = msg.payload.get("content", "")
        if not user_text:
            return
        response = await self._process(user_text)
        reply = Message(
            topic=f"agent.{self.name}.outgoing",
            sender_id=self.agent_id,
            message_type=MessageType.TEXT,
            payload={"content": response, "reply_to": str(msg.message_id)},
        )
        await self.bus.publish(f"agent.{self.name}.outgoing", reply)

    async def chat(self, user_input: str) -> str:
        """Direct call interface — for REPL mode, bypasses the bus."""
        return await self._process(user_input)

    async def _process(self, user_input: str) -> str:
        user_msg = LLMMessage(role="user", content=user_input)
        self._history.append(user_msg)
        await self.memory.store(session_id=self.name, content=user_input)

        response = await self._call_llm()

        max_tool_rounds = 5
        rounds = 0
        while response.tool_calls and rounds < max_tool_rounds:
            assistant_msg = LLMMessage(
                role="assistant",
                content=response.content or "",
                tool_calls=response.tool_calls,
            )
            self._history.append(assistant_msg)

            for tc in response.tool_calls:
                result = await self._execute_tool(tc)
                tool_msg = LLMMessage(
                    role="tool",
                    content=result,
                    tool_call_id=tc.id,
                )
                self._history.append(tool_msg)

            response = await self._call_llm()
            rounds += 1

        final_content = response.content or ""
        if final_content:
            assistant_final = LLMMessage(role="assistant", content=final_content)
            self._history.append(assistant_final)
            await self.memory.store(session_id=self.name, content=final_content)

        return final_content

    async def _call_llm(self) -> LLMResponse:
        messages: list[LLMMessage] = []

        # Build system prompt with OpenClaw skill instructions injected
        system_parts: list[str] = []
        if self.system_prompt:
            system_parts.append(self.system_prompt)

        # Inject skill instructions into system prompt
        all_skills = self.skills.list_skills()
        if all_skills:
            skill_lines = ["\n\n## Available Skills\n"]
            for s in all_skills:
                skill_lines.append(f"### {s.name}\n{s.instructions}\n")
            system_parts.append("\n".join(skill_lines))

        if system_parts:
            messages.append(LLMMessage(role="system", content="\n\n".join(system_parts)))

        recent = self._history[-20:]
        messages.extend(recent)

        tools: list[ToolDefinition] | None = None
        tool_names = self.tools.list_tools()
        if tool_names or all_skills:
            tools = []
            for name in tool_names:
                entry = self.tools.get(name)
                if entry:
                    _, schema = entry
                    desc = schema.get("description", "")
                    params = schema.get("parameters", {})
                    tools.append(ToolDefinition(name=name, description=desc, parameters=params))

            # Expose skills as callable tools with "skill_" prefix
            for s in all_skills:
                tools.append(ToolDefinition(
                    name=f"skill_{s.name}",
                    description=f"Skill: {s.name} — {s.description}",
                    parameters={"type": "object", "properties": {"input": {"type": "string", "description": "Input for the skill"}}},
                ))

        request = LLMRequest(messages=messages, tools=tools or None)
        return await self.llm.complete(request)

    async def _execute_tool(self, tc: ToolCall) -> str:
        # Check if this is a skill call
        if tc.name.startswith("skill_"):
            skill_name = tc.name[6:]  # strip "skill_" prefix
            try:
                args = json.loads(tc.arguments) if isinstance(tc.arguments, str) else tc.arguments
                result = self.skills.execute(skill_name, args)
                return json.dumps(result)
            except Exception as e:
                return json.dumps({"error": str(e)})

        # Existing tool execution logic
        entry = self.tools.get(tc.name)
        if entry is None:
            return json.dumps({"error": f"Unknown tool: {tc.name}"})
        handler, _ = entry
        try:
            args = json.loads(tc.arguments) if isinstance(tc.arguments, str) else tc.arguments
            result = handler(**args)
            if hasattr(result, "__await__"):
                result = await result
            return json.dumps({"result": result})
        except Exception as e:
            return json.dumps({"error": str(e)})
