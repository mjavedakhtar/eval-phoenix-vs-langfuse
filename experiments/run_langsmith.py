"""Optional: LangSmith cloud. Not part of the Phoenix vs Langfuse lab.

Kept so we can footnote cloud-only tracing if needed.
Requires LANGSMITH_API_KEY. UI: https://smith.langchain.com
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from langsmith import Client

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

os.environ.setdefault("LANGSMITH_TRACING", "true")
os.environ.setdefault("LANGSMITH_PROJECT", "data-fabric-agent")

from agent import load_golden_set, run_question
from evals import score_run, summarize


def main() -> None:
    if not os.getenv("LANGSMITH_API_KEY"):
        raise RuntimeError("Set LANGSMITH_API_KEY in .env")

    client = Client()
    dataset_name = "data-fabric-golden-v1"
    existing = {d.name for d in client.list_datasets()}
    if dataset_name not in existing:
        dataset = client.create_dataset(
            dataset_name=dataset_name,
            description="Simulated industrial data-fabric diagnostic questions.",
        )
        for case in load_golden_set():
            client.create_example(
                inputs={"question": case["question"]},
                outputs={"task_success": case["task_success"]},
                dataset_id=dataset.id,
                metadata={"id": case["id"], "expected_tools": case["expected_tools"]},
            )
        print(f"Created LangSmith dataset {dataset_name}")
    else:
        print(f"Using existing LangSmith dataset {dataset_name}")

    rows = []
    for case in load_golden_set():
        print(f"\n=== {case['id']} ===")
        result = run_question(case["question"])
        scored = score_run(case, result)
        rows.append(scored)
        print(json.dumps({k: scored[k] for k in ("task_success", "tools_called")}, indent=2))

    summary = summarize(rows)
    out = Path(__file__).parent / "results" / "langsmith_eval.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({"summary": summary, "rows": rows}, indent=2))
    print("\nLangSmith summary:", json.dumps(summary, indent=2))
    print(f"Wrote {out}")
    print("Open the data-fabric-agent project in LangSmith and inspect trajectories.")


if __name__ == "__main__":
    main()
