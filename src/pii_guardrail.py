"""Regex-based PII detection, masking, and payment-card validation."""

from __future__ import annotations

import re

from .config import PII_PATTERNS
from .verdicts import GuardrailVerdict


def _digits(value: str) -> str:
    return re.sub(r"\D", "", value)


def is_valid_luhn(value: str) -> bool:
    digits = _digits(value)
    if not 13 <= len(digits) <= 19:
        return False
    checksum = 0
    parity = len(digits) % 2
    for index, digit in enumerate(map(int, digits)):
        if index % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit
    return checksum % 10 == 0


def _mask(match: re.Match[str], kind: str) -> str:
    return f"[{kind.upper()}]"


def detect_and_mask(text: str) -> GuardrailVerdict:
    findings: list[dict[str, str]] = []
    masked = text
    card_found = False

    for kind in ("email", "phone", "student_id"):
        pattern = PII_PATTERNS[kind]
        matches = list(re.finditer(pattern, masked, flags=re.IGNORECASE))
        for match in matches:
            findings.append({"type": kind, "value": match.group(0)})
        masked = re.sub(
            pattern,
            lambda match, current_kind=kind: _mask(match, current_kind),
            masked,
            flags=re.IGNORECASE,
        )

    for match in re.finditer(PII_PATTERNS["card_candidate"], text):
        if is_valid_luhn(match.group(0)):
            card_found = True
            findings.append({"type": "payment_card", "value": match.group(0)})

    if card_found:
        return GuardrailVerdict(
            flagged=True,
            kind="payment_card",
            reason="A valid payment-card number was detected.",
            score=1.0,
            suggested_action="block",
            details={"findings": findings, "masked_text": masked},
        )

    return GuardrailVerdict(
        flagged=bool(findings),
        kind="pii" if findings else "none",
        reason=(
            "PII was detected and masked."
            if findings
            else "No configured PII pattern detected."
        ),
        score=min(1.0, len(findings) / 3),
        suggested_action="mask_and_continue" if findings else "continue",
        details={"findings": findings, "masked_text": masked},
    )
