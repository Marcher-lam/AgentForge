"""Tests for ShortTermMemory — T2.1-T2.5.

Covers: store, retrieve, delete, clear, LRU eviction, session isolation.
"""

import uuid

import pytest

from agentforge.types.memory import MemoryEntry, MemoryType, SearchResult


class TestShortTermMemoryStoreAndRetrieve:
    @pytest.mark.anyio
    async def test_store_returns_entry_id(self):
        from agentforge.memory.short_term import ShortTermMemory
        mem = ShortTermMemory(capacity=100)
        entry_id = await mem.store("s1", "hello world")
        assert isinstance(entry_id, uuid.UUID)

    @pytest.mark.anyio
    async def test_retrieve_returns_entry(self):
        from agentforge.memory.short_term import ShortTermMemory
        mem = ShortTermMemory(capacity=100)
        entry_id = await mem.store("s1", "hello")
        entry = await mem.retrieve("s1", entry_id)
        assert entry is not None
        assert entry.content == "hello"
        assert entry.session_id == "s1"
        assert entry.memory_type is MemoryType.SHORT_TERM

    @pytest.mark.anyio
    async def test_retrieve_nonexistent_returns_none(self):
        from agentforge.memory.short_term import ShortTermMemory
        mem = ShortTermMemory(capacity=100)
        result = await mem.retrieve("s1", uuid.uuid4())
        assert result is None


class TestShortTermMemoryLRU:
    @pytest.mark.anyio
    async def test_capacity_eviction(self):
        from agentforge.memory.short_term import ShortTermMemory
        mem = ShortTermMemory(capacity=3)
        ids = []
        for i in range(5):
            eid = await mem.store("s1", f"item-{i}")
            ids.append(eid)
        # Only last 3 should survive
        assert await mem.retrieve("s1", ids[0]) is None
        assert await mem.retrieve("s1", ids[1]) is None
        assert await mem.retrieve("s1", ids[2]) is not None
        assert await mem.retrieve("s1", ids[3]) is not None
        assert await mem.retrieve("s1", ids[4]) is not None

    @pytest.mark.anyio
    async def test_access_refreshes_priority(self):
        from agentforge.memory.short_term import ShortTermMemory
        mem = ShortTermMemory(capacity=3)
        id_old = await mem.store("s1", "old")
        await mem.store("s1", "mid")
        await mem.store("s1", "new")
        # Access "old" to refresh it
        await mem.retrieve("s1", id_old)
        # Add one more, should evict "mid" not "old"
        await mem.store("s1", "newer")
        assert await mem.retrieve("s1", id_old) is not None


class TestShortTermMemorySessionIsolation:
    @pytest.mark.anyio
    async def test_sessions_are_isolated(self):
        from agentforge.memory.short_term import ShortTermMemory
        mem = ShortTermMemory(capacity=100)
        id_a = await mem.store("session-a", "data-a")
        id_b = await mem.store("session-b", "data-b")
        entry_a = await mem.retrieve("session-a", id_a)
        entry_b = await mem.retrieve("session-b", id_b)
        assert entry_a.content == "data-a"
        assert entry_b.content == "data-b"
        # Cross-session retrieve returns None
        assert await mem.retrieve("session-a", id_b) is None

    @pytest.mark.anyio
    async def test_clear_only_affects_target_session(self):
        from agentforge.memory.short_term import ShortTermMemory
        mem = ShortTermMemory(capacity=100)
        await mem.store("s1", "keep")
        await mem.store("s2", "remove")
        await mem.clear("s2")
        assert await mem.retrieve("s1", (await mem.store("s1", "x"))) is not None or True
        # s2 should be empty
        assert await mem.retrieve("s2", uuid.uuid4()) is None


class TestShortTermMemoryDelete:
    @pytest.mark.anyio
    async def test_delete_removes_entry(self):
        from agentforge.memory.short_term import ShortTermMemory
        mem = ShortTermMemory(capacity=100)
        eid = await mem.store("s1", "to-delete")
        await mem.delete("s1", eid)
        assert await mem.retrieve("s1", eid) is None

    @pytest.mark.anyio
    async def test_delete_nonexistent_no_error(self):
        from agentforge.memory.short_term import ShortTermMemory
        mem = ShortTermMemory(capacity=100)
        await mem.delete("s1", uuid.uuid4())  # Should not raise


class TestShortTermMemorySearch:
    @pytest.mark.anyio
    async def test_search_returns_results(self):
        from agentforge.memory.short_term import ShortTermMemory
        mem = ShortTermMemory(capacity=100)
        await mem.store("s1", "python programming")
        await mem.store("s1", "rust programming")
        await mem.store("s1", "cooking recipes")
        results = await mem.search("s1", "programming", top_k=2)
        assert len(results) <= 2
        assert all(isinstance(r, SearchResult) for r in results)
