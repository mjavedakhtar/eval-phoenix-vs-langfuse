"""Deterministic evals that work the same for Phoenix and LangSmith runs.

LLM-as-judge can be added later. Start with code checks so the first lab
results are cheap, repeatable, and not themselves a model-quality debate.
"""

from __future__ import annotations

from typing import Any


def score_run(case: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    answer = (result.get("answer") or "").lower()
    tools = result.get("tools_called") or []
    expected = case.get("expected_tools") or []

    trajectory_hit = all(
        any(exp.lower() in str(tool).lower() for tool in tools) for exp in expected
    )
    cited = [
        token
        for token in case.get("must_cite") or []
        if token.lower() in answer
    ]
    invented = [
        token
        for token in case.get("must_not_invent") or []
        if token.lower() in answer
    ]
    grounded = len(cited) == len(case.get("must_cite") or [])
    hallucination = len(invented) > 0
    task_success = grounded and not hallucination and trajectory_hit

    return {
        "id": case["id"],
        "trajectory_ok": trajectory_hit,
        "grounded": grounded,
        "hallucination": hallucination,
        "task_success": task_success,
        "cited": cited,
        "invented": invented,
        "tools_called": tools,
        "answer": result.get("answer"),
    }


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    n = max(len(rows), 1)
    return {
        "n": len(rows),
        "task_success_rate": round(sum(r["task_success"] for r in rows) / n, 3),
        "grounded_rate": round(sum(r["grounded"] for r in rows) / n, 3),
        "hallucination_rate": round(sum(r["hallucination"] for r in rows) / n, 3),
        "trajectory_ok_rate": round(sum(r["trajectory_ok"] for r in rows) / n, 3),
    }
