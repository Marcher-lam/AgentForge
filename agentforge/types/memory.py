from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class MemoryType(Enum):
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    VECTOR = "vector"


@dataclass(frozen=True, slots=True)
class MemoryEntry:
    content: str
    session_id: str
    memory_type: MemoryType
    entry_id: uuid.UUID = field(default_factory=uuid.uuid4)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)
    ttl_seconds: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "content": self.content,
            "session_id": self.session_id,
            "memory_type": self.memory_type.value,
            "entry_id": str(self.entry_id),
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "ttl_seconds": self.ttl_seconds,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MemoryEntry:
        return cls(
            content=data["content"],
            session_id=data["session_id"],
            memory_type=MemoryType(data["memory_type"]),
            entry_id=uuid.UUID(data["entry_id"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {}),
            ttl_seconds=data.get("ttl_seconds"),
        )


@dataclass(frozen=True, slots=True)
class SearchResult:
    entry: MemoryEntry
    score: float
    source: str
