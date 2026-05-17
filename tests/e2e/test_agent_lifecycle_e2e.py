"""E2E: Full agent lifecycle with bus communication.

Outside-in TDD outer shell — tests user-visible end-to-end behavior.
These tests drive the design by requiring all components to work together.

Covers specs:
  - 01-agent-lifecycle (init → run → stop → destroy)
  - 02-communication-bus (InProcess pub/sub + RPC)
  - Agent events (state_changed, started, stopped, destroyed)
"""

from __future__ import annotations

import uuid

import pytest

import anyio

from agentforge.agent.base import AgentBase
from agentforge.bus.inprocess import InProcessMessageBus
from agentforge.types.errors import InvalidStateTransition, AgentInitFailed
from agentforge.types.message import Message, MessageType
from agentforge.types.state import AgentState


# ─── Test Helpers ───


class EchoAgent(AgentBase):
    """Minimal agent that echoes messages back on the bus."""

    def __init__(self, bus: InProcessMessageBus, **kwargs):
        super().__init__(**kwargs)
        self.bus = bus
        self.received: list[Message] = []

    async def _on_init(self) -> None:
        await self.bus.subscribe("agent.echo", self._handle_echo)

    async def _on_run(self) -> None:
        pass

    async def _on_stop(self) -> None:
        pass

    async def _on_destroy(self) -> None:
        pass

    async def _handle_echo(self, msg: Message) -> None:
        self.received.append(msg)
        reply = Message(
            topic="agent.echo.reply",
            sender_id=self.agent_id,
            message_type=MessageType.TEXT,
            payload={"echo": msg.payload},
            correlation_id=msg.message_id,
        )
        await self.bus.publish("agent.echo.reply", reply)


class FailingAgent(AgentBase):
    """Agent whose _on_init raises."""

    async def _on_init(self) -> None:
        raise RuntimeError("init failure")

    async def _on_run(self) -> None:
        pass

    async def _on_stop(self) -> None:
        pass

    async def _on_destroy(self) -> None:
        pass


# ─── E2E Tests ───


class TestAgentLifecycleE2E:
    """Full lifecycle: create → init → run → stop → destroy with event tracking."""

    @pytest.mark.anyio
    async def test_full_lifecycle_with_events(self):
        """Spec: 01-agent-lifecycle — 完整生命周期事件序列"""
        bus = InProcessMessageBus()
        agent = EchoAgent(bus, name="echo-1")
        events: list[str] = []

        agent.events.on("state_changed", lambda *a: events.append(f"{a[0].value}→{a[1].value}"))

        assert agent.state == AgentState.CREATED

        await agent.init()
        assert agent.state == AgentState.INITIALIZED

        await agent.run()
        assert agent.state == AgentState.RUNNING

        await agent.stop()
        assert agent.state == AgentState.STOPPED

        await agent.run()
        assert agent.state == AgentState.RUNNING

        await agent.stop()
        assert agent.state == AgentState.STOPPED

        await agent.destroy()
        assert agent.state == AgentState.DESTROYED

        assert "created→initialized" in events
        assert "initialized→running" in events
        assert "running→stopped" in events
        assert "stopped→running" in events
        assert "stopped→destroyed" in events

    @pytest.mark.anyio
    async def test_init_failure_destroys_agent(self):
        """Spec: 01-agent-lifecycle — init 失败必须销毁重建"""
        agent = FailingAgent(name="bad")

        with pytest.raises(AgentInitFailed):
            await agent.init()

        assert agent.state == AgentState.DESTROYED

    @pytest.mark.anyio
    async def test_destroy_is_idempotent(self):
        """Spec: 01-agent-lifecycle — destroy 幂等"""
        agent = EchoAgent(InProcessMessageBus(), name="test")
        await agent.init()
        await agent.run()
        await agent.stop()
        await agent.destroy()
        await agent.destroy()
        assert agent.state == AgentState.DESTROYED

    @pytest.mark.anyio
    async def test_destroyed_agent_rejects_all_operations(self):
        """Spec: 01-agent-lifecycle — DESTROYED 是终态"""
        agent = EchoAgent(InProcessMessageBus(), name="test")
        await agent.init()
        await agent.run()
        await agent.stop()
        await agent.destroy()

        with pytest.raises(InvalidStateTransition):
            await agent.init()
        with pytest.raises(InvalidStateTransition):
            await agent.run()
        with pytest.raises(InvalidStateTransition):
            await agent.stop()


class TestAgentBusE2E:
    """Agent-to-agent communication through InProcessMessageBus."""

    @pytest.mark.anyio
    async def test_agents_communicate_via_bus(self):
        """Spec: 02-communication-bus — 跨 Agent 消息投递"""
        bus = InProcessMessageBus()
        sender = EchoAgent(bus, name="sender")
        receiver = EchoAgent(bus, name="receiver")

        await sender.init()
        await receiver.init()
        await sender.run()
        await receiver.run()

        msg = Message(
            topic="agent.echo",
            sender_id=sender.agent_id,
            message_type=MessageType.TEXT,
            payload={"text": "hello"},
        )
        await bus.publish("agent.echo", msg)
        await anyio.sleep(0)  # yield to event loop for async handler delivery

        assert len(receiver.received) == 1
        assert receiver.received[0].payload["text"] == "hello"

    @pytest.mark.anyio
    async def test_wildcard_subscription(self):
        """Spec: 02-communication-bus — 通配符订阅 agent.*"""
        bus = InProcessMessageBus()
        agent = EchoAgent(bus, name="wc")
        wildcard_msgs: list[Message] = []

        await agent.init()
        await bus.subscribe("agent.*", lambda m: wildcard_msgs.append(m))

        msg_a = Message(topic="agent.task", sender_id=agent.agent_id, message_type=MessageType.TEXT)
        msg_b = Message(topic="agent.result", sender_id=agent.agent_id, message_type=MessageType.TEXT)
        msg_c = Message(topic="system.info", sender_id=agent.agent_id, message_type=MessageType.TEXT)

        await bus.publish("agent.task", msg_a)
        await bus.publish("agent.result", msg_b)
        await bus.publish("system.info", msg_c)

        assert len(wildcard_msgs) == 2

    @pytest.mark.anyio
    async def test_message_serialization_roundtrip(self):
        """Spec: 02-communication-bus — Message JSON 序列化/反序列化"""
        original = Message(
            topic="test.topic",
            sender_id=uuid.uuid4(),
            message_type=MessageType.JSON,
            payload={"key": "value"},
            correlation_id=uuid.uuid4(),
        )
        json_dict = original.to_json()
        restored = Message.from_json(json_dict)

        assert restored.message_id == original.message_id
        assert restored.topic == original.topic
        assert restored.sender_id == original.sender_id
        assert restored.payload == original.payload
        assert restored.correlation_id == original.correlation_id
