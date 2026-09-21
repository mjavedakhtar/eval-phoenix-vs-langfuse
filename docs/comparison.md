# Phoenix vs Langfuse — public comparison

This is the write-up for GitHub (and a CV link). It uses only the synthetic plant in this repo. Employer-internal decision records are not published here.

**Setup:** same LangGraph agent, same five golden questions, local Ollama, both platforms self-hosted.

## The hook

A fluent answer can still be wrong in an agent. The flight recorder has to show *which tool fired*, *what it returned*, and *whether the model cited that* — including the case where the asset does not exist and the agent must refuse.

Two traces decide most of the product question:

1. **Line 3 scrap spike** — multi-hop (graph → time series → alarms)
2. **Line 9** — missing asset, must not invent a factory line

## Results

_Fill after the lab. Paste screenshots of those two traces from each UI._

| Case | Phoenix task success | Langfuse task success | Notes |
| --- | --- | --- | --- |
| scrap-line-3 | | | |
| upstream-press-12 | | | |
| oven-a-work-order | | | |
| missing-line-9 | | | |
| oven-a-alarms | | | |

| Dimension (1–5) | Phoenix | Langfuse | What I actually saw |
| --- | --- | --- | --- |
| Trace fidelity | | | |
| Offline evals / experiments | | | |
| Human review loop | | | |
| Self-host friction | | | |
| Time-to-first-trace | | | |

## Take

_One paragraph after scores. Example shape, not a conclusion yet:_ Phoenix wins if you want the lightest OpenTelemetry-native loop. Langfuse wins if you want prompts, datasets, and annotation in one self-hosted product and will run Compose. Dual-export is a hedge, not a strategy.

## CV blurb

Compared Arize Phoenix and Langfuse as self-hosted observability for a tool-using diagnostic agent (knowledge graph, metrics, alarms, work orders). Built a synthetic golden set and code evals for groundedness, tool trajectory, and hallucination, including a must-refuse missing-asset case.
