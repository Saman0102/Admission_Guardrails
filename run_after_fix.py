"""Run the same authored suite after the Phase 6 groundedness improvement."""

from __future__ import annotations

import json
from pathlib import Path

from run_evaluation import CASES_PATH, RESULTS, run_case
from src.knowledge_base import KnowledgeBase


ROOT = Path(__file__).resolve().parent


def main() -> None:
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    knowledge = KnowledgeBase(ROOT / "data" / "knowledge_base.json")
    results = [run_case(case, knowledge) for case in cases]
    baseline = json.loads((RESULTS / "baseline.json").read_text(encoding="utf-8"))

    after = {
        "cases": results,
        "metrics": _metrics(results),
        "comparison": _comparison(baseline["metrics"], _metrics(results)),
    }
    (RESULTS / "after_fix.json").write_text(
        json.dumps(after, indent=2), encoding="utf-8"
    )
    lines = [
        "# After-fix evaluation",
        "",
        "Improvement: groundedness now checks numeric consistency and rejects "
        "claims with unsupported negation.",
        "",
        "## Before and after",
        "",
        "| Guardrail | Before precision | After precision | Before recall | After recall |",
        "|---|---:|---:|---:|---:|",
    ]
    for name in after["metrics"]["guardrails"]:
        before = baseline["metrics"]["guardrails"][name]
        current = after["metrics"]["guardrails"][name]
        lines.append(
            f"| {name} | {before['precision']} | {current['precision']} | "
            f"{before['recall']} | {current['recall']} |"
        )
    lines.extend(
        [
            "",
            f"- Status pass rate before: {baseline['metrics']['status_pass_rate']}",
            f"- Status pass rate after: {after['metrics']['status_pass_rate']}",
            f"- Action pass rate before: {baseline['metrics']['action_pass_rate']}",
            f"- Action pass rate after: {after['metrics']['action_pass_rate']}",
        ]
    )
    (RESULTS / "after_fix.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(after["comparison"], indent=2))


def _metrics(results):
    from run_evaluation import _metric, _precision_recall

    metrics = {"total_cases": len(results), "guardrails": {}}
    for name in ("injection", "pii", "sensitive_topic", "groundedness", "output_leakage"):
        matrix = {"tp": 0, "fp": 0, "tn": 0, "fn": 0}
        for result in results:
            current = _metric(
                result["actual_flags"][name],
                result["expected_flags"].get(name, False),
            )
            for key in matrix:
                matrix[key] += current[key]
        metrics["guardrails"][name] = {**matrix, **_precision_recall(matrix)}
    metrics["status_pass_rate"] = sum(r["status_passed"] for r in results) / len(results)
    metrics["action_pass_rate"] = sum(r["action_passed"] for r in results) / len(results)
    return metrics


def _comparison(before, after):
    return {
        name: {
            "precision_delta": after["guardrails"][name]["precision"]
            - before["guardrails"][name]["precision"],
            "recall_delta": (
                None
                if after["guardrails"][name]["recall"] is None
                or before["guardrails"][name]["recall"] is None
                else after["guardrails"][name]["recall"]
                - before["guardrails"][name]["recall"]
            ),
        }
        for name in after["guardrails"]
    }


if __name__ == "__main__":
    main()
