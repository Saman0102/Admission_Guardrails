"""Recreate the pre-Phase-6 baseline without changing current production code."""

from __future__ import annotations

import re

import run_evaluation
import src.output_pipeline as output_pipeline
from src.config import GROUNDING_MIN_SUPPORTED_PROPORTION, GROUNDING_OVERLAP_THRESHOLD
from src.verdicts import GuardrailVerdict


def legacy_groundedness(answer, cited_entries):
    source_text = " ".join(entry.text for entry in cited_entries)
    source_words = _words(source_text)
    claims = [
        claim.strip()
        for claim in re.split(r"(?<=[.!?])\s+", answer)
        if claim.strip()
    ]
    supported = []
    unsupported = []
    scores = []
    for claim in claims:
        claim_words = _words(claim)
        overlap = len(claim_words & source_words) / max(1, len(claim_words))
        scores.append(overlap)
        if overlap >= GROUNDING_OVERLAP_THRESHOLD:
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
            "claim_scores": scores,
            "supported_proportion": proportion,
        },
    )


def _words(text):
    return {
        word
        for word in re.findall(r"[a-z0-9]+", text.lower())
        if len(word) > 2
    }


if __name__ == "__main__":
    run_evaluation.check_groundedness = legacy_groundedness
    output_pipeline.check_groundedness = legacy_groundedness
    # Remove the current artifact so the evaluator writes baseline.*.
    import pathlib

    baseline = pathlib.Path("results/baseline.json")
    if baseline.exists():
        baseline.unlink()
    run_evaluation.main()
