import json

from src.groundedness import check_groundedness
from src.knowledge_base import KnowledgeBase


def test_wrong_number_is_rejected():
    knowledge = KnowledgeBase(
        "d:/Projects/FuseMachine/Week18/admissions_guardrails/data/knowledge_base.json"
    )
    result = check_groundedness(
        "The application fee is 450 US dollars.",
        [knowledge.get("KB003")],
    )
    assert result.flagged
    assert result.details["numbers_consistent"] == [False]


def test_negated_claim_is_rejected():
    knowledge = KnowledgeBase(
        "d:/Projects/FuseMachine/Week18/admissions_guardrails/data/knowledge_base.json"
    )
    result = check_groundedness(
        "The application fee is not 45 US dollars.",
        [knowledge.get("KB003")],
    )
    assert result.flagged


def test_supported_numeric_claim_still_passes():
    knowledge = KnowledgeBase(
        "d:/Projects/FuseMachine/Week18/admissions_guardrails/data/knowledge_base.json"
    )
    result = check_groundedness(
        "The application fee is 45 US dollars per submitted application.",
        [knowledge.get("KB003")],
    )
    assert not result.flagged
