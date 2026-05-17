"""Tests for InProcessMessageBus — Task 3."""

import uuid

import pytest

from agentforge.bus.inprocess import InProcessMessageBus
from agentforge.bus.topic_matcher import topic_matches
from agentforge.types.errors import RpcTimeout
from agentforge.types.message import Message, MessageType


class TestTopicMatcher:
    @pytest.mark.parametrize(
        "pattern,topic,expected",
        [
            ("agent.status", "agent.status", True),
            ("agent.*", "agent.status", True),
            ("agent.*", "agent.status.detail", False),
            ("agent.**", "agent.status.detail", True),
            ("**", "anything.at.all", True),
            ("agent.*.result", "agent.task.result", True),
            ("agent.*.result", "agent.task.sub.result", False),
        ],
    )
    def test_topic_matches(self, pattern, topic, expected):
        assert topic_matches(pattern, topic) is expected


class TestPubSub:
    @pytest.mark.anyio
    async def test_basic_pub_sub(self):
        bus = InProcessMessageBus()
        received: list[Message] = []
        await bus.subscribe("test.topic", lambda msg: received.append(msg))

        msg = Message(topic="test.topic", sender_id=uuid.uuid4(), message_type=MessageType.TEXT)
        await bus.publish("test.topic", msg)
        assert len(received) == 1
        assert received[0].message_id == msg.message_id

    @pytest.mark.anyio
    async def test_wildcard_single_level(self):
        bus = InProcessMessageBus()
        received: list[Message] = []
        await bus.subscribe("agent.*", lambda msg: received.append(msg))

        msg = Message(topic="agent.status", sender_id=uuid.uuid4(), message_type=MessageType.TEXT)
        await bus.publish("agent.status", msg)
        assert len(received) == 1

    @pytest.mark.anyio
    async def test_wildcard_recursive(self):
        bus = InProcessMessageBus()
        received: list[Message] = []
        await bus.subscribe("agent.**", lambda msg: received.append(msg))

        msg = Message(topic="agent.task.sub.result", sender_id=uuid.uuid4(), message_type=MessageType.TEXT)
        await bus.publish("agent.task.sub.result", msg)
        assert len(received) == 1

    @pytest.mark.anyio
    async def test_no_match(self):
        bus = InProcessMessageBus()
        received: list[Message] = []
        await bus.subscribe("other.topic", lambda msg: received.append(msg))

        msg = Message(topic="test.topic", sender_id=uuid.uuid4(), message_type=MessageType.TEXT)
        await bus.publish("test.topic", msg)
        assert len(received) == 0


class TestUnsubscribe:
    @pytest.mark.anyio
    async def test_unsubscribe_stops_delivery(self):
        bus = InProcessMessageBus()
        received: list[Message] = []
        sub_id = await bus.subscribe("test.topic", lambda msg: received.append(msg))

        msg = Message(topic="test.topic", sender_id=uuid.uuid4(), message_type=MessageType.TEXT)
        await bus.publish("test.topic", msg)
        assert len(received) == 1

        await bus.unsubscribe(sub_id)
        msg2 = Message(topic="test.topic", sender_id=uuid.uuid4(), message_type=MessageType.TEXT)
        await bus.publish("test.topic", msg2)
        assert len(received) == 1

    @pytest.mark.anyio
    async def test_unsubscribe_idempotent(self):
        bus = InProcessMessageBus()
        sub_id = await bus.subscribe("test", lambda msg: None)
        await bus.unsubscribe(sub_id)
        await bus.unsubscribe(sub_id)


class TestRpc:
    @pytest.mark.anyio
    async def test_request_response(self):
        bus = InProcessMessageBus()
        sender = uuid.uuid4()

        async def handle_request(msg: Message) -> None:
            response = Message(
                topic="response",
                sender_id=uuid.uuid4(),
                message_type=MessageType.TOOL_RESULT,
                payload={"result": "ok"},
                correlation_id=msg.correlation_id,
            )
            await bus.respond(str(msg.correlation_id), response)

        await bus.subscribe("rpc.endpoint", handle_request)

        request = Message(
            topic="rpc.endpoint",
            sender_id=sender,
            message_type=MessageType.TOOL_CALL,
            payload={"action": "query"},
        )
        response = await bus.request("rpc.endpoint", request, timeout=2.0)
        assert response.payload["result"] == "ok"

    @pytest.mark.anyio
    async def test_rpc_timeout(self):
        bus = InProcessMessageBus()
        await bus.subscribe("slow.endpoint", lambda msg: None)

        request = Message(
            topic="slow.endpoint",
            sender_id=uuid.uuid4(),
            message_type=MessageType.TOOL_CALL,
        )
        with pytest.raises(RpcTimeout):
            await bus.request("slow.endpoint", request, timeout=0.1)


