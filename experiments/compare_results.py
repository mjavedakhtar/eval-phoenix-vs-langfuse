"""Print a side-by-side summary once both lab runs have produced JSON."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parent / "results"


def load(name: str) -> dict:
    path = ROOT / name
    if not path.exists():
        return {"summary": {}, "rows": [], "missing": True}
    return json.loads(path.read_text())


def task(rows: list, case_id: str) -> str:
    row = next((r for r in rows if r["id"] == case_id), {})
    if not row:
        return "-"
    return str(row.get("task_success"))


def main() -> None:
    phoenix = load("phoenix_eval.json")
    langfuse = load("langfuse_eval.json")
    print("Phoenix  ", phoenix.get("summary") or "not run yet")
    print("Langfuse ", langfuse.get("summary") or "not run yet")
    ids = sorted(
        {row["id"] for row in phoenix.get("rows", [])}
        | {row["id"] for row in langfuse.get("rows", [])}
    )
    print(f"{'case':24} {'phoenix':10} {'langfuse':10}")
    for case_id in ids:
        print(
            f"{case_id:24} {task(phoenix.get('rows', []), case_id):10} "
            f"{task(langfuse.get('rows', []), case_id):10}"
        )


if __name__ == "__main__":
    main()
