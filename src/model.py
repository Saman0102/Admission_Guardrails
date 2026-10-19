"""Model interface, deterministic mock, and Google Gemini implementation."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any

from .knowledge_base import KnowledgeEntry
from .settings import gemini_api_key, gemini_model


class Model(ABC):
    """Provider-neutral model contract."""

    @abstractmethod
    def generate(
        self,
        user_input: str,
        context: list[KnowledgeEntry],
        case_id: str | None = None,
        retry_feedback: str | None = None,
    ) -> str:
        """Generate a JSON string from cleaned input and retrieved context."""


class MockModel(Model):
    """Deterministic model with optional case-specific scripted outputs."""

    def __init__(self, scripted_outputs: dict[str, str] | None = None) -> None:
        self.scripted_outputs = dict(scripted_outputs or {})
        self.calls = 0
        self.history: list[dict[str, Any]] = []

    def generate(
        self,
        user_input: str,
        context: list[KnowledgeEntry],
        case_id: str | None = None,
        retry_feedback: str | None = None,
    ) -> str:
        self.calls += 1
        self.history.append(
            {
                "user_input": user_input,
                "case_id": case_id,
                "retry_feedback": retry_feedback,
            }
        )
        if case_id in self.scripted_outputs and not retry_feedback:
            return self.scripted_outputs[case_id]
        return self._safe_response(user_input, context)

    @staticmethod
    def _safe_response(
        user_input: str,
        context: list[KnowledgeEntry],
    ) -> str:
        del user_input
        if not context:
            return json.dumps(
                {
                    "answer": "I could not find that information in the admissions FAQ.",
                    "sources": [],
                    "confidence": 0.2,
                    "category": "out_of_scope",
                    "status": "fallback",
                }
            )

        entry = context[0]
        return json.dumps(
            {
                "answer": entry.text,
                "sources": [entry.id],
                "confidence": 0.85,
                "category": entry.category,
                "status": "answered",
            }
        )


class GeminiModel(Model):
    """Google AI Studio Gemini provider using the official Google Gen AI SDK."""

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str | None = None,
    ) -> None:
        self.api_key = api_key or gemini_api_key()
        self.model_name = model_name or gemini_model()
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY is required when the Gemini provider is selected."
            )
        try:
            from google import genai
        except ImportError as exc:
            raise RuntimeError(
                "The Gemini provider requires google-genai. "
                "Install it with: python -m pip install -r requirements.txt"
            ) from exc

        self.client = genai.Client(api_key=self.api_key)
        self.calls = 0

    def generate(
        self,
        user_input: str,
        context: list[KnowledgeEntry],
        case_id: str | None = None,
        retry_feedback: str | None = None,
    ) -> str:
        del case_id
        self.calls += 1
        context_text = "\n\n".join(
            f"[{entry.id}] {entry.title}: {entry.text}" for entry in context
        )
        feedback = (
            f"\nCorrect the previous response using this validation feedback: "
            f"{retry_feedback}\n"
            if retry_feedback
            else ""
        )
        prompt = f"""You are an admissions FAQ assistant for a fictional university.
Answer only from the public reference context below. Do not invent facts.
Return only valid JSON with exactly these fields:
{{
  "answer": "string",
  "sources": ["public KB IDs used"],
  "confidence": 0.0,
  "category": "deadlines|fees|documents|scholarships|international|general|out_of_scope",
  "status": "answered|refused|fallback"
}}
Use an empty sources list and status "fallback" when the context does not
support an answer. Confidence must be a number between 0 and 1.

Reference context:
{context_text or "[No matching public context]"}

Applicant question:
{user_input}
{feedback}"""
        try:
            from google.genai import types

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.0,
                    response_mime_type="application/json",
                ),
            )
        except Exception as exc:
            raise RuntimeError(
                f"Gemini request failed for model {self.model_name}: {exc}"
            ) from exc

        text = getattr(response, "text", None)
        if not text:
            raise RuntimeError("Gemini returned an empty response.")
        return text.strip()
