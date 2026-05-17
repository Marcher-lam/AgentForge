"""Integration: Agent + InProcessMessageBus wired together.

Tests the Agent-Bus boundary without external dependencies.
Covers pub/sub, wildcard routing, unsubscribe, and RPC patterns.
"""

from __future__ import annotations

import anyio
import pytest
import uuid

from agentforge.agent.base import AgentBase
from agentforge.bus.inprocess import InProcessMessageBus
from agentforge.types.errors import RpcTimeout
from agentforge.types.message import Message, MessageType
from agentforge.types.state import AgentState


class SubscribingAgent(AgentBase):
    """Agent that subscribes to a topic and collects messages."""

    def __init__(self, bus: InProcessMessageBus, topic: str, **kwargs):
        super().__init__(**kwargs)
        self.bus = bus
        self.topic = topic
        self.received: list[Message] = []
        self._sub_id: str | None = None

    async def _on_init(self) -> None:
        self._sub_id = await self.bus.subscribe(self.topic, self._handle_sync)

    async def _on_run(self) -> None:
        pass

    async def _on_stop(self) -> None:
        pass

    async def _on_destroy(self) -> None:
        if self._sub_id:
            await self.bus.unsubscribe(self._sub_id)

    def _handle_sync(self, msg: Message) -> None:
        self.received.append(msg)


class TestAgentBusIntegration:
    """Agent + bus integration tests."""

    @pytest.mark.anyio
    async def test_agent_subscribes_and_receives(self):
        """Agent subscribes on init, receives published messages."""
        bus = InProcessMessageBus()
        agent = SubscribingAgent(bus, topic="test.topic", name="sub")

        await agent.init()
        assert agent.state == AgentState.INITIALIZED

        msg = Message(
            topic="test.topic",
            sender_id=uuid.uuid4(),
            message_type=MessageType.TEXT,
            payload={"hello": "world"},
        )
        await bus.publish("test.topic", msg)

        assert len(agent.received) == 1
        assert agent.received[0].payload["hello"] == "world"

    @pytest.mark.anyio
    async def test_multiple_agents_same_topic(self):
        """Multiple agents subscribe to same topic, all receive messages."""
        bus = InProcessMessageBus()
        agents = [SubscribingAgent(bus, topic="broadcast", name=f"a{i}") for i in range(3)]

        for a in agents:
            await a.init()

        msg = Message(topic="broadcast", sender_id=uuid.uuid4(), message_type=MessageType.TEXT)
        await bus.publish("broadcast", msg)

        for a in agents:
            assert len(a.received) == 1

    @pytest.mark.anyio
    async def test_wildcard_routing(self):
        """agent.* matches agent.task and agent.result but not system.info."""
        bus = InProcessMessageBus()
        collected: list[Message] = []
        await bus.subscribe("agent.*", lambda m: collected.append(m))

        await bus.publish("agent.task", Message(topic="agent.task", sender_id=uuid.uuid4(), message_type=MessageType.TEXT))
        await bus.publish("agent.result", Message(topic="agent.result", sender_id=uuid.uuid4(), message_type=MessageType.TEXT))
        await bus.publish("system.info", Message(topic="system.info", sender_id=uuid.uuid4(), message_type=MessageType.TEXT))

        assert len(collected) == 2

    @pytest.mark.anyio
    async def test_unsubscribe_stops_delivery(self):
        """After unsubscribe, agent no longer receives messages."""
        bus = InProcessMessageBus()
        agent = SubscribingAgent(bus, topic="test.topic", name="sub")

        await agent.init()
        await bus.publish("test.topic", Message(topic="test.topic", sender_id=uuid.uuid4(), message_type=MessageType.TEXT))
        assert len(agent.received) == 1

        await agent.destroy()  # calls unsubscribe
        await bus.publish("test.topic", Message(topic="test.topic", sender_id=uuid.uuid4(), message_type=MessageType.TEXT))
        assert len(agent.received) == 1  # no new message

    @pytest.mark.anyio
    async def test_rpc_request_response(self):
        """RPC request gets response from subscriber."""
        bus = InProcessMessageBus()

        async def rpc_handler(msg: Message) -> None:
            reply = Message(
                topic="response",
                sender_id=uuid.uuid4(),
                message_type=MessageType.TOOL_RESULT,
                payload={"result": 42},
                correlation_id=msg.correlation_id,
            )
            await bus.respond(str(msg.correlation_id), reply)

        await bus.subscribe("rpc.compute", rpc_handler)

        request = Message(
            topic="rpc.compute",
            sender_id=uuid.uuid4(),
            message_type=MessageType.TOOL_CALL,
            payload={"x": 1},
        )
        result = await bus.request("rpc.compute", request, timeout=2.0)

        assert result.payload["result"] == 42

    @pytest.mark.anyio
    async def test_rpc_timeout(self):
        """RPC request to topic with no responder times out."""
        bus = InProcessMessageBus()

        request = Message(
            topic="rpc.noone",
            sender_id=uuid.uuid4(),
            message_type=MessageType.TOOL_CALL,
        )
        with pytest.raises(RpcTimeout):
            await bus.request("rpc.noone", request, timeout=0.1)
