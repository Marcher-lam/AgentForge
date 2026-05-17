"""Start both backend API server and frontend dev server."""

from __future__ import annotations

import argparse
import asyncio
import subprocess
import sys
import os

import uvicorn


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Start AgentForge backend + frontend")
    p.add_argument("--provider", default="openai", help="LLM provider")
    p.add_argument("--model", default="", help="Model name")
    p.add_argument("--base-url", default="", help="API base URL")
    p.add_argument("--api-key", default="", help="API key")
    p.add_argument("--system-prompt", default="You are a helpful AI assistant.", help="System prompt")
    p.add_argument("--host", default="0.0.0.0", help="Backend host")
    p.add_argument("--port", type=int, default=8000, help="Backend port")
    p.add_argument("--frontend-port", type=int, default=5173, help="Frontend port")
    p.add_argument("--no-frontend", action="store_true", help="Skip frontend launch")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    os.environ.setdefault("LLM_PROVIDER", args.provider)
    if args.model:
        os.environ.setdefault("LLM_MODEL", args.model)
    if args.api_key:
        os.environ.setdefault("LLM_API_KEY", args.api_key)
    if args.base_url:
        os.environ.setdefault("LLM_BASE_URL", args.base_url)
    os.environ.setdefault("LLM_SYSTEM_PROMPT", args.system_prompt)

    frontend_proc = None
    if not args.no_frontend:
        frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "frontend")
        if os.path.isdir(frontend_dir):
            print(f"Starting frontend dev server on port {args.frontend_port}...")
            frontend_proc = subprocess.Popen(
                ["npx", "vite", "--port", str(args.frontend_port), "--host"],
                cwd=frontend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        else:
            print(f"Frontend directory not found at {frontend_dir}, skipping.")

    print(f"Starting backend API server on http://{args.host}:{args.port}")
    print(f"API docs: http://{args.host}:{args.port}/docs")
    print(f"WebSocket: ws://{args.host}:{args.port}/ws")
    print()

    try:
        uvicorn.run(
            "agentforge.server.main:create_and_run",
            host=args.host,
            port=args.port,
            reload=False,
            factory=True,
        )
    finally:
        if frontend_proc:
            print("Shutting down frontend...")
            frontend_proc.terminate()
            frontend_proc.wait(timeout=5)


if __name__ == "__main__":
    main()
