import json

from src.knowledge_base import KnowledgeBase
from src.logger import DecisionLogger
from src.model import MockModel
from src.orchestrator import Orchestrator


def test_retrieval_excludes_confidential_entries(tmp_path):
    kb = KnowledgeBase(
        "d:/Projects/FuseMachine/Week18/admissions_guardrails/data/knowledge_base.json"
    )
    entries = kb.retrieve("What is the admissions deadline?")
    assert entries
    assert all(not entry.confidential for entry in entries)


def test_orchestrator_runs_and_logs(tmp_path):
    kb = KnowledgeBase(
        "d:/Projects/FuseMachine/Week18/admissions_guardrails/data/knowledge_base.json"
    )
    log_path = tmp_path / "decisions.jsonl"
    orchestrator = Orchestrator(kb, MockModel(), DecisionLogger(log_path))

    result = orchestrator.run("What is the application fee?", case_id="phase2-fee")

    assert result["retrieved_context"]
    assert json.loads(result["final_response"])["status"] == "answered"
    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["input"] == "What is the application fee?"


def test_scripted_mock_output_is_deterministic():
    model = MockModel({"case-1": '{"status": "scripted"}'})
    assert model.generate("x", [], case_id="case-1") == '{"status": "scripted"}'
    assert model.calls == 1
