"""Measure a stricter groundedness threshold without changing config.py."""

from __future__ import annotations

import json
from pathlib import Path

import src.groundedness as groundedness
from run_after_fix import _metrics, run_case
from src.knowledge_base import KnowledgeBase


ROOT = Path(__file__).resolve().parent


def main() -> None:
    cases = json.loads((ROOT / "data" / "test_cases.json").read_text(encoding="utf-8"))
    knowledge = KnowledgeBase(ROOT / "data" / "knowledge_base.json")
    original = groundedness.GROUNDING_OVERLAP_THRESHOLD
    default_results = [run_case(case, knowledge) for case in cases]
    groundedness.GROUNDING_OVERLAP_THRESHOLD = 0.80
    strict_results = [run_case(case, knowledge) for case in cases]
    groundedness.GROUNDING_OVERLAP_THRESHOLD = original

    default = _metrics(default_results)
    strict = _metrics(strict_results)
    changed = [
        {
            "id": before["id"],
            "default_status": before["actual_status"],
            "strict_status": after["actual_status"],
        }
        for before, after in zip(default_results, strict_results)
        if before["actual_status"] != after["actual_status"]
    ]
    report = {
        "default_threshold": original,
        "strict_threshold": 0.80,
        "default_metrics": default,
        "strict_metrics": strict,
        "status_changes": changed,
        "additional_status_failures": sum(
            not result["status_passed"] for result in strict_results
        ) - sum(not result["status_passed"] for result in default_results),
    }
    (ROOT / "results" / "tradeoff.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
