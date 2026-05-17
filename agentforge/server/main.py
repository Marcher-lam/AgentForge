"""Uvicorn factory entrypoint — loads LLM config from env vars."""

from __future__ import annotations

import os

from agentforge.llm import create_backend
from agentforge.agent.llm_agent import LLMAgent
from agentforge.server.app import create_app


def create_and_run():
    app = create_app()
    state = app.state.agentforge

    provider = os.environ.get("LLM_PROVIDER", "openai")
    model = os.environ.get("LLM_MODEL", "")
    api_key = os.environ.get("LLM_API_KEY", "")
    base_url = os.environ.get("LLM_BASE_URL", "")
    system_prompt = os.environ.get("LLM_SYSTEM_PROMPT", "You are a helpful AI assistant.")

    state.llm_config = {
        "provider": provider,
        "model": model,
        "base_url": base_url,
        "api_key": api_key,
        "temperature": 0.7,
        "max_tokens": 2048,
    }

    # Auto-create a default agent
    kwargs: dict = {}
    if model:
        kwargs["model"] = model
    if api_key:
        kwargs["api_key"] = api_key
    if base_url:
        kwargs["base_url"] = base_url

    llm = create_backend(provider, **kwargs)
    agent = LLMAgent(
        bus=state.bus,
        llm=llm,
        name="assistant",
        system_prompt=system_prompt,
    )
    import asyncio, uuid

    async def _init():
        await agent.init()
        await agent.run()
        aid = str(agent.agent_id)
        state.agents[aid] = agent
        import uuid as _uuid
        session_id = str(_uuid.uuid4())
        state.sessions.append({
            "session_id": session_id,
            "type": "ONE_VS_ONE",
            "name": "Default Chat",
            "agent_ids": [aid],
            "unread_count": 0,
            "last_message": None,
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        })
        state.messages[session_id] = []

    loop = asyncio.get_event_loop()
    loop.create_task(_init())

    return app
