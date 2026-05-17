"""InProcessMessageBus — pub/sub with wildcards, RPC, backpressure."""

from __future__ import annotations

import asyncio
import json
import uuid
from collections import defaultdict
from typing import Any, Callable

import anyio

from agentforge.bus.topic_matcher import topic_matches
from agentforge.types.errors import MessageDecodeError, RpcTimeout, SubscriptionNotFound
from agentforge.types.message import Message, MessageType


class InProcessMessageBus:
    """In-process async pub/sub bus with wildcard topics, RPC, and backpressure."""

    def __init__(self, queue_capacity: int = 1000) -> None:
        self._queue_capacity = queue_capacity
        self._subscriptions: dict[str, tuple[str, Callable[[Message], Any]]] = {}
        self._topic_handlers: dict[str, list[str]] = defaultdict(list)
        self._rpc_pending: dict[str, asyncio.Future[Message]] = {}
        self._queues: dict[str, asyncio.Queue[Message]] = {}

    def _find_matching_topics(self, topic: str) -> list[str]:
        matched: list[str] = []
        for registered_topic in self._topic_handlers:
            if topic_matches(registered_topic, topic):
                matched.append(registered_topic)
        return matched

    @staticmethod
    def _validate_message(message: Message) -> None:
        """Validate message structure by round-tripping through JSON.

        Raises ``MessageDecodeError`` if the message cannot be serialized
        to JSON or is missing required fields.
        """
        try:
            data = message.to_json()
            json.dumps(data)
            required = ("message_id", "topic", "message_type", "sender_id", "timestamp")
            for field in required:
                if field not in data or data[field] is None:
                    raise MessageDecodeError(f"Missing required field: {field}")
        except MessageDecodeError:
            raise
        except (TypeError, ValueError, KeyError) as exc:
            raise MessageDecodeError(f"Invalid message format: {exc}") from exc

    async def subscribe(self, topic: str, handler: Callable[[Message], Any]) -> str:
        """Subscribe a handler to a topic pattern; returns subscription ID."""
        sub_id = str(uuid.uuid4())
        self._subscriptions[sub_id] = (topic, handler)
        self._topic_handlers[topic].append(sub_id)
        self._queues[sub_id] = asyncio.Queue(maxsize=self._queue_capacity)
        return sub_id

    async def unsubscribe(self, subscription_id: str) -> None:
        """Remove a subscription by its ID."""
        if subscription_id not in self._subscriptions:
            return
        topic, _ = self._subscriptions.pop(subscription_id)
        self._topic_handlers[topic] = [
            s for s in self._topic_handlers[topic] if s != subscription_id
        ]
        self._queues.pop(subscription_id, None)

    async def publish(self, topic: str, message: Message) -> None:
        """Publish a message to all subscribers matching the topic."""
        self._validate_message(message)
        matched_topics = self._find_matching_topics(topic)
        for matched_topic in matched_topics:
            for sub_id in self._topic_handlers.get(matched_topic, []):
                await self._deliver_to_subscriber(sub_id, topic, message)

    async def _deliver_to_subscriber(self, sub_id: str, topic: str, message: Message) -> None:
        queue = self._queues.get(sub_id)
        if queue is None:
            return
        if queue.full():
            await self._notify_delivery_failed(sub_id, topic, message)
        await queue.put(message)
        if sub_id in self._subscriptions:
            _, handler = self._subscriptions[sub_id]
            self._deliver(queue, handler)

    async def _notify_delivery_failed(self, sub_id: str, topic: str, message: Message) -> None:
        dropped = await self._drop_oldest(self._queues[sub_id])
        if dropped and sub_id in self._subscriptions:
            _, handler = self._subscriptions[sub_id]
            fail_msg = Message(
                topic=topic,
                sender_id=message.sender_id,
                message_type=MessageType.DELIVERY_FAILED,
                payload={"original_message_id": str(dropped.message_id)},
            )
            try:
                result = handler(fail_msg)
                if result is not None and hasattr(result, "__await__"):
                    await result
            except Exception:
                pass

    def _deliver(self, queue: asyncio.Queue[Message], handler: Callable[[Message], Any]) -> None:
        while not queue.empty():
            try:
                msg = queue.get_nowait()
            except asyncio.QueueEmpty:
                break
            try:
                result = handler(msg)
                if result is not None and hasattr(result, "__await__"):
                    asyncio.ensure_future(result)
            except Exception:
                pass

    async def _drop_oldest(self, queue: asyncio.Queue[Message]) -> Message | None:
        try:
            return queue.get_nowait()
        except asyncio.QueueEmpty:
            return None

    async def request(self, topic: str, message: Message, timeout: float = 5.0) -> Message:
        """Send an RPC request and wait for a response within the timeout."""
        self._validate_message(message)
        correlation_id = message.correlation_id or uuid.uuid4()
        message = Message(
            topic=message.topic,
            sender_id=message.sender_id,
            message_type=message.message_type,
            payload=message.payload,
            message_id=message.message_id,
            timestamp=message.timestamp,
            correlation_id=correlation_id,
        )
        loop = asyncio.get_event_loop()
        future: asyncio.Future[Message] = loop.create_future()
        self._rpc_pending[str(correlation_id)] = future

        await self.publish(topic, message)

        try:
            return await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError:
            self._rpc_pending.pop(str(correlation_id), None)
            raise RpcTimeout(f"RPC to {topic} timed out after {timeout}s")

    async def respond(self, correlation_id: str, response: Message) -> None:
        """Resolve a pending RPC request with the given response."""
        future = self._rpc_pending.pop(correlation_id, None)
        if future and not future.done():
            future.set_result(response)
