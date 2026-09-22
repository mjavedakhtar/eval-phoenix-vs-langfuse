# MCP server traces in Phoenix (no agent)

This is a **second** experiment. It is not the Phoenix vs Langfuse agent comparison.

## What it is

An MCP server that exposes the same fake plant tools (graph, time series, alarms, work orders). A small client calls those tools over MCP. There is **no LangGraph and no LLM**.

Phoenix should show tool-call spans in a project named **`mcp-plant-fabric`**.

## Why it exists

Someone may care about logging the **tool server**, not the agent. This checks: can Phoenix record MCP traffic if nothing “agent-like” is running?

It also starts the server in its **own process** and registers Phoenix’s tracer there first. That avoids the “another trace provider is already in place, so the project is not auto-created” problem.

## How to run

Phoenix must already be up (`uvx arize-phoenix serve`).

```bash
uv run python experiments/run_mcp_phoenix.py
```

Then in Phoenix: **Projects → mcp-plant-fabric** (not `default`, not `data-fabric-agent`).

You should see `tools/call …` spans. Line 9 is the graph lookup that returns no hits.

## What this is not

It does not replace the agent lab. It does not prove Langfuse. It does not use a production MCP stack — FastMCP + the same synthetic plant.
