"""Common structured verdicts returned by guardrails."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GuardrailVerdict:
    flagged: bool
    kind: str
    reason: str
    score: float
    suggested_action: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "flagged": self.flagged,
            "kind": self.kind,
            "reason": self.reason,
            "score": self.score,
            "suggested_action": self.suggested_action,
            "details": self.details,
        }
