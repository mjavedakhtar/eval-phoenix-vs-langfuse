# Agent flight recorders

**Same diagnostic agent. Same five questions. Two self-hosted observability stacks.**

When an agent calls a knowledge graph, time series, alarms, and work orders, the interesting failure is rarely the last paragraph. It is the hop it skipped, the asset it invented, or the alarm it pinned on the wrong machine. This repo is a side-by-side lab of [Arize Phoenix](https://arize.com/phoenix/) and [Langfuse](https://langfuse.com/) — both run on your laptop — scoring whether you can *see* those hops and *test* them.

No live plant. No customer data. A tiny invented factory, local [Ollama](https://ollama.com/), and golden cases that fail if the agent does not use the tools.

---

## Why this comparison

Chatbot evals score the final answer. Agentic evals have to score the **path**.

| If the agent… | A chatbot metric will… | A trace + eval lab should… |
| --- | --- | --- |
| Skip the graph and guess topology | Often still look fluent | Fail trajectory + groundedness |
| Mix Oven A alarms with Press 12 | Miss it | Fail the citation check |
| Invent Line 9 | Miss it | Fail the refusal case |

Phoenix is the lightest self-host (OpenTelemetry / OpenInference, one process). Langfuse is the production-shaped self-host (Docker Compose, traces, datasets, scores, prompt management, MIT core). LangSmith is intentionally out: the useful product is cloud-hosted.

> **Lab finding — self-host friction is not theoretical.** Phoenix: `uvx arize-phoenix serve`, UI on `:6006` in minutes. Langfuse: official Compose (web, worker, Postgres, ClickHouse, Redis, Minio). First boot on an **x86_64 qemu Colima** on an M3 Pro pulled six images, then ran **49 ClickHouse migrations**; a `lab@localhost` init email 500'd the app (`z.email()` rejects it); recreating web flapped Minio/Postgres healthchecks; Tracing then timed out on `events.getSdkVersionInfo` while ClickHouse sat at ~1000% CPU. **Native aarch64 Colima + arm64 images** made the same UI fast, and Line 3 / Line 9 trees are now captured. Details: [docs/comparison.md](docs/comparison.md).

**Resume line (copy):** Compared self-hosted LLM observability (Arize Phoenix vs Langfuse) on a multi-tool diagnostic agent, with code evals for groundedness, tool trajectory, and hallucination traps. Both UIs showed the skipped Line 3 hops and the Line 9 “no alarms” miss. Phoenix was minutes to first trace; Langfuse’s Compose stack was the costly half of time-to-first-trace.

---

## Lab snapshot (both recorders scored)

Local Ollama `llama3.2:3b`, five golden questions, code evals in `experiments/evals.py`. Same agent, same scores on Phoenix and Langfuse — the 40% is the model, not the backend.

| | Rate | What it means |
| --- | ---: | --- |
| Task success | **40%** | 2 / 5 cases: upstream Press 12, Oven A alarms |
| Grounded | **60%** | Cited the tokens the golden set required |
| Hallucination | **0%** | Did not invent Line 9 as a running plant |
| Trajectory | **60%** | Called the expected tools (not just a fluent paragraph) |

The 40% is the point of the lab, not a bug in Phoenix. The model sounded fine. The traces showed the missing hops.

<p align="center">
  <img src="docs/images/phoenix/01-projects.png" alt="Phoenix projects: mcp-plant-fabric 18 traces, data-fabric-agent 5 traces, default empty" width="100%">
</p>

<p align="center"><sub><b>Phoenix after the lab.</b> Named projects, not <code>default</code>. Agent runs land in <code>data-fabric-agent</code>. MCP-only traffic lands in <code>mcp-plant-fabric</code>.</sub></p>

<p align="center">
  <img src="docs/images/langfuse/02-traces-list.png" alt="Langfuse Tracing table with five LangGraph rows for the golden set" width="100%">
</p>

<p align="center"><sub><b>Langfuse Tracing</b> after the same five questions. All rows are named <code>LangGraph</code> — you open a row to see the question. Catchable, extra click vs Phoenix.</sub></p>

---

## The two traces that matter

Open these two in any backend you try. A small local model may take a clumsy path; you are judging whether the UI shows the path.

### 1. Line 3 scrap spike — skipped hops

Golden path: knowledge graph → scrap time series → alarms. The agent only called `get_timeseries`, then answered with the 07:10 / 8.7% point. Fluent. **Task fail.** Phoenix shows a single tool span and the exact payload.

<p align="center">
  <img src="docs/images/phoenix/03-line3-scrap-trace.png" alt="Phoenix trace tree for Line 3 scrap: only get_timeseries_tool, input Line3 scrap_rate, output 8.7 percent at 07:10" width="100%">
</p>

<p align="center"><sub>Phoenix: <code>LangGraph → tools → get_timeseries_tool</code>. No graph. No alarms. Input <code>{"asset": "Line3", "metric": "scrap_rate"}</code>.</sub></p>

<p align="center">
  <img src="docs/images/langfuse/03-line3-scrap-trace.png" alt="Langfuse trace tree for Line 3 scrap: only get_timeseries_tool under tools" width="100%">
</p>

<p align="center"><sub>Langfuse, same run: <code>LangGraph → tools → get_timeseries_tool</code>. Same skipped hops. Catchable in one expand.</sub></p>

### 2. Line 9 missing asset — wrong tool, no refusal

Golden path: search the graph, get zero hits, refuse. The agent called `get_alarms` on “Line 9”, got **Asset not in fabric**, and still said there were no alarms. **Task fail.** Phoenix shows the empty-asset error on the tool span.

<p align="center">
  <img src="docs/images/phoenix/04-line9-missing-trace.png" alt="Phoenix trace tree for Line 9: get_alarms_tool with Asset not in fabric error" width="100%">
</p>

<p align="center"><sub>Phoenix: input is the missing asset. Output is an empty alarm list plus <code>Asset not in fabric</code>.</sub></p>

<p align="center">
  <img src="docs/images/langfuse/04-line9-missing-trace.png" alt="Langfuse trace tree for Line 9: only get_alarms_tool under tools" width="100%">
</p>

<p align="center"><sub>Langfuse: <code>tools → get_alarms_tool</code> only. Answer in the panel: “Line 9 is not currently experiencing any alarms.” Same miss as Phoenix.</sub></p>

Full per-case table and the Phoenix vs Langfuse scorecard: **[docs/comparison.md](docs/comparison.md)**.

---

## What you get

```
experiments/
  plant_fabric.py     # invented plant: graph, metrics, alarms, work orders
  agent.py            # LangGraph copilot over those four tools
  dataset/golden.json # five cases, including a missing-asset refusal
  evals.py            # same scorecard for both backends
  run_phoenix.py
  run_langfuse.py
  mcp_server.py       # FastMCP, no LLM — second experiment
  run_mcp_phoenix.py
  run_mcp_langfuse.py
```

Synthetic assets only: Line3, Press12, OvenA, WarehouseB. Site name is `north`. Nothing here is operational data.

---

## Run it

Needs Python 3.11+, [uv](https://docs.astral.sh/uv/), [Ollama](https://ollama.com/) with `llama3.2:3b` (or any chat model), and Docker for Langfuse.

```bash
uv sync
cp .env.example .env
```

**Phoenix** — no account:

```bash
uvx arize-phoenix serve          # http://localhost:6006
uv run python experiments/run_phoenix.py
```

Open project **`data-fabric-agent`**, not `default`. Collector URL must include `/v1/traces`.

**Langfuse** — official Docker Compose, *your* UI (not Langfuse Cloud). Expect a long first boot (image pull + ClickHouse migrations). The script binds **:3001** if :3000 is already taken. Init user email must be a real-looking address (`lab@example.com`, not `lab@localhost`).

```bash
./scripts/start-langfuse.sh      # http://localhost:3000 or :3001
# wait until the UI actually loads, then:
uv run python experiments/run_langfuse.py
```

Open the **Line 3 scrap** trace and the **Line 9 missing** trace in both UIs. That pair is the comparison. On Apple Silicon, Colima must be **aarch64** (`colima start --arch aarch64 --vm-type vz`); an x86_64 qemu VM will look like the stack is “too heavy” when it is really emulating amd64 ClickHouse. If Langfuse is still migrating, it will refuse connections — that is first-boot, not a missing exporter.

---

## Second experiment: MCP server only (no agent)

A small MCP server exposes the same plant tools. A client calls them. **No LLM.** Phoenix records `tools/call …` spans in project `mcp-plant-fabric`. Langfuse records the same methods over OTLP (session/tag `mcp-plant-fabric`). The MCP process registers the tracer first.

```bash
uvx arize-phoenix serve          # if it is not already running
uv run python experiments/run_mcp_phoenix.py

./scripts/start-langfuse.sh      # if it is not already running
uv run python experiments/run_mcp_langfuse.py
```

<p align="center">
  <img src="docs/images/phoenix/05-mcp-plant-fabric-spans.png" alt="Phoenix mcp-plant-fabric project with tools/call spans for alarms, work orders, knowledge graph, and time series" width="100%">
</p>

<p align="center"><sub>Phoenix <code>mcp-plant-fabric</code>: 18 spans, including <code>tools/call get_alarms</code>, <code>search_knowledge_graph</code>, <code>get_timeseries</code>, <code>get_work_orders</code>.</sub></p>

<p align="center">
  <img src="docs/images/langfuse/05-mcp-plant-fabric-spans.png" alt="Langfuse Tracing table with MCP tool spans tagged mcp: get_alarms, tools/list, get_work_orders, search_knowledge_graph, get_timeseries, server/discover" width="100%">
</p>

<p align="center"><sub>Langfuse: same MCP methods, tag <code>mcp</code>, session <code>mcp-plant-fabric</code>. No LangGraph on those rows.</sub></p>

Details: [docs/mcp-phoenix.md](docs/mcp-phoenix.md).

---

## Scorecard

| Dimension | Phoenix | Langfuse |
| --- | --- | --- |
| Nested LLM + tool + retrieval spans | **yes** — LangGraph tree, ChatOllama, tool I/O | **yes** — same hops; extra Prompt / RunnableSequence nesting; I/O in the side panel |
| MCP-only (no agent) | **yes** — project `mcp-plant-fabric` | **yes** — OTLP; session/tag `mcp-plant-fabric` |
| Time-to-first-trace | minutes, one process | **hours** on first Compose boot; Tracing unusable on x86 qemu; native arm64 UI is then fast |
| Datasets → experiments → regression | code evals in-repo; Phoenix Datasets UI still empty | code evals in-repo; Langfuse Datasets / Experiments nav not exercised |
| Human labels on a span | **Annotate this span** in the drawer | **Annotate** / **Comment** on the trace; Human Annotation in the nav |
| Self-host / data stays on the machine | yes (ELv2) | yes (MIT core) — six containers |
| Footprint | light (`uvx arize-phoenix serve`) | Postgres + ClickHouse + Redis + Minio + web + worker |

---

## What this is not

- Not a vendor bake-off of every observability product
- Not a production data fabric, MES, or historian
- Not an employer case study (that write-up lives elsewhere and is not in this repo)

MIT licensed. Synthetic demo data only.
