"""Milvus-based per-agent knowledge base with fastembed semantic embeddings.

Each Agent owns an independent Milvus collection. Knowledge upload uses a
user-preprocessed JSON format; the server embeds the text and stores metadata.

Supported JSON formats:

1) Object wrapper:
{
  "documents": [
    {"id": "optional-id", "text": "knowledge text", "metadata": {"source": "doc"}}
  ]
}

2) Top-level array:
[
  {"id": "optional-id", "text": "knowledge text", "metadata": {"source": "doc"}}
]

3) Compact fields:
[
  {"content": "knowledge text", "source": "doc", "title": "...", "tags": ["..."]}
]
"""

from __future__ import annotations

import hashlib
import os
from typing import Any

from fastembed import TextEmbedding
from pymilvus import DataType, MilvusClient


class MilvusKnowledgeBase:
    """Per-agent knowledge base using Milvus + fastembed."""

    def __init__(self, uri: str | None = None, dim: int = 384) -> None:
        # Keep URI configurable. User can set MILVUS_URI to Docker endpoint, e.g. http://127.0.0.1:19530.
        # Empty means Milvus is not configured yet; the app can still start.
        self.uri = uri if uri is not None else os.environ.get("MILVUS_URI", "")
        self.dim = dim
        self._client: MilvusClient | None = None
        self._model = TextEmbedding("BAAI/bge-small-en-v1.5")

    @property
    def client(self) -> MilvusClient:
        if not self.uri:
            raise RuntimeError("MILVUS_URI is not configured")
        if self._client is None:
            self._client = MilvusClient(uri=self.uri)
        return self._client

    def _collection_name(self, agent_id: str) -> str:
        return f"agent_{agent_id.replace('-', '_')}"

    def _embed(self, texts: list[str]) -> list[list[float]]:
        return [e.tolist() for e in self._model.embed(texts)]

    def ensure_collection(self, agent_id: str) -> str:
        """Create the agent-specific Milvus collection if it does not exist."""
        name = self._collection_name(agent_id)
        if name in self.client.list_collections():
            return name

        schema = MilvusClient.create_schema(auto_id=False, enable_dynamic_field=True)
        schema.add_field(field_name="id", datatype=DataType.VARCHAR, is_primary=True, max_length=256)
        schema.add_field(field_name="vector", datatype=DataType.FLOAT_VECTOR, dim=self.dim)
        schema.add_field(field_name="text", datatype=DataType.VARCHAR, max_length=8192)
        schema.add_field(field_name="source", datatype=DataType.VARCHAR, max_length=512)
        schema.add_field(field_name="title", datatype=DataType.VARCHAR, max_length=512)
        schema.add_field(field_name="role", datatype=DataType.VARCHAR, max_length=128)

        index_params = self.client.prepare_index_params()
        index_params.add_index(
            field_name="vector",
            index_type="AUTOINDEX",
            metric_type="COSINE",
        )

        self.client.create_collection(
            collection_name=name,
            schema=schema,
            index_params=index_params,
        )
        return name

    def _normalize_json_docs(self, data: Any) -> tuple[list[str], list[dict], list[str] | None]:
        """Normalize user-uploaded JSON into texts/metas/ids."""
        docs = data.get("documents") if isinstance(data, dict) else data
        if not isinstance(docs, list):
            raise ValueError("JSON must be a list or an object with a 'documents' list")

        texts: list[str] = []
        metas: list[dict] = []
        ids: list[str] = []

        for i, item in enumerate(docs):
            if isinstance(item, str):
                text = item.strip()
                meta = {"source": "json_upload"}
                doc_id = ""
            elif isinstance(item, dict):
                text = str(item.get("text") or item.get("content") or "").strip()
                raw_meta = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
                meta = {
                    **raw_meta,
                    "source": item.get("source") or raw_meta.get("source") or "json_upload",
                    "title": item.get("title") or raw_meta.get("title") or "",
                    "role": item.get("role") or raw_meta.get("role") or "",
                    "tags": item.get("tags") or raw_meta.get("tags") or [],
                }
                doc_id = str(item.get("id") or "")
            else:
                continue

            if not text:
                continue
            if not doc_id:
                digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]
                doc_id = f"json_{i}_{digest}"
            texts.append(text)
            metas.append(meta)
            ids.append(doc_id)

        return texts, metas, ids

    def add_json(self, agent_id: str, data: Any) -> int:
        """Add user-preprocessed JSON documents into this agent's collection."""
        texts, metas, ids = self._normalize_json_docs(data)
        return self.add(agent_id, texts=texts, metas=metas, ids=ids)

    def add(
        self,
        agent_id: str,
        texts: list[str],
        metas: list[dict] | None = None,
        ids: list[str] | None = None,
    ) -> int:
        if not texts:
            return 0

        name = self.ensure_collection(agent_id)
        embeddings = self._embed(texts)
        if ids is None:
            ids = [f"doc_{i}_{hashlib.sha1(t.encode('utf-8')).hexdigest()[:16]}" for i, t in enumerate(texts)]
        if metas is None:
            metas = [{"source": "upload"} for _ in texts]

        rows = []
        for i, text in enumerate(texts):
            meta = metas[i] if i < len(metas) else {}
            rows.append({
                "id": ids[i],
                "vector": embeddings[i],
                "text": text,
                "source": str(meta.get("source", "upload")),
                "title": str(meta.get("title", "")),
                "role": str(meta.get("role", "")),
                "tags": meta.get("tags", []),
            })

        self.client.upsert(collection_name=name, data=rows)
        return len(rows)

    def search(self, agent_id: str, query: str, top_k: int = 5) -> list[dict]:
        try:
            name = self.ensure_collection(agent_id)
            if self.count(agent_id) == 0:
                return []
            query_emb = self._embed([query])[0]
            results = self.client.search(
                collection_name=name,
                data=[query_emb],
                anns_field="vector",
                limit=top_k,
                output_fields=["text", "source", "title", "role", "tags"],
            )
            hits = results[0] if results else []
            items = []
            for hit in hits:
                entity = hit.get("entity", {})
                items.append({
                    "content": entity.get("text", ""),
                    "score": round(float(hit.get("distance", 0.0)), 3),
                    "metadata": {
                        "source": entity.get("source", ""),
                        "title": entity.get("title", ""),
                        "role": entity.get("role", ""),
                        "tags": entity.get("tags", []),
                    },
                })
            return items
        except Exception:
            return []

    def count(self, agent_id: str) -> int:
        try:
            name = self.ensure_collection(agent_id)
            stats = self.client.get_collection_stats(collection_name=name)
            return int(stats.get("row_count", 0))
        except Exception:
            return 0

    def delete_collection(self, agent_id: str) -> None:
        name = self._collection_name(agent_id)
        try:
            if name in self.client.list_collections():
                self.client.drop_collection(collection_name=name)
        except Exception:
            pass


# Backward-compatible name used by app.py
ChromaKnowledgeBase = MilvusKnowledgeBase
