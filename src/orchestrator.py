"""Phase 2 end-to-end flow before guardrails are added."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .knowledge_base import KnowledgeBase
from .input_pipeline import evaluate_input
from .logger import DecisionLogger
from .model import Model
from .output_pipeline import evaluate_output, safe_fallback
from .settings import model_provider


class Orchestrator:
    """Connect retrieval, model generation, and decision logging."""

    def __init__(
        self,
        knowledge_base: KnowledgeBase,
        model: Model,
        logger: DecisionLogger | None = None,
    ) -> None:
        self.knowledge_base = knowledge_base
        self.model = model
        self.logger = logger

    def run(self, user_input: str, case_id: str | None = None) -> dict[str, Any]:
        input_decision = evaluate_input(user_input)
        model_output = ""
        context = []
        output_decision = None
        if input_decision.allowed:
            context = self.knowledge_base.retrieve(input_decision.cleaned_text)
            model_output = self.model.generate(
                input_decision.cleaned_text, context, case_id=case_id
            )
            output_decision = evaluate_output(
                model_output, self.knowledge_base, context
            )
            if output_decision.action == "regenerate" and output_decision.retry_feedback:
                model_output = self.model.generate(
                    input_decision.cleaned_text,
                    context,
                    case_id=case_id,
                    retry_feedback=output_decision.retry_feedback,
                )
                output_decision = evaluate_output(
                    model_output, self.knowledge_base, context
                )
        response: dict[str, Any] = {
            "input": user_input,
            "retrieved_context": [entry.id for entry in context],
            "model_output": model_output,
            "final_response": model_output,
            "guardrails": {"input": input_decision.to_dict()},
            "actions": [input_decision.action],
        }
        if not input_decision.allowed:
            import json

            response["final_response"] = json.dumps(
                {
                    "answer": input_decision.block_reason or "Request refused.",
                    "sources": [],
                    "confidence": 0.0,
                    "category": "out_of_scope",
                    "status": "refused",
                }
            )
        elif output_decision:
            response["final_response"] = output_decision.final_text
            response["guardrails"]["output"] = output_decision.to_dict()
            response["actions"].append(output_decision.action)
        if self.logger:
            self.logger.log(response)
        return response


def build_demo_orchestrator(
    project_root: str | Path,
    log_path: str | Path | None = None,
    provider: str | None = None,
) -> Orchestrator:
    root = Path(project_root)
    knowledge_base = KnowledgeBase(root / "data" / "knowledge_base.json")
    logger = DecisionLogger(log_path) if log_path else None
    from .model import GeminiModel, MockModel

    selected_provider = provider or model_provider()
    if selected_provider == "mock":
        model = MockModel()
    elif selected_provider == "gemini":
        model = GeminiModel()
    else:
        raise ValueError(
            f"Unknown model provider '{selected_provider}'. "
            "Use 'mock' or 'gemini'."
        )
    return Orchestrator(knowledge_base, model, logger)
