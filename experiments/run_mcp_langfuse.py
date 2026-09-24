"""Call the plant MCP server with no agent and no LLM.

Starts mcp_server.py in its own process (own TracerProvider → Langfuse OTLP),
then invokes tools over MCP HTTP. Filter Langfuse Tracing by session
`mcp-plant-fabric` (or tag `mcp`).

    ./scripts/start-langfuse.sh
    uv run python experiments/run_mcp_langfuse.py
"""

from __future__ import annotations

import asyncio
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from fastmcp import Client

# Same plant questions as run_mcp_phoenix.py — different sink, not different tools.
PORT = int(os.getenv("MCP_SERVER_PORT", "8766"))
MCP_URL = os.getenv("MCP_SERVER_URL", f"http://127.0.0.1:{PORT}/mcp")
SERVER = Path(__file__).resolve().parent / "mcp_server.py"
SESSION = os.getenv("LANGFUSE_MCP_SESSION", "mcp-plant-fabric")

CALLS = [
    ("search_knowledge_graph_tool", {"query": "Line3"}),
    ("get_timeseries_tool", {"asset": "Line3", "metric": "scrap_rate"}),
    ("get_alarms_tool", {"asset": "Press12"}),
    ("search_knowledge_graph_tool", {"query": "Line9"}),
    ("get_work_orders_tool", {"asset": "OvenA"}),
    ("get_alarms_tool", {"asset": "OvenA"}),
]


def _wait_for_server(timeout_s: float = 20.0) -> None:
    deadline = time.time() + timeout_s
    last_err = None
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", PORT), timeout=1):
                time.sleep(1.5)
                return
        except OSError as exc:
            last_err = exc
            time.sleep(0.2)
    raise RuntimeError(f"MCP server did not start on port {PORT}: {last_err}")


async def _call_tools() -> None:
    async with Client(MCP_URL) as client:
        tools = await client.list_tools()
        print("Tools:", [t.name for t in tools])
        for name, args in CALLS:
            print(f"\n=== MCP {name} {args} ===")
            result = await client.call_tool(name, args)
            text = getattr(result, "data", None) or getattr(result, "content", result)
            print(str(text)[:500])


def main() -> None:
    if not os.getenv("LANGFUSE_PUBLIC_KEY") or not os.getenv("LANGFUSE_SECRET_KEY"):
        raise RuntimeError(
            "Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY in .env."
        )

    env = os.environ.copy()
    env["MCP_TRACE_BACKEND"] = "langfuse"
    env["MCP_SERVER_PORT"] = str(PORT)
    log_path = Path(__file__).parent / "results" / "mcp_server_langfuse.log"
    log_path.parent.mkdir(exist_ok=True)
    logf = open(log_path, "w")
    proc = subprocess.Popen(
        [sys.executable, str(SERVER)],
        env=env,
        cwd=str(Path(__file__).resolve().parents[1]),
        stdout=logf,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        _wait_for_server()
        asyncio.run(_call_tools())
        time.sleep(2)
        host = os.getenv("LANGFUSE_BASE_URL") or os.getenv("LANGFUSE_HOST") or "http://localhost:3000"
        print(f"\nNo agent ran. Open Langfuse Tracing: {host}")
        print(f"Filter session '{SESSION}' (tag mcp). You should see tools/call spans, not LangGraph.")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        logf.close()


if __name__ == "__main__":
    main()
