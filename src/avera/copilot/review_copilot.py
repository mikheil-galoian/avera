"""Deterministic, evidence-grounded AI Review Copilot stub.

This module is intentionally NOT a free-form LLM. It is a deterministic intent
matcher over an evidence pack. Each supported intent reads exactly one fact from
the pack and cites it. If the fact is missing, or no intent matches the question,
the copilot returns :data:`INSUFFICIENT_EVIDENCE`.

The evidence pack is a mapping that may contain any of::

    {
      "report":       {...},   # avera-report.json
      "decision":     {...},   # avera-decision.json
      "gate":         {...},   # gate decision dict
      "traceability": {...},   # avera-traceability-index.json
      "manifest":     {...},   # avera-evidence-manifest.json
    }

Design contract (no hallucination):
- Every non-insufficient answer carries at least one citation.
- Every cited value is taken verbatim from the pack — never synthesised.
- Unknown questions => insufficient evidence (the copilot does not guess).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

COPILOT_ANSWER_SCHEMA_VERSION = "avera.copilot_answer.v0.1"
INSUFFICIENT_EVIDENCE = "insufficient evidence"


@dataclass(frozen=True)
class Citation:
    source: str  # e.g. "report", "decision", "manifest"
    field: str   # e.g. "verdict", "integrity_root"
    value: Any

    def to_dict(self) -> dict[str, Any]:
        return {"source": self.source, "field": self.field, "value": self.value}


@dataclass(frozen=True)
class CopilotAnswer:
    question: str
    answer: str
    supported: bool
    citations: tuple[Citation, ...] = ()
    schema_version: str = COPILOT_ANSWER_SCHEMA_VERSION

    @property
    def is_insufficient(self) -> bool:
        return not self.supported

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "question": self.question,
            "answer": self.answer,
            "supported": self.supported,
            "citations": [c.to_dict() for c in self.citations],
        }


# ---------------------------------------------------------------------------
# Intent matching
# ---------------------------------------------------------------------------

def _get(pack: dict[str, Any], source: str, field_name: str) -> Any:
    payload = pack.get(source)
    if not isinstance(payload, dict):
        return None
    value = payload.get(field_name)
    if value in (None, "", [], {}):
        return None
    return value


@dataclass(frozen=True)
class _Intent:
    name: str
    keywords: tuple[str, ...]
    resolve: Callable[[dict[str, Any]], tuple[str, tuple[Citation, ...]] | None]


def _verdict(pack):
    v = _get(pack, "report", "verdict")
    if v is None:
        return None
    return f"The recorded verdict is '{v}'.", (Citation("report", "verdict", v),)


def _risk(pack):
    v = _get(pack, "report", "risk")
    if v is None:
        return None
    return f"The recorded risk level is '{v}'.", (Citation("report", "risk", v),)


def _confidence(pack):
    label = _get(pack, "report", "confidence")
    score = _get(pack, "report", "confidence_score")
    if label is None and score is None:
        return None
    cites = []
    parts = []
    if label is not None:
        parts.append(f"confidence '{label}'")
        cites.append(Citation("report", "confidence", label))
    if score is not None:
        parts.append(f"confidence_score {score}")
        cites.append(Citation("report", "confidence_score", score))
    return "The recorded " + " and ".join(parts) + ".", tuple(cites)


def _requirements(pack):
    v = _get(pack, "report", "affected_requirements")
    if v is None:
        return None
    return f"Affected requirements are recorded in the report ({len(v)} entry/entries).", (
        Citation("report", "affected_requirements", v),
    )


def _components(pack):
    v = _get(pack, "report", "affected_components")
    if v is None:
        return None
    return f"Affected components: {v}.", (Citation("report", "affected_components", v),)


def _decision(pack):
    action = _get(pack, "decision", "action")
    rec = _get(pack, "decision", "release_recommendation")
    if action is None and rec is None:
        return None
    cites = []
    parts = []
    if action is not None:
        parts.append(f"decision action '{action}'")
        cites.append(Citation("decision", "action", action))
    if rec is not None:
        parts.append(f"release recommendation '{rec}'")
        cites.append(Citation("decision", "release_recommendation", rec))
    return "The recorded " + " and ".join(parts) + ". (Human review still required.)", tuple(cites)


def _owner(pack):
    v = _get(pack, "decision", "owner")
    if v is None:
        return None
    return f"The routed owner is '{v}'.", (Citation("decision", "owner", v),)


def _gate(pack):
    v = _get(pack, "gate", "status")
    if v is None:
        return None
    return f"The gate status is '{v}'.", (Citation("gate", "status", v),)


def _integrity(pack):
    v = _get(pack, "manifest", "integrity_root")
    if v is None:
        return None
    return f"The evidence manifest integrity root is {v}.", (
        Citation("manifest", "integrity_root", v),
    )


_INTENTS: tuple[_Intent, ...] = (
    _Intent("integrity", ("integrity", "manifest", "hash", "root", "tamper"), _integrity),
    _Intent("confidence", ("confidence", "certain", "sure", "score"), _confidence),
    _Intent("requirements", ("requirement", "req", "affected requirement"), _requirements),
    _Intent("components", ("component", "module", "subsystem"), _components),
    _Intent("owner", ("owner", "who", "assigned", "responsible"), _owner),
    _Intent("decision", ("decision", "action", "release", "ship", "deploy", "recommend"), _decision),
    _Intent("gate", ("gate", "pass", "block", "blocked", "review"), _gate),
    _Intent("verdict", ("verdict", "regression", "result", "outcome", "classif"), _verdict),
    _Intent("risk", ("risk", "danger", "severity", "safety"), _risk),
)


class AIReviewCopilot:
    """A deterministic, evidence-grounded review assistant.

    It interprets evidence; it does not decide releases and does not invent facts.
    """

    def __init__(self, evidence_pack: dict[str, Any] | None = None) -> None:
        self.evidence_pack: dict[str, Any] = dict(evidence_pack or {})

    def answer(self, question: str, evidence_pack: dict[str, Any] | None = None) -> CopilotAnswer:
        pack = dict(evidence_pack) if evidence_pack is not None else self.evidence_pack
        q = str(question or "").strip().lower()

        if not q:
            return CopilotAnswer(question=question, answer=INSUFFICIENT_EVIDENCE, supported=False)

        for intent in _INTENTS:
            if any(keyword in q for keyword in intent.keywords):
                resolved = intent.resolve(pack)
                if resolved is not None:
                    text, citations = resolved
                    return CopilotAnswer(
                        question=question,
                        answer=text,
                        supported=True,
                        citations=citations,
                    )
                # Intent matched but the supporting fact is absent from the pack.
                return CopilotAnswer(
                    question=question,
                    answer=INSUFFICIENT_EVIDENCE,
                    supported=False,
                )

        # No known intent — never guess.
        return CopilotAnswer(question=question, answer=INSUFFICIENT_EVIDENCE, supported=False)


def answer_question(question: str, evidence_pack: dict[str, Any]) -> CopilotAnswer:
    """Convenience wrapper around :class:`AIReviewCopilot`."""

    return AIReviewCopilot(evidence_pack).answer(question)
