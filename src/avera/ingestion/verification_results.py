"""Load baseline/current verification result JSON artifacts."""

from __future__ import annotations

from typing import Any

from avera.ingestion._helpers import PathLike, read_json_object, require_text
from avera.models.verification import TestResult, VerificationRun


RUN_KNOWN_FIELDS = ("runId", "run_id", "stage", "tests")
TEST_KNOWN_FIELDS = ("id", "component", "status", "metrics", "evidence")


def load_verification_results(path: PathLike) -> VerificationRun:
    """Load a baseline_results.json or current_results.json artifact."""

    data = read_json_object(path)
    tests = data.get("tests")
    if not isinstance(tests, list):
        raise ValueError(f"Verification results must include a tests array: {path}")

    run_id = data.get("runId", data.get("run_id"))
    run_record = {**data, "run_id": run_id}
    metadata = {
        key: value
        for key, value in data.items()
        if key not in RUN_KNOWN_FIELDS and value not in (None, "")
    }

    return VerificationRun(
        run_id=require_text(run_record, "run_id", str(path)),
        stage=require_text(data, "stage", str(path)),
        tests=tuple(_test_result_from_mapping(item, path, index) for index, item in enumerate(tests)),
        metadata=metadata,
    )


def _test_result_from_mapping(value: Any, path: PathLike, index: int) -> TestResult:
    if not isinstance(value, dict):
        raise ValueError(f"Verification test entry must be an object: {path} tests[{index}]")

    source = f"{path} tests[{index}]"

    # AI evaluation format compatibility: testId → id, passed (bool) → status
    normalized = dict(value)
    if "id" not in normalized and "testId" in normalized:
        normalized["id"] = normalized["testId"]
    if "status" not in normalized and "passed" in normalized:
        normalized["status"] = "passed" if normalized["passed"] else "failed"

    # AI evaluation format compatibility: inline metric/value → metrics dict
    metrics = normalized.get("metrics", {})
    if not isinstance(metrics, dict):
        raise ValueError(f"Verification test metrics must be an object: {source}")
    if not metrics and "metric" in normalized and "value" in normalized:
        metrics = {str(normalized["metric"]): normalized["value"]}

    metadata = {
        key: item
        for key, item in normalized.items()
        if key not in TEST_KNOWN_FIELDS and item not in (None, "")
    }

    return TestResult(
        id=require_text(normalized, "id", source),
        component=str(normalized.get("component") or "").strip(),
        status=require_text(normalized, "status", source),
        metrics=dict(metrics),
        evidence=str(normalized.get("evidence") or "").strip(),
        metadata=metadata,
    )
