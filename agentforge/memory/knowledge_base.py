"""ChromaDB-based per-agent knowledge base with fastembed semantic embeddings."""
from __future__ import annotations

import numpy as np
import chromadb
from fastembed import TextEmbedding


class ChromaKnowledgeBase:
    """Per-agent knowledge base using ChromaDB + fastembed (ONNX, no PyTorch)."""

    def __init__(self, persist_dir: str = "chroma_data") -> None:
        self._client = chromadb.PersistentClient(path=persist_dir)
        self._model = TextEmbedding("BAAI/bge-small-en-v1.5")

    def _embed(self, texts: list[str]) -> list[list[float]]:
        return [e.tolist() for e in self._model.embed(texts)]

    def _collection(self, agent_id: str):
        name = f"agent_{agent_id.replace('-', '_')}"
        return self._client.get_or_create_collection(name=name)

    def add(self, agent_id: str, texts: list[str], metas: list[dict] | None = None, ids: list[str] | None = None) -> int:
        if not texts:
            return 0
        col = self._collection(agent_id)
        if ids is None:
            ids = [f"doc_{i}_{hash(t) % 10**8}" for i, t in enumerate(texts)]
        if metas is None:
            metas = [{"source": "upload"} for _ in texts]
        embeddings = self._embed(texts)
        col.upsert(documents=texts, ids=ids, metadatas=metas, embeddings=embeddings)
        return len(texts)

    def search(self, agent_id: str, query: str, top_k: int = 5) -> list[dict]:
        try:
            col = self._collection(agent_id)
            query_emb = self._embed([query])
            result = col.query(query_embeddings=query_emb, n_results=min(top_k, col.count() or 1))
            docs = result.get("documents", [[]])[0]
            dists = result.get("distances", [[]])[0]
            metas = result.get("metadatas", [[]])[0]
            items = []
            for i, doc in enumerate(docs):
                items.append({
                    "content": doc,
                    "score": round(1 - dists[i], 3) if i < len(dists) else 0,
                    "metadata": metas[i] if i < len(metas) else {},
                })
            return items
        except Exception:
            return []

    def count(self, agent_id: str) -> int:
        try:
            return self._collection(agent_id).count()
        except Exception:
            return 0

    def delete_collection(self, agent_id: str) -> None:
        name = f"agent_{agent_id.replace('-', '_')}"
        try:
            self._client.delete_collection(name=name)
        except Exception:
            pass
