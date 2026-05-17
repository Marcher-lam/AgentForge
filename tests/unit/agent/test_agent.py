"""Tests for AgentBase ABC + State Machine — Task 2."""

import uuid

import anyio
import pytest

from agentforge.agent.base import AgentBase
from agentforge.types.errors import AgentInitFailed, InvalidStateTransition
from agentforge.types.state import AgentState


class SimpleAgent(AgentBase):
    """Concrete agent for testing."""

    def __init__(self, fail_init: bool = False, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._fail_init = fail_init
        self.lifecycle: list[str] = []

    async def _on_init(self) -> None:
        if self._fail_init:
            raise RuntimeError("init boom")
        self.lifecycle.append("init")

    async def _on_run(self) -> None:
        self.lifecycle.append("run")

    async def _on_stop(self) -> None:
        self.lifecycle.append("stop")

    async def _on_destroy(self) -> None:
        self.lifecycle.append("destroy")


class TestLifecycle:
    @pytest.mark.anyio
    async def test_full_lifecycle(self):
        agent = SimpleAgent(name="test")
        assert agent.state == AgentState.CREATED

        await agent.init()
        assert agent.state == AgentState.INITIALIZED

        await agent.run()
        assert agent.state == AgentState.RUNNING

        await agent.stop()
        assert agent.state == AgentState.STOPPED

        await agent.destroy()
        assert agent.state == AgentState.DESTROYED

        assert agent.lifecycle == ["init", "run", "stop", "destroy"]

    @pytest.mark.anyio
    async def test_init_failure_sets_destroyed(self):
        agent = SimpleAgent(fail_init=True)
        with pytest.raises(AgentInitFailed):
            await agent.init()
        assert agent.state == AgentState.DESTROYED

    @pytest.mark.anyio
    async def test_destroy_idempotent(self):
        agent = SimpleAgent()
        await agent.init()
        await agent.destroy()
        assert agent.state == AgentState.DESTROYED
        await agent.destroy()
        assert agent.state == AgentState.DESTROYED
        assert agent.lifecycle.count("destroy") == 1

    @pytest.mark.anyio
    async def test_agent_id_auto_generated(self):
        agent = SimpleAgent()
        assert isinstance(agent.agent_id, uuid.UUID)

    @pytest.mark.anyio
    async def test_agent_id_custom(self):
        custom_id = uuid.uuid4()
        agent = SimpleAgent(agent_id=custom_id)
        assert agent.agent_id == custom_id

    def test_name_fallback_to_class_name(self):
        agent = SimpleAgent()
        assert agent.name == "SimpleAgent"

    def test_name_explicit(self):
        agent = SimpleAgent(name="CustomName")
        assert agent.name == "CustomName"


class TestInvalidTransitions:
    @pytest.mark.anyio
    async def test_run_without_init(self):
        agent = SimpleAgent()
        with pytest.raises(InvalidStateTransition):
            await agent.run()

    @pytest.mark.anyio
    async def test_stop_without_run(self):
        agent = SimpleAgent()
        await agent.init()
        with pytest.raises(InvalidStateTransition):
            await agent.stop()

    @pytest.mark.anyio
    async def test_double_init(self):
        agent = SimpleAgent()
        await agent.init()
        with pytest.raises(InvalidStateTransition):
            await agent.init()

    @pytest.mark.anyio
    async def test_destroy_from_any_state(self):
        agent = SimpleAgent()
        await agent.destroy()
        assert agent.state == AgentState.DESTROYED


class TestConcurrency:
    @pytest.mark.anyio
    async def test_concurrent_init_only_one_succeeds(self):
        agent = SimpleAgent()
        results: list[object] = []

        async def try_init() -> None:
            try:
                await agent.init()
                results.append("ok")
            except (InvalidStateTransition, AgentInitFailed):
                results.append("fail")

        async with anyio.create_task_group() as tg:
            tg.start_soon(try_init)
            tg.start_soon(try_init)

        assert results.count("ok") == 1
        assert results.count("fail") == 1


class TestEvents:
    @pytest.mark.anyio
    async def test_state_changed_event(self):
        agent = SimpleAgent()
        transitions: list[tuple[AgentState, AgentState]] = []

        agent.events.on("state_changed", lambda old, new: transitions.append((old, new)))
        await agent.init()
        assert len(transitions) == 1
        assert transitions[0] == (AgentState.CREATED, AgentState.INITIALIZED)

    @pytest.mark.anyio
    async def test_multiple_event_handlers(self):
        agent = SimpleAgent()
        call_log: list[str] = []

        agent.events.on("state_changed", lambda o, n: call_log.append("handler1"))
        agent.events.on("state_changed", lambda o, n: call_log.append("handler2"))
        await agent.init()
        assert call_log == ["handler1", "handler2"]

    @pytest.mark.anyio
    async def test_off_removes_handler(self):
        agent = SimpleAgent()
        call_log: list[str] = []
        handler = lambda o, n: call_log.append("called")

        agent.events.on("state_changed", handler)
        await agent.init()
        assert call_log == ["called"]

        agent.events.off("state_changed", handler)
        await agent.destroy()
        assert call_log == ["called"]

    @pytest.mark.anyio
    async def test_async_handler_is_awaited(self):
        agent = SimpleAgent()
        results: list[str] = []

        async def async_handler(old: object, new: object) -> None:
            results.append(f"async:{new}")

        agent.events.on("state_changed", async_handler)
        await agent.init()
        assert results == [f"async:{AgentState.INITIALIZED}"]
