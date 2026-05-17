"""Tests for memory types — T1.1, T1.2, T1.3.

Covers: MemoryEntry, MemoryType, SearchResult data types.
"""

import uuid
from datetime import datetime, timezone

import pytest

from agentforge.types.memory import MemoryEntry, MemoryType, SearchResult


class TestMemoryType:
    def test_enum_values(self):
        assert MemoryType.SHORT_TERM.value == "short_term"
        assert MemoryType.LONG_TERM.value == "long_term"
        assert MemoryType.VECTOR.value == "vector"

    def test_enum_from_value(self):
        assert MemoryType("short_term") is MemoryType.SHORT_TERM


class TestMemoryEntry:
    def test_create_minimal(self):
        entry = MemoryEntry(
            content="test content",
            session_id="session-1",
            memory_type=MemoryType.SHORT_TERM,
        )
        assert entry.content == "test content"
        assert entry.session_id == "session-1"
        assert entry.memory_type is MemoryType.SHORT_TERM
        assert isinstance(entry.entry_id, uuid.UUID)
        assert isinstance(entry.timestamp, datetime)

    def test_create_with_metadata(self):
        entry = MemoryEntry(
            content="test",
            session_id="s1",
            memory_type=MemoryType.LONG_TERM,
            metadata={"source": "agent", "priority": 1},
            ttl_seconds=3600,
        )
        assert entry.metadata == {"source": "agent", "priority": 1}
        assert entry.ttl_seconds == 3600

    def test_frozen_immutability(self):
        entry = MemoryEntry(
            content="immutable",
            session_id="s1",
            memory_type=MemoryType.SHORT_TERM,
        )
        with pytest.raises(AttributeError):
            entry.content = "changed"

    def test_serialization_roundtrip(self):
        entry = MemoryEntry(
            content="serialize me",
            session_id="s1",
            memory_type=MemoryType.VECTOR,
            metadata={"key": "val"},
        )
        data = entry.to_dict()
        restored = MemoryEntry.from_dict(data)
        assert restored.content == entry.content
        assert restored.session_id == entry.session_id
        assert restored.memory_type == entry.memory_type
        assert restored.entry_id == entry.entry_id
        assert restored.metadata == entry.metadata


class TestSearchResult:
    def test_create(self):
        entry = MemoryEntry(
            content="hello",
            session_id="s1",
            memory_type=MemoryType.SHORT_TERM,
        )
        result = SearchResult(entry=entry, score=0.95, source="short_term")
        assert result.entry is entry
        assert result.score == 0.95
        assert result.source == "short_term"

    def test_frozen(self):
        entry = MemoryEntry(
            content="x",
            session_id="s1",
            memory_type=MemoryType.SHORT_TERM,
        )
        result = SearchResult(entry=entry, score=0.5, source="vector")
        with pytest.raises(AttributeError):
            result.score = 0.9
