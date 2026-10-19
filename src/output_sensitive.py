"""Output PII and known-sensitive-information detector."""

from __future__ import annotations

import re

from .config import PII_PATTERNS
from .knowledge_base import KnowledgeEntry
from .pii_guardrail import is_valid_luhn
from .verdicts import GuardrailVerdict


def detect_output_leakage(
    answer: str,
    knowledge_base_entries: list[KnowledgeEntry],
) -> GuardrailVerdict:
    findings: list[dict[str, str]] = []
    redacted = answer
    for kind in ("email", "phone", "student_id"):
        for match in re.finditer(PII_PATTERNS[kind], redacted, flags=re.IGNORECASE):
            findings.append({"type": kind, "value": match.group(0)})
        redacted = re.sub(
            PII_PATTERNS[kind],
            f"[{kind.upper()}]",
            redacted,
            flags=re.IGNORECASE,
        )
    for match in re.finditer(PII_PATTERNS["card_candidate"], answer):
        if is_valid_luhn(match.group(0)):
            findings.append({"type": "payment_card", "value": match.group(0)})

    for entry in knowledge_base_entries:
        if entry.confidential and entry.text.lower() in answer.lower():
            findings.append({"type": "confidential_kb", "value": entry.id})

    prompt_fragments = ("system instructions", "trust & safety layer", "do not modify")
    for fragment in prompt_fragments:
        if fragment in answer.lower():
            findings.append({"type": "system_prompt_fragment", "value": fragment})

    confidential = any(
        finding["type"] in {"confidential_kb", "system_prompt_fragment"}
        for finding in findings
    )
    return GuardrailVerdict(
        flagged=bool(findings),
        kind="confidential_leak" if confidential else ("pii_leak" if findings else "none"),
        reason=(
            "Known confidential information or system-prompt text leaked."
            if confidential
            else ("PII was detected and redacted." if findings else "No known sensitive information leaked.")
        ),
        score=min(1.0, len(findings) / 2),
        suggested_action="block" if confidential else ("redact" if findings else "continue"),
        details={"findings": findings, "redacted_text": redacted},
    )
