"""Shared response schema used by the model and later guardrails."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class AssistantResponse:
    """The response shape expected from every pipeline stage."""

    answer: str
    sources: list[str]
    confidence: float
    category: str
    status: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
