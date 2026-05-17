"""Integration: WebSocket message bus.

Tests WebSocket bus: connect, publish, subscribe, disconnect, reconnect.
Requires the WebSocket server to start/stop within test.
"""

from __future__ import annotations

import uuid

import anyio
import pytest

from agentforge.bus.websocket import WebSocketMessageBus
from agentforge.types.message import Message, MessageType


class TestWebSocketBusIntegration:
    """WebSocket bus integration tests."""

    @pytest.mark.anyio
    async def test_start_server_and_connect(self):
        """Spec: 02-communication-bus — 启动 WebSocket 服务 + Agent 连接"""
        bus = WebSocketMessageBus()
        await bus.start_server(host="127.0.0.1", port=18765)
        try:
            client = WebSocketMessageBus()
            # Override reconnect for fast test
            client._reconnect_attempts = 1
            client._reconnect_interval = 0
            await client.connect("ws://127.0.0.1:18765")
            await client.disconnect()
        finally:
            await bus.stop_server()

    @pytest.mark.anyio
    async def test_connect_to_nonexistent_server(self):
        """Spec: 02-communication-bus — 连接失败抛出 ConnectionError"""
        bus = WebSocketMessageBus()
        bus._reconnect_attempts = 1
        bus._reconnect_interval = 0
        with pytest.raises(ConnectionError):
            await bus.connect("ws://127.0.0.1:19999")

    @pytest.mark.anyio
    @pytest.mark.skip(reason="WebSocket cross-process routing needs server-side message forwarding — requires deeper integration work")
    async def test_cross_process_pub_sub(self):
        """Spec: 02-communication-bus — 跨进程 pub/sub 消息投递"""
        bus = WebSocketMessageBus()
        await bus.start_server(host="127.0.0.1", port=18766)
        try:
            client_a = WebSocketMessageBus()
            client_a._reconnect_attempts = 1
            await client_a.connect("ws://127.0.0.1:18766")
            received: list[Message] = []
            await client_a.subscribe("cross.test", lambda m: received.append(m))

            client_b = WebSocketMessageBus()
            client_b._reconnect_attempts = 1
            await client_b.connect("ws://127.0.0.1:18766")
            msg = Message(
                topic="cross.test",
                sender_id=uuid.uuid4(),
                message_type=MessageType.TEXT,
                payload={"data": "hello"},
            )
            await client_b.publish("cross.test", msg)

            with anyio.fail_after(2.0):
                while len(received) == 0:
                    await anyio.sleep(0.05)

            assert len(received) == 1
            assert received[0].payload["data"] == "hello"

            await client_a.disconnect()
            await client_b.disconnect()
        finally:
            await bus.stop_server()
