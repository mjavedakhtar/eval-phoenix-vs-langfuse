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

**Resume line (copy):** Compared self-hosted LLM observability (Arize Phoenix vs Langfuse) on a multi-tool diagnostic agent, with code evals for groundedness, tool trajectory, and hallucination traps.

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
```

Synthetic assets only: Line3, Press12, OvenA, WarehouseB. Site name is `north`. Nothing here is operational data.

---

## Run it

Needs Python 3.11+, [Ollama](https://ollama.com/) with `llama3.2:3b` (or any chat model), and Docker for Langfuse.

```bash
cd experiments
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env
```

**Phoenix** — no account:

```bash
uvx arize-phoenix serve          # http://localhost:6006
python run_phoenix.py
```

**Langfuse** — local Docker, then a project on *your* UI (not Langfuse Cloud):

```bash
../scripts/start-langfuse.sh     # http://localhost:3000
# sign up locally, paste LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY into .env
python run_langfuse.py
```

```bash
python compare_results.py
```

Open the **Line 3 scrap** trace and the **Line 9 missing** trace in both UIs. That pair is the comparison. A small local model may take a clumsy tool path; you are judging whether the UI shows the path, not whether llama3.2 is a plant expert.

Fill [docs/comparison.md](docs/comparison.md) after you have screenshots. That page is the public write-up.

---

## Scorecard

| Dimension | Phoenix | Langfuse |
| --- | --- | --- |
| Nested LLM + tool + retrieval spans | lab | lab |
| Time-to-first-trace | one process | Compose + local keys |
| Datasets → experiments → regression | lab | lab |
| Human labels on a span | lab | lab |
| Self-host / data stays on the machine | yes (ELv2) | yes (MIT core) |
| Footprint | light | Postgres + ClickHouse + … |

---

## What this is not

- Not a vendor bake-off of every observability product
- Not a production data fabric, MES, or historian
- Not an employer case study (that write-up lives elsewhere and is not in this repo)

MIT licensed. Synthetic demo data only.
