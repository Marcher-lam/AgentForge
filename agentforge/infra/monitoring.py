"""In-memory monitoring event store for AgentForge runtime observability."""

from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal
import uuid


MonitorEventType = Literal[
    "system",
    "message",
    "typing",
    "chunk",
    "tool_call",
    "rag",
    "memory",
    "llm",
    "rl",
    "evolution",
    "coevolution",
    "persistence",
    "error",
]

Severity = Literal["info", "warning", "error"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class MonitorEvent:
    id: str
    timestamp: str
    type: str
    severity: str
    payload: dict[str, Any] = field(default_factory=dict)
    session_id: str | None = None
    agent_id: str | None = None
    run_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "type": self.type,
            "severity": self.severity,
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "run_id": self.run_id,
            "payload": self.payload,
        }


class MonitorStore:
    def __init__(self, max_events: int = 5000) -> None:
        self._events: deque[MonitorEvent] = deque(maxlen=max_events)

    def record(
        self,
        event_type: MonitorEventType | str,
        payload: dict[str, Any] | None = None,
        *,
        severity: Severity | str = "info",
        session_id: str | None = None,
        agent_id: str | None = None,
        run_id: str | None = None,
    ) -> dict[str, Any]:
        event = MonitorEvent(
            id=str(uuid.uuid4()),
            timestamp=_now(),
            type=str(event_type),
            severity=str(severity),
            session_id=session_id,
            agent_id=agent_id,
            run_id=run_id,
            payload=payload or {},
        )
        self._events.append(event)
        return event.to_dict()

    def list_events(
        self,
        *,
        event_type: str | None = None,
        severity: str | None = None,
        session_id: str | None = None,
        agent_id: str | None = None,
        run_id: str | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        result: list[MonitorEvent] = []
        for event in reversed(self._events):
            if event_type and event.type != event_type:
                continue
            if severity and event.severity != severity:
                continue
            if session_id and event.session_id != session_id:
                continue
            if agent_id and event.agent_id != agent_id:
                continue
            if run_id and event.run_id != run_id:
                continue
            result.append(event)
            if len(result) >= limit:
                break
        return [event.to_dict() for event in result]

    def stats(self) -> dict[str, Any]:
        events = list(self._events)
        by_type = Counter(event.type for event in events)
        by_severity = Counter(event.severity for event in events)
        by_agent = Counter(event.agent_id for event in events if event.agent_id)
        by_session = Counter(event.session_id for event in events if event.session_id)
        errors = [event.to_dict() for event in events if event.severity == "error"][-10:]

        return {
            "total_events": len(events),
            "by_type": dict(by_type),
            "by_severity": dict(by_severity),
            "top_agents": by_agent.most_common(10),
            "top_sessions": by_session.most_common(10),
            "recent_errors": errors,
        }

    def clear(self) -> None:
        self._events.clear()
