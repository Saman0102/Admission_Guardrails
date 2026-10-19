"""Strict, explainable validation for the assistant response contract."""

from __future__ import annotations

import json
import re
from typing import Any

from .config import MAX_ANSWER_LENGTH, OUTPUT_CATEGORIES, OUTPUT_STATUSES
from .verdicts import GuardrailVerdict


def parse_response(raw: str) -> tuple[dict[str, Any] | None, list[str]]:
    """Parse JSON and report fenced JSON separately from malformed JSON."""
    stripped = raw.strip()
    errors: list[str] = []
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", stripped, re.DOTALL | re.IGNORECASE)
    if fenced:
        errors.append("JSON was wrapped in a markdown code fence.")
        stripped = fenced.group(1).strip()
    try:
        value = json.loads(stripped)
    except json.JSONDecodeError as exc:
        errors.append(f"Response is not valid JSON: {exc.msg}.")
        return None, errors
    if not isinstance(value, dict):
        errors.append("Response JSON must be an object.")
        return None, errors
    return value, errors


def validate_response(raw: str, valid_source_ids: set[str]) -> GuardrailVerdict:
    value, errors = parse_response(raw)
    if value is None:
        return GuardrailVerdict(
            True, "schema", "; ".join(errors), 1.0, "regenerate", {"errors": errors}
        )

    required = {"answer", "sources", "confidence", "category", "status"}
    missing = sorted(required - value.keys())
    if missing:
        errors.append(f"Missing required field(s): {', '.join(missing)}.")
    if not isinstance(value.get("answer"), str) or not value.get("answer", "").strip():
        errors.append("Field 'answer' must be a non-empty string.")
    elif len(value["answer"]) > MAX_ANSWER_LENGTH:
        errors.append(f"Field 'answer' must be at most {MAX_ANSWER_LENGTH} characters.")
    if not isinstance(value.get("sources"), list) or not all(
        isinstance(source, str) for source in value.get("sources", [])
    ):
        errors.append("Field 'sources' must be a list of strings.")
    else:
        unknown = sorted(set(value["sources"]) - valid_source_ids)
        if unknown:
            errors.append(f"Field 'sources' contains unknown IDs: {', '.join(unknown)}.")
    confidence = value.get("confidence")
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
        errors.append("Field 'confidence' must be a number.")
    elif not 0 <= confidence <= 1:
        errors.append("Field 'confidence' must be between 0 and 1.")
    if value.get("category") not in OUTPUT_CATEGORIES:
        errors.append(f"Field 'category' must be one of: {', '.join(OUTPUT_CATEGORIES)}.")
    if value.get("status") not in OUTPUT_STATUSES:
        errors.append(f"Field 'status' must be one of: {', '.join(OUTPUT_STATUSES)}.")
    if value.get("status") == "answered" and not value.get("sources"):
        errors.append("Answered responses must contain at least one source.")

    return GuardrailVerdict(
        flagged=bool(errors),
        kind="schema" if errors else "none",
        reason="; ".join(errors) if errors else "Response matches the required schema.",
        score=1.0 if errors else 0.0,
        suggested_action="regenerate" if errors else "continue",
        details={"errors": errors, "parsed": value},
    )
