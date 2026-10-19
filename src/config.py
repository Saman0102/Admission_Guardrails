"""Single source of truth for assignment thresholds and detection rules."""

from __future__ import annotations

from dataclasses import dataclass


OUTPUT_CATEGORIES = (
    "deadlines",
    "fees",
    "documents",
    "scholarships",
    "international",
    "general",
    "out_of_scope",
)
OUTPUT_STATUSES = ("answered", "refused", "fallback")

MAX_INPUT_LENGTH = 2_000
MAX_ANSWER_LENGTH = 800
MAX_SCHEMA_RETRIES = 1

INJECTION_THRESHOLD = 0.70
GROUNDING_OVERLAP_THRESHOLD = 0.50
GROUNDING_MIN_SUPPORTED_PROPORTION = 0.60

INJECTION_PATTERNS: dict[str, tuple[tuple[str, float], ...]] = {
    "instruction_override": (
        (r"\bignore (all |your |the )?(previous|prior|above) instructions?\b", 0.90),
        (r"\bdisregard (all |your |the )?(previous|prior|above) instructions?\b", 0.90),
        (r"\bnew (system )?instructions?\s*:", 0.80),
    ),
    "prompt_extraction": (
        (r"\breveal (your )?(system )?prompt\b", 0.95),
        (r"\bshow me (your )?instructions?\b", 0.85),
        (r"\bprint (the )?system prompt\b", 0.95),
    ),
    "persona_jailbreak": (
        (r"\bpretend (you are|to be) (a )?(different|unrestricted|evil)\b", 0.85),
        (r"\byou are now (unrestricted|uncensored|without rules)\b", 0.90),
        (r"\bdo anything now\b", 0.85),
    ),
    "restriction_bypass": (
        (r"\bbypass (the )?(safety|permission|approval) (check|flow|system)\b", 0.95),
        (r"\bturn off (your )?safety filters?\b", 0.90),
    ),
}

PII_PATTERNS = {
    "email": r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
    "phone": r"(?<!\d)(?:\+?\d[\d .()-]{8,}\d)(?!\d)",
    "student_id": r"\b[A-Z]{2}\d{7}\b",
    "card_candidate": r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)",
}

SENSITIVE_TOPIC_RULES: dict[str, tuple[str, ...]] = {
    "self_harm": (
        "suicide",
        "self harm",
        "self-harm",
        "kill myself",
        "overdose",
    ),
    "medical": (
        "diagnosis",
        "medical advice",
        "symptoms",
        "prescription",
        "medicine",
    ),
    "legal_visa": (
        "visa advice",
        "immigration lawyer",
        "legal advice",
        "student visa",
        "immigration status",
    ),
    "financial_hardship": (
        "cannot afford",
        "can't afford",
        "financial hardship",
        "pay my tuition",
        "emergency funding",
    ),
}

SENSITIVE_TOPIC_PRIORITY = (
    "self_harm",
    "medical",
    "legal_visa",
    "financial_hardship",
)


@dataclass(frozen=True)
class OutputSchemaConfig:
    """Names and bounds used by the output schema validator."""

    required_fields: tuple[str, ...] = (
        "answer",
        "sources",
        "confidence",
        "category",
        "status",
    )
    max_answer_length: int = MAX_ANSWER_LENGTH
    categories: tuple[str, ...] = OUTPUT_CATEGORIES
    statuses: tuple[str, ...] = OUTPUT_STATUSES


OUTPUT_SCHEMA = OutputSchemaConfig()
