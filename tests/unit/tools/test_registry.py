"""Unit tests for SimpleToolRegistry."""

from agentforge.tools.registry import SimpleToolRegistry


class TestSimpleToolRegistry:
    def test_register_and_list(self):
        reg = SimpleToolRegistry()
        reg.register("tool_a", lambda: None, {"description": "Tool A"})
        assert reg.list_tools() == ["tool_a"]

    def test_register_multiple(self):
        reg = SimpleToolRegistry()
        reg.register("a", lambda: 1, {"description": "A"})
        reg.register("b", lambda: 2, {"description": "B"})
        assert sorted(reg.list_tools()) == ["a", "b"]

    def test_get_existing(self):
        handler = lambda x: x * 2
        schema = {"description": "Double", "parameters": {}}
        reg = SimpleToolRegistry()
        reg.register("double", handler, schema)
        result = reg.get("double")
        assert result is not None
        assert result[0] is handler
        assert result[1] == schema

    def test_get_nonexistent(self):
        reg = SimpleToolRegistry()
        assert reg.get("missing") is None

    def test_unregister(self):
        reg = SimpleToolRegistry()
        reg.register("temp", lambda: None, {})
        reg.unregister("temp")
        assert reg.get("temp") is None
        assert reg.list_tools() == []

    def test_unregister_nonexistent(self):
        reg = SimpleToolRegistry()
        reg.unregister("nope")

    def test_overwrite_registration(self):
        reg = SimpleToolRegistry()
        reg.register("tool", lambda: 1, {"v": 1})
        reg.register("tool", lambda: 2, {"v": 2})
        entry = reg.get("tool")
        assert entry[1] == {"v": 2}
