"""ChatMemory — Per-session compact timeline memory with strict context budget."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ChatEvent:
    """A single chat event in compact form."""

    ts: str  # HH:MM
    sender: str  # "用户" | agent name
    action: str  # "问" | "答" | "@提及" | "PASS" | "共识"
    target: str | None = None  # @mention target
    summary: str = ""  # ≤60 chars

    def format(self, me: str = "") -> str:
        """Format as a compact line. Mark events about 'me' with (我)."""
        sender_tag = f"{self.sender}(我)" if self.sender == me else self.sender
        if self.action == "@提及" and self.target:
            return f"[{self.ts}] {sender_tag}→@{self.target}: {self.summary}"
        if self.action == "共识":
            return f"[{self.ts}] [共识] {self.summary}"
        if self.action == "PASS":
            return f"[{self.ts}] {sender_tag}: PASS"
        return f"[{self.ts}] {sender_tag}: {self.summary}"


class ChatMemory:
    """Per-session timeline memory with strict context budget.

    Stores compact event summaries (≤60 chars each), not raw text.
    Session-isolated: group chat A's memory never leaks into group chat B.
    """

    def __init__(self, max_events_per_session: int = 100) -> None:
        self._sessions: dict[str, list[ChatEvent]] = {}
        self._max_events = max_events_per_session

    def record(
        self,
        session_id: str,
        sender: str,
        action: str,
        summary: str,
        target: str | None = None,
    ) -> None:
        """Record a chat event. Summary is auto-truncated to 60 chars."""
        events = self._sessions.setdefault(session_id, [])
        now = datetime.now().strftime("%H:%M")
        events.append(
            ChatEvent(
                ts=now,
                sender=sender,
                action=action,
                target=target,
                summary=summary[:60],
            )
        )
        # Evict oldest if over capacity
        if len(events) > self._max_events:
            self._sessions[session_id] = events[-self._max_events :]

    def get_context(
        self, session_id: str, agent_name: str, budget: int = 800
    ) -> str:
        """Build compact timeline context within budget chars.

        Returns a formatted string showing recent events, newest first,
        fitting within `budget` characters. Events involving `agent_name`
        are tagged with (我).
        """
        events = self._sessions.get(session_id, [])
        if not events:
            return ""

        lines: list[str] = []
        total = 0
        header = "--- 讨论时序 ---\n"
        total += len(header)

        for event in reversed(events):
            line = event.format(me=agent_name) + "\n"
            if total + len(line) > budget:
                break
            lines.insert(0, line)
            total += len(line)

        if not lines:
            return ""

        return "\n" + header + "".join(lines)

    def get_mentions_of(self, session_id: str, agent_name: str) -> list[ChatEvent]:
        """Get all events where agent_name was @mentioned."""
        events = self._sessions.get(session_id, [])
        return [
            e for e in events if e.action == "@提及" and e.target == agent_name
        ]

    def get_last_user_question(self, session_id: str) -> str:
        """Extract the last user question from this session's timeline."""
        events = self._sessions.get(session_id, [])
        for event in reversed(events):
            if event.sender == "用户" and event.action == "问":
                return event.summary
        return ""

    def clear_session(self, session_id: str) -> None:
        """Remove all events for a session."""
        self._sessions.pop(session_id, None)
