"""Ordered output guardrails with one corrective retry signal."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .groundedness import check_groundedness
from .knowledge_base import KnowledgeBase, KnowledgeEntry
from .output_schema import validate_response
from .output_sensitive import detect_output_leakage


@dataclass
class OutputDecision:
    allowed: bool
    final_text: str
    action: str
    block_reason: str | None
    schema: Any
    groundedness: Any
    sensitive_information: Any
    retry_feedback: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "final_text": self.final_text,
            "action": self.action,
            "block_reason": self.block_reason,
            "schema": self.schema.to_dict(),
            "groundedness": self.groundedness.to_dict(),
            "sensitive_information": self.sensitive_information.to_dict(),
            "retry_feedback": self.retry_feedback,
        }


def safe_fallback(reason: str) -> str:
    import json

    return json.dumps(
        {
            "answer": "I could not safely verify an answer from the admissions FAQ.",
            "sources": [],
            "confidence": 0.0,
            "category": "out_of_scope",
            "status": "fallback",
            "reason": reason,
        }
    )


def evaluate_output(
    raw_text: str,
    knowledge_base: KnowledgeBase,
    retrieved_entries: list[KnowledgeEntry],
) -> OutputDecision:
    valid_source_ids = {
        entry.id for entry in knowledge_base.public_entries()
    }
    schema = validate_response(raw_text, valid_source_ids)
    if schema.flagged:
        return OutputDecision(
            False,
            safe_fallback(schema.reason),
            "regenerate",
            schema.reason,
            schema,
            _empty_groundedness(),
            _empty_sensitive(),
            schema.reason,
        )

    parsed = schema.details["parsed"]
    cited_entries = [
        knowledge_base.get(source_id)
        for source_id in parsed["sources"]
        if source_id in {entry.id for entry in retrieved_entries}
    ]
    groundedness = check_groundedness(parsed["answer"], cited_entries)
    if groundedness.flagged:
        supported = groundedness.details["supported_claims"]
        if supported and groundedness.details["supported_proportion"] >= 0.60:
            parsed["answer"] = " ".join(supported)
        else:
            return OutputDecision(
                False,
                safe_fallback(groundedness.reason),
                "fallback",
                groundedness.reason,
                schema,
                groundedness,
                _empty_sensitive(),
            )

    sensitive = detect_output_leakage(
        parsed["answer"], knowledge_base.entries
    )
    if sensitive.flagged and sensitive.suggested_action == "block":
        return OutputDecision(
            False,
            safe_fallback(sensitive.reason),
            "fallback",
            sensitive.reason,
            schema,
            groundedness,
            sensitive,
        )
    if sensitive.flagged:
        parsed["answer"] = sensitive.details["redacted_text"]
    import json

    return OutputDecision(
        True,
        json.dumps(parsed),
        "redact" if sensitive.flagged else "continue",
        sensitive.reason if sensitive.flagged else None,
        schema,
        groundedness,
        sensitive,
    )


def _empty_groundedness():
    from .verdicts import GuardrailVerdict

    return GuardrailVerdict(False, "not_run", "Not run.", 0.0, "skip")


def _empty_sensitive():
    from .verdicts import GuardrailVerdict

    return GuardrailVerdict(False, "not_run", "Not run.", 0.0, "skip")
