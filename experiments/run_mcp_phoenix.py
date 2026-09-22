"""Call the plant MCP server with no agent and no LLM.

Starts mcp_server.py in its own process (own TracerProvider), then invokes
tools over MCP HTTP. Look in Phoenix project mcp-plant-fabric.

    uvx arize-phoenix serve          # already running is fine
    uv run python experiments/run_mcp_phoenix.py
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

PORT = int(os.getenv("MCP_SERVER_PORT", "8765"))
MCP_URL = os.getenv("MCP_SERVER_URL", f"http://127.0.0.1:{PORT}/mcp")
PROJECT = os.getenv("PHOENIX_MCP_PROJECT", "mcp-plant-fabric")
SERVER = Path(__file__).resolve().parent / "mcp_server.py"

# Same plant questions as the agent lab, but we call tools ourselves.
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
    env = os.environ.copy()
    log_path = Path(__file__).parent / "results" / "mcp_server.log"
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
        print(
            f"\nNo agent ran. Open Phoenix project '{PROJECT}': "
            "http://localhost:6006"
        )
        print("You should see tools/call spans, not LangGraph.")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        logf.close()


if __name__ == "__main__":
    main()
