"""Adversarial-hardening tests for the audit log: keyed tamper-evidence,
truncation anchor, and fixed-schema verification."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from avera.audit import AuditLog, ChainIntegrityError


def _seed(path: Path, key=None, n=3):
    log = AuditLog(path, key=key)
    for i in range(n):
        log.append(event="verdict_issued", project="p", run_id=f"r{i}", verdict="confirmed_regression")
    return log


# --- keyed (HMAC) tamper-evidence: re-stitch without the key fails -----------

def test_keyed_log_verifies():
    import tempfile
    p = Path(tempfile.mkdtemp()) / "a.jsonl"
    log = _seed(p, key="s3cret", n=3)
    assert log.verify_chain() == 3


def test_keyed_log_rejects_unkeyed_restitch():
    import tempfile
    p = Path(tempfile.mkdtemp()) / "a.jsonl"
    _seed(p, key="s3cret", n=3)
    # Attacker WITHOUT the key forges record 0's verdict and re-stitches the whole
    # chain using plain SHA-256 (they don't know the HMAC key).
    lines = p.read_text().splitlines()
    def canon(o): return json.dumps(o, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    prev = hashlib.sha256(b"").hexdigest()
    new_lines = []
    for ln in lines:
        obj = json.loads(ln)
        obj["payload"]["verdict"] = "successful_change"  # forge
        obj["prev_hash"] = prev
        pre = {k: obj[k] for k in ("seq", "timestamp_utc", "event", "project", "prev_hash", "payload")}
        obj["self_hash"] = hashlib.sha256(canon(pre).encode()).hexdigest()  # no key
        prev = obj["self_hash"]
        new_lines.append(json.dumps(obj, ensure_ascii=False, separators=(",", ":")))
    p.write_text("\n".join(new_lines) + "\n")
    with pytest.raises(ChainIntegrityError):
        AuditLog(p, key="s3cret").verify_chain()


# --- truncation anchor -------------------------------------------------------

def test_truncation_detected_with_anchor():
    import tempfile
    p = Path(tempfile.mkdtemp()) / "a.jsonl"
    _seed(p, n=4)
    lines = p.read_text().splitlines()
    p.write_text("\n".join(lines[:2]) + "\n")  # drop last 2
    log = AuditLog(p)
    assert log.verify_chain() == 2  # self-consistent prefix — passes without anchor
    with pytest.raises(ChainIntegrityError):
        log.verify_chain(expected_count=4)  # anchor catches truncation


def test_head_mismatch_detected():
    import tempfile
    p = Path(tempfile.mkdtemp()) / "a.jsonl"
    _seed(p, n=3)
    with pytest.raises(ChainIntegrityError):
        AuditLog(p).verify_chain(expected_last_hash="0" * 64)


# --- default (unkeyed) behaviour preserved ----------------------------------

def test_unkeyed_default_still_works():
    import tempfile
    p = Path(tempfile.mkdtemp()) / "a.jsonl"
    log = _seed(p, n=3)
    assert log.verify_chain() == 3
    records = log.read_all()
    assert len(records) == 3 and records[0].seq == 0


# --- honest tamper-evidence reporting (audit: keyless chain is forgeable) ----

def test_keyed_flag_reflects_key_presence():
    import tempfile
    p = Path(tempfile.mkdtemp()) / "a.jsonl"
    assert AuditLog(p).keyed is False
    assert AuditLog(p, key="s3cret").keyed is True


def test_tamper_evidence_level_is_honest():
    import tempfile
    p = Path(tempfile.mkdtemp()) / "a.jsonl"
    assert AuditLog(p).tamper_evidence == "change-detection-only"
    assert AuditLog(p, key="s3cret").tamper_evidence == "keyed-hmac"


def test_keyless_verify_warns_about_forgeability(caplog):
    import logging
    import tempfile
    p = Path(tempfile.mkdtemp()) / "a.jsonl"
    log = _seed(p, n=2)
    with caplog.at_level(logging.WARNING):
        log.verify_chain()
    assert any("AVERA_AUDIT_KEY" in r.message for r in caplog.records)


def test_keyed_verify_does_not_warn(caplog):
    import logging
    import tempfile
    p = Path(tempfile.mkdtemp()) / "a.jsonl"
    log = _seed(p, key="s3cret", n=2)
    with caplog.at_level(logging.WARNING):
        log.verify_chain()
    assert not any("AVERA_AUDIT_KEY" in r.message for r in caplog.records)
