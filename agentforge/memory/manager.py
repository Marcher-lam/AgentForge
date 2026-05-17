"""MemoryManager — unified facade over short-term, long-term, and vector memory."""

from __future__ import annotations

from typing import Any

import structlog

from agentforge.memory.long_term import LongTermMemory, LongTermMemoryEntry
from agentforge.memory.short_term import ShortTermMemory
from agentforge.memory.vector_memory import VectorEntry, VectorMemory
from agentforge.types.memory import MemoryEntry, MemoryType, SearchResult

logger = structlog.get_logger("agentforge.memory.manager")


class MemoryManager:
    """Facade combining ShortTermMemory, LongTermMemory, and VectorMemory."""

    def __init__(
        self,
        short_term: ShortTermMemory | None = None,
        long_term: LongTermMemory | None = None,
        vector: VectorMemory | None = None,
    ) -> None:
        self.short_term = short_term or ShortTermMemory()
        self.long_term = long_term or LongTermMemory()
        self.vector = vector or VectorMemory()

    async def store(
        self,
        level: str,
        agent_id: str,
        key: str,
        value: str,
        **kwargs: Any,
    ) -> str:
        """Route store to the appropriate memory level. Returns entry id."""
        if level == "short_term":
            entry_id = await self.short_term.store(
                session_id=agent_id,
                content=value,
                metadata=kwargs.get("metadata"),
            )
            return str(entry_id)

        if level == "long_term":
            return await self.long_term.store(
                agent_id=agent_id,
                key=key,
                value=value,
                metadata=kwargs.get("metadata"),
                ttl=kwargs.get("ttl"),
            )

        if level == "vector":
            return self.vector.add(
                agent_id=agent_id,
                text=value,
                embedding=kwargs.get("embedding"),
                metadata=kwargs.get("metadata"),
            )

        raise ValueError(f"Unknown memory level: {level}")

    async def search(
        self,
        agent_id: str,
        query: str,
        levels: list[str] | None = None,
        top_k: int = 10,
    ) -> list[SearchResult]:
        """Search across all specified memory levels."""
        target_levels = levels or ["short_term", "long_term", "vector"]
        results: list[SearchResult] = []

        if "short_term" in target_levels:
            st_results = await self.short_term.search(
                session_id=agent_id, query=query, top_k=top_k
            )
            results.extend(st_results)

        if "long_term" in target_levels:
            lt_entries = await self.long_term.search(
                agent_id=agent_id, query=query, limit=top_k
            )
            for entry in lt_entries:
                mem_entry = MemoryEntry(
                    content=entry.value,
                    session_id=entry.agent_id,
                    memory_type=MemoryType.LONG_TERM,
                    entry_id=entry.id,
                    timestamp=entry.created_at,
                    metadata=entry.metadata,
                    ttl_seconds=entry.ttl_seconds,
                )
                results.append(
                    SearchResult(entry=mem_entry, score=1.0, source="long_term")
                )

        if "vector" in target_levels:
            from agentforge.memory.vector_memory import semantic_embedding

            query_emb = semantic_embedding(query)
            v_results = self.vector.search(
                agent_id=agent_id, query_embedding=query_emb, top_k=top_k
            )
            for score, ventry in v_results:
                mem_entry = MemoryEntry(
                    content=ventry.text,
                    session_id=ventry.agent_id,
                    memory_type=MemoryType.VECTOR,
                    entry_id=ventry.id,
                    timestamp=ventry.created_at,
                    metadata=ventry.metadata,
                )
                results.append(
                    SearchResult(entry=mem_entry, score=score, source="vector")
                )

        # Sort all results by score (descending), deduplicate by content
        results.sort(key=lambda r: r.score, reverse=True)
        seen_content: set[str] = set()
        deduped: list[SearchResult] = []
        for r in results:
            content_key = r.entry.content[:80]
            if content_key not in seen_content:
                seen_content.add(content_key)
                deduped.append(r)

        return deduped[:top_k]

    async def promote(
        self, agent_id: str, key: str, from_level: str, to_level: str
    ) -> bool:
        """Move a memory entry from one level to another."""
        # Retrieve from source
        if from_level == "short_term":
            import uuid

            entry = await self.short_term.retrieve(
                session_id=agent_id, entry_id=uuid.UUID(key)
            )
            if entry is None:
                return False
            value = entry.content
            metadata = entry.metadata

        elif from_level == "long_term":
            entries = await self.long_term.retrieve(agent_id=agent_id, key=key)
            if not entries:
                return False
            value = entries[0].value
            metadata = entries[0].metadata

        elif from_level == "vector":
            if key not in self.vector._entries:
                return False
            ventry = self.vector._entries[key]
            if ventry.agent_id != agent_id:
                return False
            value = ventry.text
            metadata = ventry.metadata
        else:
            raise ValueError(f"Unknown source level: {from_level}")

        # Store to target
        await self.store(to_level, agent_id, key, value, metadata=metadata)
        logger.debug(
            "memory_promote",
            agent_id=agent_id,
            key=key,
            from_level=from_level,
            to_level=to_level,
        )
        return True

    async def cleanup_expired(self) -> int:
        """Remove expired long-term entries. Returns count of deleted rows."""
        return await self.long_term.delete_expired()

    async def close(self) -> None:
        """Close underlying resources (e.g. SQLite connection)."""
        await self.long_term.close()
