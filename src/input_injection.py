"""Explainable prompt-injection detector."""

from __future__ import annotations

import re
import unicodedata

from .config import INJECTION_PATTERNS, INJECTION_THRESHOLD
from .verdicts import GuardrailVerdict


def normalize_text(text: str) -> str:
    """Normalize common obfuscation without attempting semantic decoding."""
    normalized = unicodedata.normalize("NFKC", text).lower()
    normalized = "".join(
        character
        for character in normalized
        if unicodedata.category(character) not in {"Cf", "Cc"}
        or character in "\n\t"
    )
    return " ".join(normalized.split())


def detect_injection(text: str) -> GuardrailVerdict:
    normalized = normalize_text(text)
    matches: list[dict[str, str | float]] = []
    score = 0.0
    for category, patterns in INJECTION_PATTERNS.items():
        for pattern, weight in patterns:
            if re.search(pattern, normalized):
                matches.append(
                    {"category": category, "pattern": pattern, "weight": weight}
                )
                score += weight
    score = min(score, 1.0)
    flagged = score >= INJECTION_THRESHOLD
    return GuardrailVerdict(
        flagged=flagged,
        kind="prompt_injection" if flagged else "none",
        reason=(
            "Prompt-injection pattern detected."
            if flagged
            else "No configured prompt-injection pattern detected."
        ),
        score=score,
        suggested_action="refuse" if flagged else "continue",
        details={"normalized_text": normalized, "matches": matches},
    )
