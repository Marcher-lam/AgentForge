"""Tests for infrastructure — Task 5: logging, config, shutdown."""

import os
import signal

import pytest

from agentforge.infra.config import AgentForgeConfig, WebSocketConfig, load_config
from agentforge.infra.logging import configure_logging, get_agent_logger
from agentforge.infra.shutdown import GracefulShutdown


class TestConfig:
    def test_default_config(self):
        config = load_config()
        assert config.log_level == "INFO"
        assert config.websocket.host == "0.0.0.0"
        assert config.websocket.port == 8080

    def test_env_override(self, monkeypatch):
        monkeypatch.setenv("AGENTFORGE_LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("AGENTFORGE_WEBSOCKET_PORT", "9090")
        config = load_config()
        assert config.log_level == "DEBUG"
        assert config.websocket.port == 9090


class TestLogging:
    def test_configure_logging(self):
        configure_logging("INFO")
        logger = get_agent_logger("test-agent")
        assert logger is not None

    def test_agent_logger_with_topic(self):
        configure_logging("DEBUG")
        logger = get_agent_logger("agent-1", topic="test.topic")
        assert logger is not None


class TestGracefulShutdown:
    @pytest.mark.anyio
    async def test_shutdown_calls_stop_and_destroy(self):
        shutdown = GracefulShutdown()
        lifecycle: list[str] = []

        class FakeAgent:
            async def stop(self) -> None:
                lifecycle.append("stop")

            async def destroy(self) -> None:
                lifecycle.append("destroy")

        shutdown.register_agent(FakeAgent())
        await shutdown.shutdown_all()
        assert lifecycle == ["stop", "destroy"]

    @pytest.mark.anyio
    async def test_shutdown_callbacks(self):
        shutdown = GracefulShutdown()
        called: list[str] = []

        shutdown.on_shutdown(lambda: called.append("cb1"))
        shutdown.on_shutdown(lambda: called.append("cb2"))
        await shutdown.shutdown_all()
        assert called == ["cb1", "cb2"]

    @pytest.mark.anyio
    async def test_shutdown_async_callback(self):
        shutdown = GracefulShutdown()
        called: list[str] = []

        async def async_cb() -> None:
            called.append("async_done")

        shutdown.on_shutdown(async_cb)
        await shutdown.shutdown_all()
        assert called == ["async_done"]

    @pytest.mark.anyio
    async def test_shutdown_handles_errors(self):
        shutdown = GracefulShutdown()

        class BadAgent:
            async def stop(self) -> None:
                raise RuntimeError("boom")

            async def destroy(self) -> None:
                raise RuntimeError("boom2")

        shutdown.register_agent(BadAgent())
        await shutdown.shutdown_all()

    def test_signal_flag(self):
        shutdown = GracefulShutdown()
        assert not shutdown.shutdown_requested
        shutdown._handle_signal(2, None)
        assert shutdown.shutdown_requested

    def test_signal_idempotent(self):
        shutdown = GracefulShutdown()
        shutdown._handle_signal(2, None)
        shutdown._handle_signal(2, None)
        assert shutdown.shutdown_requested

    @pytest.mark.anyio
    async def test_shutdown_reversed_order(self):
        shutdown = GracefulShutdown()
        order: list[str] = []

        class Agent:
            def __init__(self, name: str) -> None:
                self.name = name

            async def stop(self) -> None:
                order.append(f"stop:{self.name}")

            async def destroy(self) -> None:
                order.append(f"destroy:{self.name}")

        shutdown.register_agent(Agent("first"))
        shutdown.register_agent(Agent("second"))
        await shutdown.shutdown_all()
        assert order == [
            "stop:second", "destroy:second",
            "stop:first", "destroy:first",
        ]

    def test_install_handlers(self):
        """Lines 29-30: install_handlers registers SIGINT/SIGTERM."""
        shutdown = GracefulShutdown()
        old_sigint = signal.getsignal(signal.SIGINT)
        shutdown.install_handlers()
        assert signal.getsignal(signal.SIGINT) is not old_sigint
        signal.signal(signal.SIGINT, old_sigint)  # restore

    @pytest.mark.anyio
    async def test_shutdown_callback_exception_handled(self):
        """Lines 59-60: callback exception during shutdown is caught."""
        shutdown = GracefulShutdown()
        called: list[str] = []

        def bad_callback() -> None:
            raise RuntimeError("callback failed")

        shutdown.on_shutdown(bad_callback)
        shutdown.on_shutdown(lambda: called.append("after_bad"))

        await shutdown.shutdown_all()
        assert called == ["after_bad"]  # second callback still runs
