"""ChatMemory — Dual-track session memory: shared group log + per-agent summary.

Design:
  Shared track: full conversation log per session (all agents see the same)
  Agent track: per-agent compact summary (only events relevant to that agent)

When building context for an agent, we blend:
  1. Shared full log (recent messages, capped at budget)
  2. Agent-specific highlights (@mentions of me, my replies, my stance)
  3. Topic markers and consensus points

Total context injected into prompt is strictly budget-controlled.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ChatEvent:
    """A single chat event."""

    ts: str  # HH:MM
    sender: str
    action: str  # "问" | "答" | "@提及" | "PASS" | "共识" | "话题切换"
    target: str | None = None
    summary: str = ""  # ≤80 chars
    raw_content: str = ""  # original text, ≤300 chars (shared log only)

    def format_timeline(self, me: str = "") -> str:
        """Compact timeline format for agent context."""
        sender_tag = f"{self.sender}(我)" if self.sender == me else self.sender
        if self.action == "@提及" and self.target:
            target_tag = f"{self.target}(我)" if self.target == me else self.target
            return f"[{self.ts}] {sender_tag}→@{target_tag}: {self.summary}"
        if self.action == "共识":
            return f"[{self.ts}] [共识] {self.summary}"
        if self.action == "话题切换":
            return f"[{self.ts}] ── 新话题: {self.summary} ──"
        if self.action == "PASS":
            return ""
        return f"[{self.ts}] {sender_tag}: {self.summary}"


@dataclass
class SessionMemory:
    """All memory for a single session (group chat or 1v1)."""

    session_id: str
    # Shared: full conversation log (all messages)
    shared_log: list[ChatEvent] = field(default_factory=list)
    # Per-agent: only events involving that agent (asked, replied, @mentioned)
    agent_log: dict[str, list[ChatEvent]] = field(default_factory=dict)
    # Topic boundaries
    topics: list[dict] = field(default_factory=list)  # [{start_idx, end_idx, topic}]

    def max_shared_events(self) -> int:
        return len(self.shared_log)


class ChatMemory:
    """Dual-track session memory with strict context budget.

    Shared track: complete conversation log, shared by all agents in session.
    Agent track: per-agent filtered view (only their interactions).

    When building context:
      - Shared log provides the full picture (who said what, in order)
      - Agent log provides personal highlights (@mentions of me, my replies)
      - Both are blended within a strict character budget
    """

    def __init__(self, max_shared_per_session: int = 200) -> None:
        self._sessions: dict[str, SessionMemory] = {}
        self._max_shared = max_shared_per_session

    def _get_or_create(self, session_id: str) -> SessionMemory:
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionMemory(session_id=session_id)
        return self._sessions[session_id]

    def record(
        self,
        session_id: str,
        sender: str,
        action: str,
        summary: str,
        raw_content: str = "",
        target: str | None = None,
        agent_ids: list[str] | None = None,
    ) -> None:
        """Record a chat event.

        Args:
            agent_ids: list of agent IDs in this session (for per-agent filtering)
        """
        session = self._get_or_create(session_id)
        now = datetime.now().strftime("%H:%M")
        event = ChatEvent(
            ts=now,
            sender=sender,
            action=action,
            target=target,
            summary=summary[:80],
            raw_content=raw_content[:300],
        )

        # Shared log: all events
        session.shared_log.append(event)
        if len(session.shared_log) > self._max_shared:
            session.shared_log = session.shared_log[-self._max_shared:]

        # Per-agent log: filter events relevant to each agent
        if agent_ids:
            for aid in agent_ids:
                agent_events = session.agent_log.setdefault(aid, [])
                # Each agent sees: their own replies, @mentions of them, user questions, consensus
                is_relevant = (
                    sender == "用户"
                    or action == "共识"
                    or action == "话题切换"
                    or target == aid  # someone @mentioned this agent
                    # Note: we add sender's own events separately below
                )
                if is_relevant:
                    agent_events.append(event)
                    if len(agent_events) > 100:
                        session.agent_log[aid] = agent_events[-100:]

    def record_agent_reply(
        self,
        session_id: str,
        agent_id: str,
        agent_name: str,
        reply: str,
        agent_ids: list[str] | None = None,
    ) -> None:
        """Record an agent's reply to both shared and per-agent logs."""
        session = self._get_or_create(session_id)
        now = datetime.now().strftime("%H:%M")

        # Detect @mentions in reply
        mentioned = None
        for line in reply.split("\n"):
            stripped = line.strip()
            if stripped.startswith("@"):
                mentioned = stripped.split()[0][1:] if stripped.split() else None
                break

        action = "@提及" if mentioned else "答"
        event = ChatEvent(
            ts=now,
            sender=agent_name,
            action=action,
            target=mentioned,
            summary=reply[:80],
            raw_content=reply[:300],
        )

        # Shared log
        session.shared_log.append(event)
        if len(session.shared_log) > self._max_shared:
            session.shared_log = session.shared_log[-self._max_shared:]

        # Per-agent log: add to THIS agent's log (their own reply)
        agent_events = session.agent_log.setdefault(agent_id, [])
        agent_events.append(event)
        if len(agent_events) > 100:
            session.agent_log[agent_id] = agent_events[-100:]

        # Per-agent log: if this agent @mentioned someone, add to TARGET's log too
        if mentioned and agent_ids:
            # Find the target agent's ID by name
            from agentforge.server.app import _parse_agent_config
            # We'll match by name in shared_log agents
            # For now, add to all agent logs (target filtering happens at context build)
            pass

    def get_context(
        self, session_id: str, agent_name: str, agent_id: str, budget: int = 800
    ) -> str:
        """Build compact context for an agent, blending shared + personal views.

        Strategy:
          1. Recent shared log (full picture, newest first, within budget)
          2. Personal highlights are already tagged with (我) in the shared view

        This gives each agent:
          - The full conversation context (who said what, in order)
          - Visual distinction of their own contributions (我 tag)
          - All within a strict character budget
        """
        session = self._sessions.get(session_id)
        if not session or not session.shared_log:
            return ""

        lines: list[str] = []
        total = 0
        header = "--- 讨论记录 ---\n"
        total += len(header)

        # Build from newest to oldest, stop at budget
        for event in reversed(session.shared_log):
            line = event.format_timeline(me=agent_name)
            if not line:  # PASS events produce empty lines
                continue
            line += "\n"
            if total + len(line) > budget:
                break
            lines.insert(0, line)
            total += len(line)

        if not lines:
            return ""

        return "\n" + header + "".join(lines)

    def get_mentions_of(self, session_id: str, agent_name: str) -> list[ChatEvent]:
        """Get all events where agent_name was @mentioned."""
        session = self._sessions.get(session_id)
        if not session:
            return []
        return [
            e for e in session.shared_log
            if e.action == "@提及" and e.target == agent_name
        ]

    def get_shared_raw(self, session_id: str, limit: int = 10, max_chars: int = 3000) -> str:
        """Get raw conversation text for transcript building."""
        session = self._sessions.get(session_id)
        if not session:
            return ""

        lines: list[str] = []
        total = 0
        for event in reversed(session.shared_log[-limit:]):
            raw = event.raw_content or event.summary
            line = f"【{event.sender}】: {raw}\n"
            if total + len(line) > max_chars:
                break
            lines.insert(0, line)
            total += len(line)

        return "".join(lines)

    def clear_session(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)
