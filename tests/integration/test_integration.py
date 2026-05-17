"""Integration tests — Task 6: Full lifecycle + dual-agent pub/sub + WebSocket."""

import asyncio
import json
import uuid

import pytest
import websockets

from agentforge.agent.base import AgentBase
from agentforge.bus.inprocess import InProcessMessageBus
from agentforge.bus.websocket import WebSocketMessageBus
from agentforge.infra.shutdown import GracefulShutdown
from agentforge.types.message import Message, MessageType
from agentforge.types.state import AgentState


class CommunicatingAgent(AgentBase):
    """Agent that can send/receive messages via bus."""

    def __init__(self, bus: InProcessMessageBus, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._bus = bus
        self.received: list[Message] = []

    async def _on_init(self) -> None:
        await self._bus.subscribe(
            f"agent.{self.agent_id}",
            lambda msg: self.received.append(msg),
        )

    async def _on_run(self) -> None:
        pass

    async def _on_stop(self) -> None:
        pass

    async def _on_destroy(self) -> None:
        pass

    async def send(self, target_id: uuid.UUID, payload: dict) -> None:
        msg = Message(
            topic=f"agent.{target_id}",
            sender_id=self.agent_id,
            message_type=MessageType.TEXT,
            payload=payload,
        )
        await self._bus.publish(msg.topic, msg)


class TestAgentLifecycle:
    @pytest.mark.anyio
    async def test_full_lifecycle_with_events(self):
        bus = InProcessMessageBus()
        agent = CommunicatingAgent(bus=bus, name="lifecycle-test")
        transitions: list[tuple[AgentState, AgentState]] = []
        agent.events.on("state_changed", lambda o, n: transitions.append((o, n)))

        await agent.init()
        await agent.run()
        await agent.stop()
        await agent.destroy()

        assert agent.state == AgentState.DESTROYED
        assert len(transitions) == 4
        assert transitions[0] == (AgentState.CREATED, AgentState.INITIALIZED)
        assert transitions[-1] == (AgentState.STOPPED, AgentState.DESTROYED)


class TestDualAgentPubSub:
    @pytest.mark.anyio
    async def test_two_agents_communicate(self):
        bus = InProcessMessageBus()
        agent_a = CommunicatingAgent(bus=bus, name="A")
        agent_b = CommunicatingAgent(bus=bus, name="B")

        await agent_a.init()
        await agent_b.init()

        await agent_a.send(agent_b.agent_id, {"text": "Hello B"})
        await agent_b.send(agent_a.agent_id, {"text": "Hello A"})

        assert len(agent_b.received) == 1
        assert agent_b.received[0].payload["text"] == "Hello B"
        assert len(agent_a.received) == 1
        assert agent_a.received[0].payload["text"] == "Hello A"

        await agent_a.destroy()
        await agent_b.destroy()


class TestGracefulShutdownIntegration:
    @pytest.mark.anyio
    async def test_shutdown_stops_all_agents(self):
        bus = InProcessMessageBus()
        shutdown = GracefulShutdown()

        agents = [CommunicatingAgent(bus=bus, name=f"agent-{i}") for i in range(3)]
        for agent in agents:
            shutdown.register_agent(agent)
            await agent.init()
            await agent.run()

        assert all(a.state == AgentState.RUNNING for a in agents)

        await shutdown.shutdown_all()
        assert all(a.state == AgentState.DESTROYED for a in agents)


class TestWebSocketIntegration:
    @pytest.mark.anyio
    async def test_cross_process_pub_sub(self, free_tcp_port_factory):
        port = free_tcp_port_factory()
        server_bus = WebSocketMessageBus()
        await server_bus.start_server(port=port)

        received: list[Message] = []
        await server_bus.subscribe("test.cross", lambda msg: received.append(msg))

        async with websockets.connect(f"ws://127.0.0.1:{port}", proxy=None) as ws:
            msg = Message(
                topic="test.cross",
                sender_id=uuid.uuid4(),
                message_type=MessageType.JSON,
                payload={"cross": "process"},
            )
            await ws.send(json.dumps({"message": msg.to_json(), "topic": "test.cross"}))
            await asyncio.sleep(0.2)

        assert len(received) == 1
        assert received[0].payload["cross"] == "process"
        await server_bus.stop_server()
