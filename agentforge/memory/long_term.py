"""SQLite-backed persistent long-term memory."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import aiosqlite
import structlog

logger = structlog.get_logger("agentforge.memory.long_term")

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS long_term_memory (
    id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    metadata TEXT,
    created_at TEXT NOT NULL,
    ttl_seconds INTEGER,
    expires_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_ltm_agent_key ON long_term_memory(agent_id, key);
CREATE INDEX IF NOT EXISTS idx_ltm_expires ON long_term_memory(expires_at);
"""


@dataclass(frozen=True, slots=True)
class LongTermMemoryEntry:
    """A single entry in long-term memory."""

    id: str
    agent_id: str
    key: str
    value: str
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ttl_seconds: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "key": self.key,
            "value": self.value,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "ttl_seconds": self.ttl_seconds,
        }


class LongTermMemory:
    """SQLite-backed persistent memory with TTL support."""

    def __init__(self, db_path: str | Path = "memory.db") -> None:
        self._db_path = str(db_path)
        self._db: aiosqlite.Connection | None = None

    async def _ensure_db(self) -> aiosqlite.Connection:
        if self._db is None:
            self._db = await aiosqlite.connect(self._db_path)
            self._db.row_factory = aiosqlite.Row
            await self._db.executescript(_CREATE_TABLE_SQL)
            await self._db.commit()
        return self._db

    async def store(
        self,
        agent_id: str,
        key: str,
        value: str,
        metadata: dict[str, Any] | None = None,
        ttl: int | None = None,
    ) -> str:
        """Store a value and return the entry id."""
        db = await self._ensure_db()
        entry_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        metadata_json = json.dumps(metadata or {})
        expires_at = None
        if ttl is not None:
            from datetime import timedelta

            expires_at = (now + timedelta(seconds=ttl)).isoformat()

        await db.execute(
            "INSERT INTO long_term_memory (id, agent_id, key, value, metadata, created_at, ttl_seconds, expires_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (entry_id, agent_id, key, value, metadata_json, now.isoformat(), ttl, expires_at),
        )
        await db.commit()
        logger.debug("long_term_store", agent_id=agent_id, key=key, entry_id=entry_id)
        return entry_id

    async def retrieve(self, agent_id: str, key: str) -> list[LongTermMemoryEntry]:
        """Retrieve all entries matching agent_id and key."""
        db = await self._ensure_db()
        cursor = await db.execute(
            "SELECT * FROM long_term_memory WHERE agent_id = ? AND key = ? ORDER BY created_at DESC",
            (agent_id, key),
        )
        rows = await cursor.fetchall()
        return [self._row_to_entry(row) for row in rows]

    async def search(
        self, agent_id: str, query: str, limit: int = 10
    ) -> list[LongTermMemoryEntry]:
        """Full-text search via LIKE on value column."""
        db = await self._ensure_db()
        pattern = f"%{query}%"
        cursor = await db.execute(
            "SELECT * FROM long_term_memory WHERE agent_id = ? AND value LIKE ? "
            "ORDER BY created_at DESC LIMIT ?",
            (agent_id, pattern, limit),
        )
        rows = await cursor.fetchall()
        return [self._row_to_entry(row) for row in rows]

    async def delete(self, agent_id: str, key: str) -> bool:
        """Delete entries by agent_id and key. Returns True if anything was deleted."""
        db = await self._ensure_db()
        cursor = await db.execute(
            "DELETE FROM long_term_memory WHERE agent_id = ? AND key = ?",
            (agent_id, key),
        )
        await db.commit()
        deleted = cursor.rowcount > 0
        if deleted:
            logger.debug("long_term_delete", agent_id=agent_id, key=key)
        return deleted

    async def delete_expired(self) -> int:
        """Remove all TTL-expired entries. Returns count of deleted rows."""
        db = await self._ensure_db()
        now = datetime.now(timezone.utc).isoformat()
        cursor = await db.execute(
            "DELETE FROM long_term_memory WHERE expires_at IS NOT NULL AND expires_at < ?",
            (now,),
        )
        await db.commit()
        count = cursor.rowcount
        if count > 0:
            logger.debug("long_term_delete_expired", count=count)
        return count

    async def close(self) -> None:
        """Close the database connection."""
        if self._db is not None:
            await self._db.close()
            self._db = None

    @staticmethod
    def _row_to_entry(row: aiosqlite.Row) -> LongTermMemoryEntry:
        return LongTermMemoryEntry(
            id=row["id"],
            agent_id=row["agent_id"],
            key=row["key"],
            value=row["value"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            created_at=datetime.fromisoformat(row["created_at"]),
            ttl_seconds=row["ttl_seconds"],
        )
