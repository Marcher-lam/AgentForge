"""Tests for agentforge.types — Task 1: Core Types & Exception Hierarchy."""

import uuid
from datetime import datetime, timezone

import pytest

from agentforge.types import (
    AgentState,
    InvalidStateTransition,
    Message,
    MessageType,
    VALID_TRANSITIONS,
    is_valid_transition,
)
from agentforge.types.errors import (
    AgentForgeError,
    AgentInitFailed,
    BusError,
    ConfigError,
    RpcTimeout,
    SubscriptionNotFound,
)


class TestAgentState:
    def test_states_exist(self):
        assert AgentState.CREATED.value == "created"
        assert AgentState.INITIALIZED.value == "initialized"
        assert AgentState.RUNNING.value == "running"
        assert AgentState.STOPPED.value == "stopped"
        assert AgentState.DESTROYED.value == "destroyed"

    def test_valid_transitions_created(self):
        assert is_valid_transition(AgentState.CREATED, AgentState.INITIALIZED)
        assert is_valid_transition(AgentState.CREATED, AgentState.DESTROYED)
        assert not is_valid_transition(AgentState.CREATED, AgentState.RUNNING)

    def test_valid_transitions_running(self):
        assert is_valid_transition(AgentState.RUNNING, AgentState.STOPPED)
        assert is_valid_transition(AgentState.RUNNING, AgentState.DESTROYED)
        assert not is_valid_transition(AgentState.RUNNING, AgentState.CREATED)

    def test_valid_transitions_stopped(self):
        assert is_valid_transition(AgentState.STOPPED, AgentState.RUNNING)
        assert is_valid_transition(AgentState.STOPPED, AgentState.DESTROYED)

    def test_destroyed_is_terminal(self):
        assert VALID_TRANSITIONS[AgentState.DESTROYED] == set()
        assert not is_valid_transition(AgentState.DESTROYED, AgentState.CREATED)

    def test_bidirectional_running_stopped(self):
        assert is_valid_transition(AgentState.RUNNING, AgentState.STOPPED)
        assert is_valid_transition(AgentState.STOPPED, AgentState.RUNNING)


class TestMessage:
    def test_create_message(self):
        sender = uuid.uuid4()
        msg = Message(topic="test.topic", sender_id=sender, message_type=MessageType.TEXT)
        assert msg.topic == "test.topic"
        assert msg.sender_id == sender
        assert msg.message_type == MessageType.TEXT
        assert msg.payload == {}
        assert msg.correlation_id is None
        assert isinstance(msg.message_id, uuid.UUID)
        assert isinstance(msg.timestamp, datetime)

    def test_frozen(self):
        sender = uuid.uuid4()
        msg = Message(topic="test", sender_id=sender, message_type=MessageType.TEXT)
        with pytest.raises(AttributeError):
            msg.topic = "changed"  # type: ignore[misc]

    def test_with_payload_and_correlation(self):
        sender = uuid.uuid4()
        corr = uuid.uuid4()
        msg = Message(
            topic="test",
            sender_id=sender,
            message_type=MessageType.JSON,
            payload={"key": "value"},
            correlation_id=corr,
        )
        assert msg.payload == {"key": "value"}
        assert msg.correlation_id == corr

    def test_to_json_roundtrip(self):
        sender = uuid.uuid4()
        corr = uuid.uuid4()
        msg = Message(
            topic="test.roundtrip",
            sender_id=sender,
            message_type=MessageType.TOOL_CALL,
            payload={"action": "query"},
            correlation_id=corr,
        )
        json_data = msg.to_json()
        assert json_data["topic"] == "test.roundtrip"
        assert json_data["message_type"] == "tool_call"

        restored = Message.from_json(json_data)
        assert restored.topic == msg.topic
        assert restored.sender_id == msg.sender_id
        assert restored.message_type == msg.message_type
        assert restored.payload == msg.payload
        assert restored.correlation_id == msg.correlation_id
        assert restored.message_id == msg.message_id
        assert restored.timestamp == msg.timestamp

    def test_to_json_without_correlation(self):
        msg = Message(
            topic="test",
            sender_id=uuid.uuid4(),
            message_type=MessageType.SYSTEM,
        )
        json_data = msg.to_json()
        assert json_data["correlation_id"] is None
        restored = Message.from_json(json_data)
        assert restored.correlation_id is None


class TestMessageType:
    def test_all_types(self):
        expected = {"TEXT", "JSON", "BINARY", "TOOL_CALL", "TOOL_RESULT", "SYSTEM", "DELIVERY_FAILED"}
        actual = {mt.name for mt in MessageType}
        assert actual == expected


class TestExceptionHierarchy:
    def test_base_exception(self):
        assert issubclass(InvalidStateTransition, AgentForgeError)
        assert issubclass(AgentInitFailed, AgentForgeError)
        assert issubclass(BusError, AgentForgeError)
        assert issubclass(ConfigError, AgentForgeError)

    def test_invalid_transition_fields(self):
        exc = InvalidStateTransition("created", "running")
        assert exc.from_state == "created"
        assert exc.to_state == "running"
        assert "created" in str(exc)
        assert "running" in str(exc)

    def test_bus_subtypes(self):
        assert issubclass(RpcTimeout, BusError)
        assert issubclass(SubscriptionNotFound, BusError)
