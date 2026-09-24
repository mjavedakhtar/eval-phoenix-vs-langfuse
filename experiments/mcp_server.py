"""MCP server over the synthetic plant. No agent, no LLM.

OpenTelemetry is configured before FastMCP is imported so this process owns
the TracerProvider (the conflict the architect hit when another provider was
already registered).

    MCP_TRACE_BACKEND=phoenix   uv run python experiments/mcp_server.py
    MCP_TRACE_BACKEND=langfuse  uv run python experiments/mcp_server.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

_BACKEND = os.getenv("MCP_TRACE_BACKEND", "phoenix").strip().lower()

if _BACKEND == "langfuse":
    from langfuse_otel import register_langfuse_otel

    register_langfuse_otel()
else:
    from phoenix.otel import register

    from phoenix_endpoint import traces_endpoint

    register(
        project_name=os.getenv("PHOENIX_MCP_PROJECT", "mcp-plant-fabric"),
        endpoint=traces_endpoint(),
        protocol="http/protobuf",
        auto_instrument=False,
    )

from fastmcp import FastMCP

from plant_fabric import get_alarms, get_timeseries, get_work_orders, search_knowledge_graph

mcp = FastMCP("plant-fabric-mcp")


@mcp.tool
def search_knowledge_graph_tool(query: str) -> str:
    """Look up assets and relations in the plant knowledge graph."""
    return json.dumps(search_knowledge_graph(query), default=str)


@mcp.tool
def get_timeseries_tool(asset: str, metric: str) -> str:
    """Fetch metric points for an asset (scrap_rate, temperature)."""
    return json.dumps(get_timeseries(asset, metric), default=str)


@mcp.tool
def get_alarms_tool(asset: str) -> str:
    """Fetch alarms for an asset id."""
    return json.dumps(get_alarms(asset), default=str)


@mcp.tool
def get_work_orders_tool(asset: str) -> str:
    """Fetch maintenance work orders for an asset id."""
    return json.dumps(get_work_orders(asset), default=str)


if __name__ == "__main__":
    port = int(os.getenv("MCP_SERVER_PORT", "8765"))
    print(f"MCP server on http://127.0.0.1:{port}/mcp")
    if _BACKEND == "langfuse":
        print("OTLP sink: Langfuse (session mcp-plant-fabric)")
    else:
        print(
            "Phoenix project: "
            f"{os.getenv('PHOENIX_MCP_PROJECT', 'mcp-plant-fabric')}"
        )
    mcp.run(transport="http", host="127.0.0.1", port=port)
