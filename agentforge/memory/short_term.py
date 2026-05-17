from __future__ import annotations

import uuid
from collections import OrderedDict
from typing import Any

from agentforge.types.memory import MemoryEntry, MemoryType, SearchResult


class ShortTermMemory:
    def __init__(self, capacity: int = 100) -> None:
        self._capacity = capacity
        self._sessions: dict[str, OrderedDict[uuid.UUID, MemoryEntry]] = {}

    def _get_session(self, session_id: str) -> OrderedDict[uuid.UUID, MemoryEntry]:
        if session_id not in self._sessions:
            self._sessions[session_id] = OrderedDict()
        return self._sessions[session_id]

    def _evict(self, session: OrderedDict[uuid.UUID, MemoryEntry]) -> None:
        while len(session) > self._capacity:
            session.popitem(last=False)

    async def store(
        self, session_id: str, content: str, metadata: dict[str, Any] | None = None
    ) -> uuid.UUID:
        session = self._get_session(session_id)
        entry = MemoryEntry(
            content=content,
            session_id=session_id,
            memory_type=MemoryType.SHORT_TERM,
            metadata=metadata or {},
        )
        session[entry.entry_id] = entry
        session.move_to_end(entry.entry_id)
        self._evict(session)
        return entry.entry_id

    async def retrieve(self, session_id: str, entry_id: uuid.UUID) -> MemoryEntry | None:
        session = self._sessions.get(session_id)
        if session is None or entry_id not in session:
            return None
        session.move_to_end(entry_id)
        return session[entry_id]

    async def delete(self, session_id: str, entry_id: uuid.UUID) -> None:
        session = self._sessions.get(session_id)
        if session and entry_id in session:
            del session[entry_id]

    async def clear(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    async def search(self, session_id: str, query: str, top_k: int = 5) -> list[SearchResult]:
        session = self._sessions.get(session_id, OrderedDict())
        query_lower = query.lower()
        results: list[SearchResult] = []
        for entry in reversed(session.values()):
            if query_lower in entry.content.lower():
                results.append(SearchResult(entry=entry, score=1.0, source="short_term"))
                if len(results) >= top_k:
                    break
        return results
