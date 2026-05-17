"""EvoRL Agent REPL — one command to start chatting with an LLM-backed agent."""

from __future__ import annotations

import argparse
import asyncio
import uuid

from agentforge.bus.inprocess import InProcessMessageBus
from agentforge.infra.config import load_config
from agentforge.llm import create_backend
from agentforge.agent.llm_agent import LLMAgent


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="EvoRL Agent REPL")
    p.add_argument("--provider", default="openai", choices=["openai", "anthropic", "ollama"],
                    help="LLM provider (default: openai)")
    p.add_argument("--model", default="", help="Model name (default: per-provider default)")
    p.add_argument("--system-prompt", default="You are a helpful AI assistant.",
                    help="System prompt for the agent")
    p.add_argument("--temperature", type=float, default=0.7)
    p.add_argument("--max-tokens", type=int, default=2048)
    p.add_argument("--base-url", default="", help="Custom API base URL (e.g. http://127.0.0.1:8888/v1)")
    p.add_argument("--api-key", default="", help="API key (default: from env var)")
    return p.parse_args()


async def main() -> None:
    args = parse_args()
    config = load_config()

    bus = InProcessMessageBus()

    backend_kwargs: dict = {}
    if args.model:
        backend_kwargs["model"] = args.model
    if args.api_key:
        backend_kwargs["api_key"] = args.api_key
    if args.base_url:
        backend_kwargs["base_url"] = args.base_url
    if args.provider == "ollama" and "base_url" not in backend_kwargs:
        backend_kwargs["base_url"] = "http://localhost:11434"

    llm = create_backend(args.provider, **backend_kwargs)

    agent = LLMAgent(
        bus=bus,
        llm=llm,
        name="assistant",
        system_prompt=args.system_prompt,
        agent_id=uuid.uuid4(),
    )

    await agent.init()
    await agent.run()

    print(f"EvoRL Agent Ready | provider={args.provider} model={args.model or '(default)'}")
    print("Type 'quit' or 'exit' to stop.\n")

    try:
        while True:
            try:
                user_input = input("You> ")
            except EOFError:
                break
            if user_input.strip().lower() in ("quit", "exit"):
                break
            if not user_input.strip():
                continue
            try:
                response = await agent.chat(user_input)
                print(f"Agent> {response}\n")
            except Exception as e:
                print(f"Error> {e}\n")
    finally:
        await agent.stop()
        await agent.destroy()


if __name__ == "__main__":
    asyncio.run(main())
