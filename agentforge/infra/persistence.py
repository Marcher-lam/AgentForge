"""SQLite write-through persistence for sessions, messages, and agent configs."""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any


_DB_DIR = Path(os.environ.get("AGENTFORGE_DATA_DIR", os.path.join(os.getcwd(), "data")))


def _get_db_path() -> str:
    _DB_DIR.mkdir(parents=True, exist_ok=True)
    return str(_DB_DIR / "agentforge.db")


_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    type TEXT NOT NULL DEFAULT 'ONE_VS_ONE',
    name TEXT NOT NULL,
    agent_ids TEXT NOT NULL DEFAULT '[]',
    last_message TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
    message_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    sender_type TEXT NOT NULL,
    sender_id TEXT,
    sender_name TEXT,
    content TEXT NOT NULL DEFAULT '',
    content_type TEXT NOT NULL DEFAULT 'TEXT',
    created_at TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, created_at);

CREATE TABLE IF NOT EXISTS agent_configs (
    agent_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    system_prompt TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'ONLINE',
    config TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""


class PersistenceManager:
    """Synchronous SQLite write-through layer.

    - All writes go to SQLite immediately (write-through).
    - Startup loads everything into memory.
    - Reads hit in-memory structures; no SQLite queries on read path.
    """

    def __init__(self, db_path: str | None = None) -> None:
        self._db_path = db_path or _get_db_path()
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    # ── Sessions ──────────────────────────────────────────────

    def save_session(self, session: dict) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO sessions (session_id, type, name, agent_ids, last_message, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                session["session_id"],
                session.get("type", "ONE_VS_ONE"),
                session.get("name", ""),
                json.dumps(session.get("agent_ids", [])),
                json.dumps(session.get("last_message")) if session.get("last_message") else None,
                session.get("created_at", ""),
                session.get("updated_at", ""),
            ),
        )
        self._conn.commit()

    def delete_session(self, session_id: str) -> None:
        self._conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        self._conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        self._conn.commit()

    def update_session_agents(self, session_id: str, agent_ids: list[str], updated_at: str) -> None:
        self._conn.execute(
            "UPDATE sessions SET agent_ids = ?, updated_at = ? WHERE session_id = ?",
            (json.dumps(agent_ids), updated_at, session_id),
        )
        self._conn.commit()

    def update_session_last_message(self, session_id: str, last_message: dict | None, updated_at: str) -> None:
        self._conn.execute(
            "UPDATE sessions SET last_message = ?, updated_at = ? WHERE session_id = ?",
            (json.dumps(last_message) if last_message else None, updated_at, session_id),
        )
        self._conn.commit()

    def load_sessions(self) -> list[dict]:
        rows = self._conn.execute(
            "SELECT session_id, type, name, agent_ids, last_message, created_at, updated_at FROM sessions ORDER BY created_at"
        ).fetchall()
        result = []
        for row in rows:
            result.append({
                "session_id": row[0],
                "type": row[1],
                "name": row[2],
                "agent_ids": json.loads(row[3]),
                "last_message": json.loads(row[4]) if row[4] else None,
                "created_at": row[5],
                "updated_at": row[6],
            })
        return result

    # ── Messages ──────────────────────────────────────────────

    def save_message(self, msg: dict) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO messages (message_id, session_id, sender_type, sender_id, sender_name, content, content_type, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                msg["message_id"],
                msg["session_id"],
                msg.get("sender_type", "USER"),
                msg.get("sender_id"),
                msg.get("sender_name", ""),
                msg.get("content", ""),
                msg.get("content_type", "TEXT"),
                msg.get("created_at", ""),
            ),
        )
        self._conn.commit()

    def delete_message(self, message_id: str) -> None:
        self._conn.execute("DELETE FROM messages WHERE message_id = ?", (message_id,))
        self._conn.commit()

    def load_messages(self, session_id: str) -> list[dict]:
        rows = self._conn.execute(
            "SELECT message_id, session_id, sender_type, sender_id, sender_name, content, content_type, created_at "
            "FROM messages WHERE session_id = ? ORDER BY created_at",
            (session_id,),
        ).fetchall()
        return [
            {
                "message_id": r[0],
                "session_id": r[1],
                "sender_type": r[2],
                "sender_id": r[3],
                "sender_name": r[4],
                "content": r[5],
                "content_type": r[6],
                "created_at": r[7],
            }
            for r in rows
        ]

    def load_all_messages(self) -> dict[str, list[dict]]:
        rows = self._conn.execute(
            "SELECT message_id, session_id, sender_type, sender_id, sender_name, content, content_type, created_at "
            "FROM messages ORDER BY created_at"
        ).fetchall()
        buckets: dict[str, list[dict]] = {}
        for r in rows:
            sid = r[1]
            buckets.setdefault(sid, []).append({
                "message_id": r[0],
                "session_id": r[1],
                "sender_type": r[2],
                "sender_id": r[3],
                "sender_name": r[4],
                "content": r[5],
                "content_type": r[6],
                "created_at": r[7],
            })
        return buckets

    def search_messages(self, query: str, session_id: str | None = None, limit: int = 50) -> list[dict]:
        sql = "SELECT message_id, session_id, sender_type, sender_id, sender_name, content, content_type, created_at " \
              "FROM messages WHERE content LIKE ?"
        params: list[Any] = [f"%{query}%"]
        if session_id:
            sql += " AND session_id = ?"
            params.append(session_id)
        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        rows = self._conn.execute(sql, params).fetchall()
        return [
            {
                "message_id": r[0],
                "session_id": r[1],
                "sender_type": r[2],
                "sender_id": r[3],
                "sender_name": r[4],
                "content": r[5],
                "content_type": r[6],
                "created_at": r[7],
            }
            for r in rows
        ]

    # ── Agent Configs ─────────────────────────────────────────

    def save_agent_config(self, agent_id: str, name: str, system_prompt: str, config: dict, created_at: str, updated_at: str, status: str = "ONLINE") -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO agent_configs (agent_id, name, system_prompt, status, config, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (agent_id, name, system_prompt, status, json.dumps(config), created_at, updated_at),
        )
        self._conn.commit()

    def delete_agent_config(self, agent_id: str) -> None:
        self._conn.execute("DELETE FROM agent_configs WHERE agent_id = ?", (agent_id,))
        self._conn.commit()

    def update_agent_config(self, agent_id: str, **fields: Any) -> None:
        sets: list[str] = []
        vals: list[Any] = []
        for k, v in fields.items():
            if k == "config":
                sets.append("config = ?")
                vals.append(json.dumps(v))
            else:
                sets.append(f"{k} = ?")
                vals.append(v)
        if not sets:
            return
        vals.append(agent_id)
        self._conn.execute(f"UPDATE agent_configs SET {', '.join(sets)} WHERE agent_id = ?", vals)
        self._conn.commit()

    def load_agent_configs(self) -> list[dict]:
        rows = self._conn.execute(
            "SELECT agent_id, name, system_prompt, status, config, created_at, updated_at FROM agent_configs"
        ).fetchall()
        return [
            {
                "agent_id": r[0],
                "name": r[1],
                "system_prompt": r[2],
                "status": r[3],
                "config": json.loads(r[4]),
                "created_at": r[5],
                "updated_at": r[6],
            }
            for r in rows
        ]

    # ── Lifecycle ─────────────────────────────────────────────

    def close(self) -> None:
        self._conn.close()
