"""NumPy-based vector memory with cosine similarity search and real semantic embeddings."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger("agentforge.memory.vector")

_np = None
_embed_model = None


def _get_numpy():
    global _np
    if _np is None:
        import numpy
        _np = numpy
    return _np


def _get_embed_model():
    """Lazy-load fastembed model for real semantic embeddings."""
    global _embed_model
    if _embed_model is None:
        from fastembed import TextEmbedding
        _embed_model = TextEmbedding("BAAI/bge-small-en-v1.5")
    return _embed_model


def semantic_embedding(text: str) -> list[float]:
    """Generate real semantic embedding using fastembed (BAAI/bge-small-en-v1.5, 384-dim)."""
    model = _get_embed_model()
    return [e.tolist() for e in model.embed([text])][0]


@dataclass(frozen=True, slots=True)
class VectorEntry:
    """A single vector memory entry."""

    id: str
    agent_id: str
    text: str
    embedding: list[float]
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "text": self.text,
            "embedding": self.embedding,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VectorEntry:
        return cls(
            id=data["id"],
            agent_id=data["agent_id"],
            text=data["text"],
            embedding=data["embedding"],
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
        )


class VectorMemory:
    """In-memory vector store with optional JSON persistence."""

    def __init__(self, persist_path: str | Path | None = None) -> None:
        self._entries: dict[str, VectorEntry] = {}
        self._persist_path = Path(persist_path) if persist_path else None
        if self._persist_path and self._persist_path.exists():
            self._load_from_disk()

    def add(
        self,
        agent_id: str,
        text: str,
        embedding: list[float] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Add a vector entry. Uses real semantic embedding if none provided."""
        entry_id = str(uuid.uuid4())
        emb = embedding if embedding is not None else semantic_embedding(text)
        entry = VectorEntry(
            id=entry_id,
            agent_id=agent_id,
            text=text,
            embedding=emb,
            metadata=metadata or {},
        )
        self._entries[entry_id] = entry
        self._maybe_persist()
        logger.debug("vector_add", agent_id=agent_id, entry_id=entry_id)
        return entry_id

    def search(
        self, agent_id: str, query_embedding: list[float], top_k: int = 5
    ) -> list[VectorEntry]:
        """Search by cosine similarity against query_embedding."""
        np = _get_numpy()
        q = np.array(query_embedding, dtype=np.float32)
        q_norm = np.linalg.norm(q)
        if q_norm == 0:
            return []
        q = q / q_norm

        scored: list[tuple[float, VectorEntry]] = []
        for entry in self._entries.values():
            if entry.agent_id != agent_id:
                continue
            v = np.array(entry.embedding, dtype=np.float32)
            v_norm = np.linalg.norm(v)
            if v_norm == 0:
                continue
            similarity = float(np.dot(q, v / v_norm))
            scored.append((similarity, entry))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [entry for _, entry in scored[:top_k]]

    def delete(self, agent_id: str, entry_id: str) -> bool:
        """Delete a specific entry. Returns True if found and deleted."""
        entry = self._entries.get(entry_id)
        if entry is None or entry.agent_id != agent_id:
            return False
        del self._entries[entry_id]
        self._maybe_persist()
        return True

    def _maybe_persist(self) -> None:
        if self._persist_path is None:
            return
        self._save_to_disk()

    def _save_to_disk(self) -> None:
        if self._persist_path is None:
            return
        data = [e.to_dict() for e in self._entries.values()]
        self._persist_path.parent.mkdir(parents=True, exist_ok=True)
        self._persist_path.write_text(json.dumps(data, indent=2))

    def _load_from_disk(self) -> None:
        if self._persist_path is None or not self._persist_path.exists():
            return
        data = json.loads(self._persist_path.read_text())
        for item in data:
            entry = VectorEntry.from_dict(item)
            self._entries[entry.id] = entry
