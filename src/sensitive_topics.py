"""Priority-based sensitive-topic classifier."""

from __future__ import annotations

from .config import SENSITIVE_TOPIC_PRIORITY, SENSITIVE_TOPIC_RULES
from .input_injection import normalize_text
from .verdicts import GuardrailVerdict


def classify_sensitive_topic(text: str) -> GuardrailVerdict:
    normalized = normalize_text(text)
    for category in SENSITIVE_TOPIC_PRIORITY:
        matches = [
            phrase
            for phrase in SENSITIVE_TOPIC_RULES[category]
            if phrase in normalized
        ]
        if matches:
            actions = {
                "self_harm": "supportive_response",
                "medical": "refuse_and_redirect",
                "legal_visa": "answer_with_disclaimer",
                "financial_hardship": "answer_with_financial_aid_pointer",
            }
            return GuardrailVerdict(
                flagged=True,
                kind=category,
                reason=f"Sensitive topic detected: {category}.",
                score=1.0,
                suggested_action=actions[category],
                details={"matches": matches},
            )
    return GuardrailVerdict(
        flagged=False,
        kind="none",
        reason="No configured sensitive topic detected.",
        score=0.0,
        suggested_action="continue",
    )
