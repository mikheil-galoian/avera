"""Tests for the deterministic, evidence-grounded AI Review Copilot.

The central guarantee under test: the copilot never invents facts. Every answer
is either grounded in a field that exists in the evidence pack (with a citation
whose value is verbatim from the pack) or it is "insufficient evidence".
"""

from __future__ import annotations

from avera.copilot import INSUFFICIENT_EVIDENCE, AIReviewCopilot, answer_question


def _pack():
    return {
        "report": {
            "verdict": "confirmed_regression",
            "risk": "high",
            "confidence": "high",
            "confidence_score": 0.95,
            "affected_requirements": [{"id": "BMS-REQ-112"}],
            "affected_components": ["BMS Thermal Control"],
        },
        "decision": {
            "action": "block",
            "release_recommendation": "do_not_release",
            "owner": "validation_and_component_owner",
        },
        "gate": {"status": "block"},
        "manifest": {"integrity_root": "a" * 64},
    }


# ---------------------------------------------------------------------------
# Grounded answers
# ---------------------------------------------------------------------------

def test_answers_verdict_from_pack_with_citation():
    a = answer_question("What is the verdict?", _pack())
    assert a.supported is True
    assert "confirmed_regression" in a.answer
    assert a.citations
    assert a.citations[0].source == "report"
    assert a.citations[0].field == "verdict"
    assert a.citations[0].value == "confirmed_regression"


def test_answers_risk_and_integrity_root():
    pack = _pack()
    assert "high" in answer_question("how risky is this?", pack).answer
    integ = answer_question("what is the manifest integrity root?", pack)
    assert integ.supported is True
    assert "a" * 64 in integ.answer
    assert integ.citations[0].field == "integrity_root"


def test_decision_answer_notes_human_review():
    a = answer_question("can we release this?", _pack())
    assert a.supported is True
    assert "block" in a.answer
    assert "human review" in a.answer.lower()


# ---------------------------------------------------------------------------
# No-hallucination: insufficient evidence
# ---------------------------------------------------------------------------

def test_unknown_question_returns_insufficient_evidence():
    a = answer_question("what is the supplier's phone number?", _pack())
    assert a.supported is False
    assert a.answer == INSUFFICIENT_EVIDENCE
    assert a.citations == ()


def test_known_intent_but_missing_fact_returns_insufficient():
    # Ask about risk, but the report has no risk field.
    pack = {"report": {"verdict": "successful_change"}}
    a = answer_question("what is the risk level?", pack)
    assert a.supported is False
    assert a.answer == INSUFFICIENT_EVIDENCE


def test_empty_pack_is_always_insufficient():
    copilot = AIReviewCopilot({})
    for q in ("verdict?", "risk?", "owner?", "integrity root?", "gate status?"):
        a = copilot.answer(q)
        assert a.supported is False
        assert a.answer == INSUFFICIENT_EVIDENCE


def test_empty_question_is_insufficient():
    a = answer_question("", _pack())
    assert a.supported is False


def test_every_cited_value_exists_verbatim_in_pack():
    """Hard no-hallucination guard: any cited value must be present in the pack."""
    pack = _pack()
    questions = [
        "verdict", "risk", "confidence", "affected requirements", "components",
        "decision action", "owner", "gate status", "integrity root",
    ]
    flat_values = _flatten_values(pack)
    for q in questions:
        a = answer_question(q, pack)
        for citation in a.citations:
            assert citation.value in flat_values, (
                f"copilot cited a value not present in the pack: {citation.value!r}"
            )


def _flatten_values(obj) -> list:
    out = []
    if isinstance(obj, dict):
        for v in obj.values():
            out.append(v)
            out.extend(_flatten_values(v))
    elif isinstance(obj, list):
        for v in obj:
            out.append(v)
            out.extend(_flatten_values(v))
    return out


def test_answer_serialization_roundtrip():
    a = answer_question("verdict?", _pack())
    d = a.to_dict()
    assert d["schema_version"] == "avera.copilot_answer.v0.1"
    assert d["supported"] is True
    assert d["citations"][0]["field"] == "verdict"
