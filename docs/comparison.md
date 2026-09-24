# Phoenix vs Langfuse — public comparison

This is the write-up for GitHub (and a CV link). It uses only the synthetic plant in this repo. Employer-internal decision records are not published here.

**Setup:** same LangGraph agent, same five golden questions, local Ollama `llama3.2:3b`, both platforms self-hosted.

**Status:** Phoenix traces scored. Langfuse **self-host** scored from a real first boot (Compose). Langfuse **trace fidelity** not scored — the UI did not stay up long enough to send Line 3 / Line 9.

## The hook

A fluent answer can still be wrong in an agent. The flight recorder has to show *which tool fired*, *what it returned*, and *whether the model cited that* — including the case where the asset does not exist and the agent must refuse.

Two traces decide most of the product question:

1. **Line 3 scrap spike** — multi-hop (graph → time series → alarms)
2. **Line 9** — missing asset, must not invent a factory line

## Phoenix, as captured

Named projects after one agent run and one MCP run. `default` stays empty on purpose.

![Phoenix project cards](images/phoenix/01-projects.png)

![Five LangGraph traces in data-fabric-agent](images/phoenix/02-data-fabric-agent-traces.png)

## Langfuse self-host, as actually experienced

This is a scored finding, not a complaint. Phoenix is one process. Langfuse's documented self-host is a **production stack**.

What happened on a laptop Docker VM (Colima), same afternoon as the Phoenix screenshots:

| Step | What we saw |
| --- | --- |
| Images | Official `docker compose`: web, worker, Postgres, ClickHouse, Redis, Minio. Pull alone was tens of minutes. |
| First boot | UI binds nothing until entrypoint finishes. **49 ClickHouse migrations**, several 1–7 minutes each. `curl` to the UI returned empty until that completed. |
| Port | `:3000` was already taken; script moved the UI to **:3001**. |
| Then 500 | Init user `lab@localhost` fails Langfuse `z.email()`. App logs: `Invalid environment variables`. Valid-looking address required (`lab@example.com`). |
| Recreate | Restarting `langfuse-web` to pick up the email re-ran Prisma cleanup; Minio/Postgres **healthchecks flapped** (`mc ready` timeouts). Web sat in `Created` until deps were healthy again. |

**Trace screenshots from Langfuse: none yet.** The five-question runner was not started. Do not read the empty Langfuse columns below as “Langfuse cannot show hops.” They mean we have not seen those hops in that UI.

`./scripts/start-langfuse.sh` now: skip `:3000` if busy, seed a local project, reject `lab@localhost`.

## Results

Code evals (`experiments/evals.py`) against `experiments/dataset/golden.json`. Same scorer would apply to Langfuse once that run exists.

**Phoenix rates (n = 5):** task success **0.40** · grounded **0.60** · hallucination **0.00** · trajectory **0.60**

| Case | Phoenix task success | Langfuse task success | Notes |
| --- | --- | --- | --- |
| scrap-line-3 | no | — | Only `get_timeseries`. Answer cited 8.7% at 07:10. Missed graph + alarms (`Press12`, `overheat`). |
| upstream-press-12 | **yes** | — | `search_knowledge_graph` → WarehouseB. |
| oven-a-work-order | no | — | Called `get_work_orders`, cited WO-4419, said “Oven A”. Golden token is `OvenA` (no space) → grounded fail. |
| missing-line-9 | no | — | Called `get_alarms` instead of the graph. Tool returned *Asset not in fabric*. Answer: “not currently experiencing any alarms” — not a refusal. |
| oven-a-alarms | **yes** | — | `get_alarms` → thermocouple drift. Did not mix in Press 12 overheat. |

| Dimension (1–5) | Phoenix | Langfuse | What I actually saw |
| --- | --- | --- | --- |
| Trace fidelity | **5** | — | Phoenix: nested `LangGraph` → `ChatOllama` → `tools` → `get_*_tool`, with JSON input/output. Langfuse: not observed. |
| Offline evals / experiments | **3** | — | Repeatable code evals in-repo. Phoenix **Datasets & Experiments** counter is still 0. |
| Human review loop | **4** | — | Phoenix span drawer has **Annotate this span**. Not exercised with a domain label. |
| Self-host friction | **5** | **2** | Phoenix: `uvx arize-phoenix serve`. Langfuse: six containers; first boot is a platform install; healthchecks are brittle on a laptop VM. |
| Time-to-first-trace | **4** | **1** | Phoenix: minutes after `/v1/traces` + project name (empty `default` is a footgun). Langfuse: hours to a listening UI; then 500 from a bad init email; no agent traces ingested. |

### Line 3 — the skipped hop

![Line 3 scrap trace: only get_timeseries_tool](images/phoenix/03-line3-scrap-trace.png)

Phoenix makes the failure obvious: one tool, `Line3` / `scrap_rate`, points including 8.7% at 07:10. A chatbot metric would often pass this answer. Trajectory does not.

### Line 9 — the missing asset

![Line 9 trace: get_alarms_tool returns asset not in fabric](images/phoenix/04-line9-missing-trace.png)

The tool already knew the asset is not in the fabric. The model did not turn that into a refusal. That is exactly the span a reviewer should label.

## MCP-only (not part of the head-to-head)

Same plant tools, FastMCP HTTP, **no LLM**. Project `mcp-plant-fabric` auto-created (own process, tracer registered first). 18 spans: `tools/call` for graph, time series, alarms, work orders, plus `tools/list` / `server/discover`.

![MCP plant fabric spans](images/phoenix/05-mcp-plant-fabric-spans.png)

Write-up: [mcp-phoenix.md](mcp-phoenix.md).

## Take

Phoenix already answers the observability question for this agent: **you can see the hop that did not happen, and the tool error the model ignored.** Time-to-first-trace is a single process if the OTLP URL is correct. Offline evals in this lab live in the repo, not yet in Phoenix datasets — so Phoenix is not “done” as an eval platform on this evidence, only as a flight recorder.

Langfuse's **self-host cost is real on a laptop**: Compose + ClickHouse first-boot dominated the calendar, before any Line 3 tree existed. That does not prove Langfuse traces are worse. It does prove you should budget a VM/K8s owner, not treat `docker compose up` as equivalent to `uvx arize-phoenix serve`. Until Line 3 and Line 9 exist in the Langfuse UI, do not pick a platform on fidelity. Dual-export is a hedge, not a strategy.

## CV blurb

Compared Arize Phoenix and Langfuse as self-hosted observability for a tool-using diagnostic agent (knowledge graph, metrics, alarms, work orders). Built a synthetic golden set and code evals for groundedness, tool trajectory, and hallucination, including a must-refuse missing-asset case. Phoenix traces showed a fluent Line 3 answer that skipped graph and alarms, and a Line 9 “no alarms” answer after the tool returned asset-not-in-fabric. Langfuse self-host (Postgres, ClickHouse, Minio, Redis) took hours to first UI on a laptop Docker VM; trace comparison there is still open.
