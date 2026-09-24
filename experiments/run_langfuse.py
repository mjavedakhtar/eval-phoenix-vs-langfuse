"""Run the golden set with traces going to a local Langfuse instance.

Start Langfuse first:
    ./scripts/start-langfuse.sh
Then sign up at http://localhost:3000, create a project, copy the
public/secret keys into .env (LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY).

    python run_langfuse.py
UI: http://localhost:3000
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

os.environ.setdefault("LANGFUSE_BASE_URL", "http://localhost:3000")
os.environ.setdefault("LANGFUSE_HOST", os.environ["LANGFUSE_BASE_URL"])

from langfuse import Langfuse
from langfuse.langchain import CallbackHandler

from agent import load_golden_set, run_question
from evals import score_run, summarize


def main() -> None:
    if not os.getenv("LANGFUSE_PUBLIC_KEY") or not os.getenv("LANGFUSE_SECRET_KEY"):
        raise RuntimeError(
            "Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY in .env. "
            "Start Langfuse with ./scripts/start-langfuse.sh, open "
            "http://localhost:3000, create a project, and copy the keys."
        )

    langfuse = Langfuse(timeout=120)
    if not langfuse.auth_check():
        raise RuntimeError(
            "Langfuse auth failed. Check LANGFUSE_BASE_URL and the project keys."
        )

    handler = CallbackHandler()
    rows = []
    for case in load_golden_set():
        print(f"\n=== {case['id']} ===")
        result = run_question(case["question"], callbacks=[handler])
        scored = score_run(case, result)
        rows.append(scored)
        print(json.dumps({k: scored[k] for k in ("task_success", "tools_called")}, indent=2))

    langfuse.flush()

    summary = summarize(rows)
    out = Path(__file__).parent / "results" / "langfuse_eval.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({"summary": summary, "rows": rows}, indent=2))
    print("\nLangfuse summary:", json.dumps(summary, indent=2))
    print(f"Wrote {out}")
    print("Open http://localhost:3000 and inspect nested tool / LLM spans.")


if __name__ == "__main__":
    main()
