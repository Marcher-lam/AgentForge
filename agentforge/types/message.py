"""Message dataclass and MessageType enum."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class MessageType(Enum):
    """Enumeration of supported message types."""
    TEXT = "text"
    JSON = "json"
    BINARY = "binary"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    SYSTEM = "system"
    DELIVERY_FAILED = "delivery_failed"


@dataclass(frozen=True, slots=True)
class Message:
    """Immutable message with topic routing, correlation ID, and JSON serialization."""
    topic: str
    sender_id: uuid.UUID
    message_type: MessageType
    payload: dict[str, Any] = field(default_factory=dict)
    message_id: uuid.UUID = field(default_factory=uuid.uuid4)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    correlation_id: uuid.UUID | None = None

    def to_json(self) -> dict[str, Any]:
        """Serialize the message to a JSON-compatible dictionary."""
        return {
            "message_id": str(self.message_id),
            "topic": self.topic,
            "message_type": self.message_type.value,
            "sender_id": str(self.sender_id),
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": str(self.correlation_id) if self.correlation_id else None,
        }

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> Message:
        """Deserialize a message from a JSON-compatible dictionary."""
        return cls(
            message_id=uuid.UUID(data["message_id"]),
            topic=data["topic"],
            message_type=MessageType(data["message_type"]),
            sender_id=uuid.UUID(data["sender_id"]),
            payload=data.get("payload", {}),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            correlation_id=uuid.UUID(data["correlation_id"]) if data.get("correlation_id") else None,
        )
