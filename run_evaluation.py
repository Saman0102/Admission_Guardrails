"""Run the authored test suite and calculate exact baseline metrics."""

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from src.input_pipeline import evaluate_input
from src.knowledge_base import KnowledgeBase
from src.model import MockModel
from src.orchestrator import Orchestrator
from src.output_sensitive import detect_output_leakage
from src.output_schema import validate_response
from src.groundedness import check_groundedness


ROOT = Path(__file__).resolve().parent
CASES_PATH = ROOT / "data" / "test_cases.json"
RESULTS = ROOT / "results"


def _metric(actual: bool, expected: bool) -> dict[str, int]:
    return {
        "tp": int(actual and expected),
        "fp": int(actual and not expected),
        "tn": int(not actual and not expected),
        "fn": int(not actual and expected),
    }


def _precision_recall(matrix: dict[str, int]) -> dict[str, float | None]:
    precision_denominator = matrix["tp"] + matrix["fp"]
    recall_denominator = matrix["tp"] + matrix["fn"]
    return {
        "precision": (
            matrix["tp"] / precision_denominator
            if precision_denominator else None
        ),
        "recall": (
            matrix["tp"] / recall_denominator
            if recall_denominator else None
        ),
    }


def run_case(
    case: dict[str, Any],
    knowledge: KnowledgeBase,
) -> dict[str, Any]:
    model = MockModel(
        {case["id"]: case["scripted_model_output"]}
        if case.get("scripted_model_output")
        else {}
    )
    orchestrator = Orchestrator(knowledge, model)
    result = orchestrator.run(case["input"], case_id=case["id"])
    input_decision = evaluate_input(case["input"])
    context = knowledge.retrieve(input_decision.cleaned_text)
    model_output = (
        case.get("scripted_model_output")
        if case.get("scripted_model_output")
        else result["model_output"]
    )
    schema = validate_response(
        model_output,
        {entry.id for entry in knowledge.public_entries()},
    ) if model_output else None
    grounded = None
    leakage = None
    if schema and not schema.flagged:
        parsed = schema.details["parsed"]
        cited = [knowledge.get(source) for source in parsed["sources"]]
        grounded = check_groundedness(parsed["answer"], cited)
        leakage = detect_output_leakage(parsed["answer"], knowledge.entries)

    final_payload = json.loads(result["final_response"])
    actual_action = result["actions"][-1]
    if input_decision.action in {"answer_with_disclaimer", "answer_with_financial_aid_pointer"}:
        actual_action = input_decision.action

    actual_flags = {
        "injection": input_decision.injection.flagged,
        "pii": input_decision.pii.flagged,
        "sensitive_topic": input_decision.sensitive_topic.flagged,
        "groundedness": bool(grounded and grounded.flagged),
        "output_leakage": bool(leakage and leakage.flagged),
    }
    expected_flags = {
        key: bool(value)
        for key, value in case["ground_truth"].items()
    }
    expected_flags.setdefault("groundedness", case["group"] == "groundedness")
    expected_flags.setdefault("output_leakage", case["group"] == "leakage")
    status_passed = final_payload.get("status") == case["expected_status"]
    action_passed = actual_action == case["expected_action"]
    return {
        "id": case["id"],
        "group": case["group"],
        "input": case["input"],
        "expected_status": case["expected_status"],
        "actual_status": final_payload.get("status"),
        "expected_action": case["expected_action"],
        "actual_action": actual_action,
        "status_passed": status_passed,
        "action_passed": action_passed,
        "actual_flags": actual_flags,
        "expected_flags": expected_flags,
        "schema_flagged": bool(schema and schema.flagged),
        "groundedness_flagged": actual_flags["groundedness"],
        "output_leakage_flagged": actual_flags["output_leakage"],
        "model_calls": model.calls,
        "final_response": result["final_response"],
    }


def main() -> int:
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    knowledge = KnowledgeBase(ROOT / "data" / "knowledge_base.json")
    results = [run_case(case, knowledge) for case in cases]

    metrics: dict[str, Any] = {"total_cases": len(results), "guardrails": {}}
    for name in ("injection", "pii", "sensitive_topic", "groundedness", "output_leakage"):
        matrix = {"tp": 0, "fp": 0, "tn": 0, "fn": 0}
        for result in results:
            current = _metric(
                result["actual_flags"][name],
                result["expected_flags"].get(name, False),
            )
            for key in matrix:
                matrix[key] += current[key]
        metrics["guardrails"][name] = {
            **matrix,
            **_precision_recall(matrix),
        }
    schema_cases = [r for r in results if r["group"] == "schema"]
    metrics["schema"] = {
        "cases": len(schema_cases),
        "caught": sum(r["schema_flagged"] for r in schema_cases),
        "final_statuses": {
            status: sum(r["actual_status"] == status for r in schema_cases)
            for status in ("answered", "refused", "fallback")
        },
    }
    metrics["status_pass_rate"] = sum(r["status_passed"] for r in results) / len(results)
    metrics["action_pass_rate"] = sum(r["action_passed"] for r in results) / len(results)
    metrics["false_positives_negatives"] = [
        {
            "id": result["id"],
            "guardrail": name,
            "kind": "false_positive" if result["actual_flags"][name] else "false_negative",
        }
        for result in results
        for name in result["actual_flags"]
        if result["actual_flags"][name] != result["expected_flags"].get(name, False)
    ]

    RESULTS.mkdir(exist_ok=True)
    output_name = "baseline" if not (RESULTS / "baseline.json").exists() else "latest"
    (RESULTS / f"{output_name}.json").write_text(
        json.dumps({"cases": results, "metrics": metrics}, indent=2),
        encoding="utf-8",
    )
    with (RESULTS / f"{output_name}.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = ["id", "group", "expected_status", "actual_status", "expected_action", "actual_action",
                  "status_passed", "action_passed", "actual_flags", "expected_flags"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for result in results:
            writer.writerow({field: result[field] for field in fields})
    lines = [
        "# Baseline evaluation results",
        "",
        f"- Cases: {metrics['total_cases']}",
        f"- Status pass rate: {metrics['status_pass_rate']:.6f}",
        f"- Action pass rate: {metrics['action_pass_rate']:.6f}",
        "",
        "| Guardrail | TP | FP | TN | FN | Precision | Recall |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for name, value in metrics["guardrails"].items():
        lines.append(
            f"| {name} | {value['tp']} | {value['fp']} | {value['tn']} | {value['fn']} | "
            f"{value['precision']} | {value['recall']} |"
        )
    lines.extend(["", "## False positives and false negatives", ""])
    lines.extend(
        f"- `{item['id']}` — {item['guardrail']} — {item['kind']}"
        for item in metrics["false_positives_negatives"]
    )
    (RESULTS / f"{output_name}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
