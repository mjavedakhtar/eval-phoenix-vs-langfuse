"""Run the golden set with traces going to a local Phoenix instance.

Start Phoenix first:
    uvx arize-phoenix serve
Then:
    python run_phoenix.py
UI: http://localhost:6006
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from phoenix_endpoint import traces_endpoint
from phoenix.otel import register
from openinference.instrumentation.langchain import LangChainInstrumentor

from agent import load_golden_set, run_question
from evals import score_run, summarize


def main() -> None:
    register(
        project_name=os.getenv("PHOENIX_PROJECT_NAME", "data-fabric-agent"),
        endpoint=traces_endpoint(),
        protocol="http/protobuf",
        auto_instrument=False,
    )
    LangChainInstrumentor().instrument()

    rows = []
    for case in load_golden_set():
        print(f"\n=== {case['id']} ===")
        result = run_question(case["question"])
        scored = score_run(case, result)
        rows.append(scored)
        print(json.dumps({k: scored[k] for k in ("task_success", "tools_called")}, indent=2))

    summary = summarize(rows)
    out = Path(__file__).parent / "results" / "phoenix_eval.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({"summary": summary, "rows": rows}, indent=2))
    print("\nPhoenix summary:", json.dumps(summary, indent=2))
    print(f"Wrote {out}")
    print("Open http://localhost:6006 and inspect nested tool / LLM spans.")


if __name__ == "__main__":
    main()
