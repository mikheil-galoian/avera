"""Formal sign-off workflow for AVERA.

A sign-off is a human accountability record bound to a specific evidence set via
the Evidence Manifest's ``integrity_root``. It follows a small, explicit state
machine:

    draft -> reviewed -> approved
    draft -> rejected
    reviewed -> rejected

Every sign-off is bound to ``evidence_manifest.integrity_root``. If the manifest
later changes (any bound artifact changes), the sign-off no longer validates —
approval cannot silently carry over to different evidence.

The gate stays deterministic; sign-off is a separate human layer recorded as a
JSON artifact and appended to the hash-chained audit log. AVERA never approves a
release on its own — a sign-off always records a human identity, role, and reason.
"""

from .workflow import (
    SIGNOFF_SCHEMA_VERSION,
    SIGNOFF_STATES,
    TERMINAL_STATES,
    VALID_TRANSITIONS,
    SignoffError,
    SignoffEvent,
    SignoffRecord,
    SignoffValidation,
    create_signoff,
    load_signoff,
    transition_signoff,
    validate_signoff_against_manifest,
    write_signoff,
)
from .audit_binding import SIGNOFF_EVENT, record_signoff_in_audit_log

__all__ = [
    "SIGNOFF_SCHEMA_VERSION",
    "SIGNOFF_STATES",
    "TERMINAL_STATES",
    "VALID_TRANSITIONS",
    "SIGNOFF_EVENT",
    "SignoffError",
    "SignoffEvent",
    "SignoffRecord",
    "SignoffValidation",
    "create_signoff",
    "transition_signoff",
    "validate_signoff_against_manifest",
    "record_signoff_in_audit_log",
    "write_signoff",
    "load_signoff",
]
