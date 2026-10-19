"""Simple claim-level groundedness check against retrieved KB entries."""

from __future__ import annotations

import re

from .config import GROUNDING_MIN_SUPPORTED_PROPORTION, GROUNDING_OVERLAP_THRESHOLD
from .knowledge_base import KnowledgeEntry
from .verdicts import GuardrailVerdict


def _words(text: str) -> set[str]:
    return {
        word
        for word in re.findall(r"[a-z0-9]+", text.lower())
        if len(word) > 2
    }


def _claims(answer: str) -> list[str]:
    return [claim.strip() for claim in re.split(r"(?<=[.!?])\s+", answer) if claim.strip()]


def check_groundedness(
    answer: str,
    cited_entries: list[KnowledgeEntry],
) -> GuardrailVerdict:
    source_text = " ".join(entry.text for entry in cited_entries)
    source_words = _words(source_text)
    claims = _claims(answer)
    supported: list[str] = []
    unsupported: list[str] = []
    claim_scores: list[float] = []
    for claim in claims:
        claim_words = _words(claim)
        overlap = len(claim_words & source_words) / max(1, len(claim_words))
        claim_numbers = set(re.findall(r"\b\d+(?:\.\d+)?\b", claim))
        source_numbers = set(re.findall(r"\b\d+(?:\.\d+)?\b", source_text))
        numbers_consistent = claim_numbers <= source_numbers
        negated = bool(
            re.search(
                r"\b(not|never|no|isn't|isnt|cannot|can't|without)\b",
                claim.lower(),
            )
        )
        source_has_negation = bool(
            re.search(
                r"\b(not|never|no|isn't|isnt|cannot|can't|without)\b",
                source_text.lower(),
            )
        )
        negation_consistent = not negated or source_has_negation
        claim_scores.append(overlap)
        if (
            overlap >= GROUNDING_OVERLAP_THRESHOLD
            and numbers_consistent
            and negation_consistent
        ):
            supported.append(claim)
        else:
            unsupported.append(claim)
    proportion = len(supported) / max(1, len(claims))
    passed = bool(supported) and proportion >= GROUNDING_MIN_SUPPORTED_PROPORTION
    return GuardrailVerdict(
        flagged=not passed,
        kind="groundedness" if not passed else "none",
        reason=(
            "Output contains unsupported claims."
            if not passed
            else "Output claims meet the configured overlap threshold."
        ),
        score=proportion,
        suggested_action="remove_unsupported_claims" if supported else "fallback",
        details={
            "claims": claims,
            "supported_claims": supported,
            "unsupported_claims": unsupported,
            "claim_scores": claim_scores,
            "supported_proportion": proportion,
            "numbers_consistent": [
                set(re.findall(r"\b\d+(?:\.\d+)?\b", claim))
                <= set(re.findall(r"\b\d+(?:\.\d+)?\b", source_text))
                for claim in claims
            ],
        },
    )