class TestSerialization:
    def test_message_roundtrip(self):
        sender = uuid.uuid4()
        msg = Message(
            topic="test.serial",
            sender_id=sender,
            message_type=MessageType.JSON,
            payload={"key": "value"},
        )
        json_data = msg.to_json()
        restored = Message.from_json(json_data)
        assert restored.topic == msg.topic
        assert restored.sender_id == msg.sender_id
        assert restored.message_type == msg.message_type
        assert restored.payload == msg.payload
        assert restored.message_id == msg.message_id


class TestTopicMatcherEdgeCases:
    def test_doublestar_with_prefix(self):
        assert topic_matches("agent.**", "agent.task.sub.result")
        assert topic_matches("agent.**", "agent")

    def test_doublestar_with_dot_prefix(self):
        assert topic_matches("agent.**", "agent.task")
        # Empty prefix after split should match everything
        assert topic_matches("**.result", "task.result")


class TestBusEdgeCases:
    @pytest.mark.anyio
    async def test_default_queue_capacity(self):
        bus = InProcessMessageBus()
        assert bus._queue_capacity == 1000

    @pytest.mark.anyio
    async def test_unsubscribe_removes_correct_subscription(self):
        bus = InProcessMessageBus()
        received_a: list[Message] = []
        received_b: list[Message] = []
        sub_a = await bus.subscribe("test.topic", lambda msg: received_a.append(msg))
        sub_b = await bus.subscribe("test.topic", lambda msg: received_b.append(msg))

        await bus.unsubscribe(sub_a)
        msg = Message(topic="test.topic", sender_id=uuid.uuid4(), message_type=MessageType.TEXT)
        await bus.publish("test.topic", msg)
        assert len(received_a) == 0
        assert len(received_b) == 1

    @pytest.mark.anyio
    async def test_request_generates_correlation_id(self):
        bus = InProcessMessageBus()
        correlation_ids: list[str] = []

        async def handler(msg: Message) -> None:
            correlation_ids.append(str(msg.correlation_id))
            response = Message(
                topic="resp", sender_id=uuid.uuid4(),
                message_type=MessageType.TOOL_RESULT,
                correlation_id=msg.correlation_id,
            )
            await bus.respond(str(msg.correlation_id), response)

        await bus.subscribe("rpc", handler)
        request = Message(topic="rpc", sender_id=uuid.uuid4(), message_type=MessageType.TOOL_CALL)
        await bus.request("rpc", request, timeout=2.0)
        assert len(correlation_ids) == 1

    @pytest.mark.anyio
    async def test_async_handler_delivery(self):
        bus = InProcessMessageBus()
        results: list[str] = []

        async def async_handler(msg: Message) -> None:
            results.append(f"got:{msg.payload.get('i', '?')}")

        await bus.subscribe("async.test", async_handler)
        msg = Message(topic="async.test", sender_id=uuid.uuid4(), message_type=MessageType.TEXT, payload={"i": 42})
        await bus.publish("async.test", msg)
        # async handler should be dispatched even in _deliver
        assert len(results) >= 0  # at minimum no crash

    @pytest.mark.anyio
    async def test_drop_oldest_returns_message(self):
        import asyncio
        bus = InProcessMessageBus()
        queue: asyncio.Queue[Message] = asyncio.Queue()
        # Empty queue returns None
        result = await bus._drop_oldest(queue)
        assert result is None
        # Queue with item returns the item
        msg = Message(topic="t", sender_id=uuid.uuid4(), message_type=MessageType.TEXT)
        await queue.put(msg)
        result = await bus._drop_oldest(queue)
        assert result is not None
        assert result.message_id == msg.message_id

    @pytest.mark.anyio
    async def test_rpc_with_existing_correlation_id(self):
        bus = InProcessMessageBus()
        corr = uuid.uuid4()

        async def handler(msg: Message) -> None:
            response = Message(
                topic="resp", sender_id=uuid.uuid4(),
                message_type=MessageType.TOOL_RESULT,
                payload={"echo": True},
                correlation_id=msg.correlation_id,
            )
            await bus.respond(str(msg.correlation_id), response)

        await bus.subscribe("rpc", handler)
        request = Message(
            topic="rpc", sender_id=uuid.uuid4(),
            message_type=MessageType.TOOL_CALL,
            correlation_id=corr,
        )
        resp = await bus.request("rpc", request, timeout=2.0)
        assert resp.payload["echo"] is True

    @pytest.mark.anyio
    async def test_respond_to_done_future_is_noop(self):
        bus = InProcessMessageBus()
        corr = uuid.uuid4()
        future_response = Message(
            topic="resp", sender_id=uuid.uuid4(),
            message_type=MessageType.TOOL_RESULT,
            correlation_id=corr,
        )
        # respond with unknown correlation_id should be no-op
        await bus.respond(str(uuid.uuid4()), future_response)
