"""Ordered input guardrail pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .config import MAX_INPUT_LENGTH
from .input_injection import detect_injection
from .pii_guardrail import detect_and_mask
from .sensitive_topics import classify_sensitive_topic
from .verdicts import GuardrailVerdict


@dataclass
class InputDecision:
    allowed: bool
    cleaned_text: str
    action: str
    block_reason: str | None
    injection: GuardrailVerdict
    pii: GuardrailVerdict
    sensitive_topic: GuardrailVerdict

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "cleaned_text": self.cleaned_text,
            "action": self.action,
            "block_reason": self.block_reason,
            "injection": self.injection.to_dict(),
            "pii": self.pii.to_dict(),
            "sensitive_topic": self.sensitive_topic.to_dict(),
        }


def evaluate_input(text: str) -> InputDecision:
    """Apply injection -> PII -> sensitive-topic rules in order."""
    empty_verdict = GuardrailVerdict(
        flagged=False,
        kind="not_run",
        reason="Detector was not run because an earlier guardrail blocked input.",
        score=0.0,
        suggested_action="skip",
    )
    empty = text.strip() == ""
    too_long = len(text) > MAX_INPUT_LENGTH
    if empty or too_long:
        validation = GuardrailVerdict(
            flagged=True,
            kind="invalid_input",
            reason="Input is empty or exceeds the configured length limit.",
            score=1.0,
            suggested_action="refuse",
        )
        return InputDecision(
            False,
            text[:MAX_INPUT_LENGTH],
            "refuse",
            validation.reason,
            validation,
            empty_verdict,
            empty_verdict,
        )

    injection = detect_injection(text)
    if injection.flagged:
        return InputDecision(
            False, text, "refuse", injection.reason, injection, empty_verdict, empty_verdict
        )

    pii = detect_and_mask(text)
    if pii.kind == "payment_card":
        return InputDecision(False, text, "block", pii.reason, injection, pii, empty_verdict)

    cleaned_text = str(pii.details.get("masked_text", text))
    topic = classify_sensitive_topic(cleaned_text)
    if topic.flagged and topic.kind in {"self_harm", "medical"}:
        return InputDecision(
            False,
            cleaned_text,
            topic.suggested_action,
            topic.reason,
            injection,
            pii,
            topic,
        )

    return InputDecision(
        True,
        cleaned_text,
        topic.suggested_action if topic.flagged else (
            "mask_and_continue" if pii.flagged else "continue"
        ),
        None,
        injection,
        pii,
        topic,
    )
