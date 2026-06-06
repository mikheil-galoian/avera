"""AI Review Copilot boundary for AVERA.

The copilot **assists interpretation of evidence**. It never decides a release and
never generates free-form claims. It is deterministic and template-based: it can
only surface facts that are literally present in the supplied evidence pack, and
it always attaches a citation to the artifact + field it read.

If the evidence pack does not contain support for a question, the copilot returns
``"insufficient evidence"`` rather than guessing. This is the no-hallucination
contract — every answer value is traceable to a field in the pack.
"""

from .review_copilot import (
    COPILOT_ANSWER_SCHEMA_VERSION,
    INSUFFICIENT_EVIDENCE,
    AIReviewCopilot,
    Citation,
    CopilotAnswer,
    answer_question,
)

__all__ = [
    "COPILOT_ANSWER_SCHEMA_VERSION",
    "INSUFFICIENT_EVIDENCE",
    "AIReviewCopilot",
    "Citation",
    "CopilotAnswer",
    "answer_question",
]
