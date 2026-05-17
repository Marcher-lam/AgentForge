"""WebSocketMessageBus — cross-process pub/sub with reconnection and heartbeat."""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from typing import Any, Callable

import websockets
from websockets.asyncio.server import Server, ServerConnection

from agentforge.bus.inprocess import InProcessMessageBus
from agentforge.types.message import Message, MessageType

logger = logging.getLogger(__name__)


class WebSocketMessageBus(InProcessMessageBus):
    """WebSocket-based message bus with reconnection and heartbeat support."""
    def __init__(self, queue_capacity: int = 1000) -> None:
        super().__init__(queue_capacity=queue_capacity)
        self._server: Server | None = None
        self._clients: dict[str, ServerConnection] = {}
        self._client_subs: dict[str, list[str]] = {}
        self._ws: websockets.asyncio.client.ClientConnection | None = None
        self._reconnect_attempts = 3
        self._reconnect_interval = 2.0
        self._heartbeat_interval = 30.0
        self._heartbeat_timeout = 60.0
        self._running = False
        self._subscribed_topics: set[str] = set()
        self._ws_url: str | None = None

    async def start_server(self, host: str = "0.0.0.0", port: int = 8080) -> None:
        """Start the WebSocket server on the given host and port."""
        self._server = await websockets.serve(self._handle_client, host, port)
        self._running = True

    async def stop_server(self) -> None:
        """Stop the WebSocket server and disconnect all clients."""
        self._running = False
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

    async def _handle_client(self, websocket: ServerConnection) -> None:
        client_id = str(uuid.uuid4())
        self._clients[client_id] = websocket
        self._client_subs[client_id] = []
        try:
            async for raw in websocket:
                data = json.loads(raw)

                if "subscribe" in data:
                    topic = data.get("topic", "")
                    sub_id = await self.subscribe(topic, lambda m, cid=client_id: self._send_to_client(cid, m))
                    self._client_subs[client_id].append(sub_id)
                else:
                    msg = Message.from_json(data["message"])
                    topic = data.get("topic", msg.topic)
                    await self.publish(topic, msg)
        except websockets.ConnectionClosed:
            pass
        finally:
            for sub_id in self._client_subs.pop(client_id, []):
                await self.unsubscribe(sub_id)
            self._clients.pop(client_id, None)

    async def _send_to_client(self, client_id: str, message: Message) -> None:
        ws = self._clients.get(client_id)
        if ws:
            try:
                await ws.send(json.dumps({"message": message.to_json(), "topic": message.topic}))
            except websockets.ConnectionClosed:
                self._clients.pop(client_id, None)

    def _persist_subs(self) -> None:
        """Persist current subscription topics for recovery after reconnect."""
        # _subscribed_topics is already maintained by ws_subscribe/ws_unsubscribe
        pass

    def _restore_subs(self) -> None:
        """Prepare stored topics — actual re-subscription happens in _reconnect_loop."""
        # No-op: the set is always up to date; used as a hook for future persistence.
        pass

    async def _reconnect_loop(self) -> None:
        """Attempt to reconnect and re-subscribe to all stored topics."""
        for attempt in range(self._reconnect_attempts):
            try:
                self._ws = await websockets.connect(self._ws_url, proxy=None)
                self._running = True
                logger.info("Reconnected to WebSocket server (attempt %d)", attempt + 1)
                # Re-subscribe to all stored topics
                for topic in list(self._subscribed_topics):
                    try:
                        await self._ws.send(json.dumps({"subscribe": True, "topic": topic}))
                    except Exception:
                        logger.warning("Failed to re-subscribe to topic %s", topic)
                # Restart heartbeat
                asyncio.create_task(self._heartbeat_loop())
                return
            except Exception:
                logger.warning("Reconnect attempt %d failed", attempt + 1)
                if attempt < self._reconnect_attempts - 1:
                    await asyncio.sleep(self._reconnect_interval)
        logger.error("All reconnect attempts failed")
        self._running = False

    async def connect(self, url: str) -> None:
        """Connect to a WebSocket server with automatic reconnection."""
        self._ws_url = url
        for attempt in range(self._reconnect_attempts):
            try:
                self._ws = await websockets.connect(url, proxy=None)
                self._running = True
                asyncio.create_task(self._heartbeat_loop())
                return
            except Exception:
                if attempt < self._reconnect_attempts - 1:
                    await asyncio.sleep(self._reconnect_interval)
        raise ConnectionError(f"Failed to connect after {self._reconnect_attempts} attempts")

    async def disconnect(self) -> None:
        """Disconnect from the WebSocket server."""
        self._running = False
        if self._ws:
            await self._ws.close()
            self._ws = None

    async def _heartbeat_loop(self) -> None:
        while self._running and self._ws:
            try:
                await asyncio.wait_for(self._ws.ping(), timeout=self._heartbeat_timeout)
            except Exception:
                logger.warning("Heartbeat failed, triggering reconnect")
                self._ws = None
                await self._reconnect_loop()
                return
            await asyncio.sleep(self._heartbeat_interval)

    async def ws_publish(self, topic: str, message: Message) -> None:
        """Publish a message via WebSocket, falling back to in-process."""
        if self._ws:
            await self._ws.send(json.dumps({"message": message.to_json(), "topic": topic}))
        else:
            await self.publish(topic, message)

    async def ws_subscribe(self, topic: str, handler: Callable[[Message], Any]) -> str:
        """Subscribe via WebSocket and register the handler locally."""
        if self._ws:
            await self._ws.send(json.dumps({"subscribe": True, "topic": topic}))
        self._subscribed_topics.add(topic)
        self._persist_subs()
        return await self.subscribe(topic, handler)

    async def ws_unsubscribe(self, topic: str, subscription_id: str) -> None:
        """Unsubscribe from a topic and remove from stored subscriptions."""
        self._subscribed_topics.discard(topic)
        self._persist_subs()
        await self.unsubscribe(subscription_id)
