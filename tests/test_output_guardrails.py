import json

from src.knowledge_base import KnowledgeBase
from src.model import MockModel
from src.orchestrator import Orchestrator
from src.output_pipeline import evaluate_output
from src.output_schema import validate_response
from src.output_sensitive import detect_output_leakage


def kb():
    return KnowledgeBase(
        "d:/Projects/FuseMachine/Week18/admissions_guardrails/data/knowledge_base.json"
    )


def test_schema_reports_specific_errors():
    verdict = validate_response('{"confidence": 1.7}', {"KB001"})
    assert verdict.flagged
    assert "Missing required field(s)" in verdict.reason
    assert "between 0 and 1" in verdict.reason


def test_markdown_fence_is_reported():
    raw = "```json\n{\"answer\":\"x\"}\n```"
    verdict = validate_response(raw, {"KB001"})
    assert verdict.flagged
    assert "markdown code fence" in verdict.reason


def test_grounded_clean_response_passes():
    knowledge = kb()
    entries = [knowledge.get("KB001")]
    raw = json.dumps({
        "answer": entries[0].text,
        "sources": ["KB001"],
        "confidence": 0.9,
        "category": "deadlines",
        "status": "answered",
    })
    decision = evaluate_output(raw, knowledge, entries)
    assert decision.allowed
    assert json.loads(decision.final_text)["status"] == "answered"


def test_confidential_output_is_blocked():
    knowledge = kb()
    verdict = detect_output_leakage(
        knowledge.get("KB014").text, knowledge.entries
    )
    assert verdict.flagged
    assert verdict.kind == "confidential_leak"
    assert verdict.suggested_action == "block"


def test_invalid_model_output_retries_once_then_falls_back():
    knowledge = kb()
    scripted = {
        "bad": '{"answer":"missing fields"}',
    }
    model = MockModel(scripted)
    orchestrator = Orchestrator(knowledge, model)
    result = orchestrator.run("What is the application fee?", case_id="bad")
    final = json.loads(result["final_response"])
    assert final["status"] == "answered"
    assert model.calls == 2
