"""Tests for WebSocketMessageBus — Task 4."""

import asyncio
import json
import uuid

import pytest
import websockets

from agentforge.bus.websocket import WebSocketMessageBus
from agentforge.types.message import Message, MessageType


@pytest.fixture
def ws_port(free_tcp_port_factory):
    return free_tcp_port_factory()


class TestWebSocketServer:
    @pytest.mark.anyio
    async def test_start_stop_server(self, ws_port: int):
        bus = WebSocketMessageBus()
        await bus.start_server(port=ws_port)
        assert bus._running
        await bus.stop_server()
        assert not bus._running

    @pytest.mark.anyio
    async def test_cross_process_message(self, ws_port: int):
        server_bus = WebSocketMessageBus()
        await server_bus.start_server(port=ws_port)

        received: list[Message] = []
        await server_bus.subscribe("test.ws", lambda msg: received.append(msg))

        async with websockets.connect(f"ws://127.0.0.1:{ws_port}", proxy=None) as ws:
            msg = Message(topic="test.ws", sender_id=uuid.uuid4(), message_type=MessageType.TEXT)
            await ws.send(json.dumps({"message": msg.to_json(), "topic": "test.ws"}))
            await asyncio.sleep(0.1)

        assert len(received) == 1
        assert received[0].topic == "test.ws"
        await server_bus.stop_server()

    @pytest.mark.anyio
    async def test_client_connect_disconnect(self, ws_port: int):
        server_bus = WebSocketMessageBus()
        await server_bus.start_server(port=ws_port)

        client_bus = WebSocketMessageBus()
        await client_bus.connect(f"ws://127.0.0.1:{ws_port}")
        assert client_bus._running

        await client_bus.disconnect()
        assert not client_bus._running
        await server_bus.stop_server()


class TestReconnection:
    @pytest.mark.anyio
    async def test_connect_failure_raises(self):
        bus = WebSocketMessageBus()
        with pytest.raises(ConnectionError):
            await bus.connect("ws://127.0.0.1:1")
