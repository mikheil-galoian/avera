# AVERA AI Extension — AI Change Verification

**Status:** Production-ready proof of concept  
**Added:** 2026-05-07  
**Verified:** 2026-05-08

---

## What This Proves

AVERA's kernel detects AI model regressions **without any modifications to the core pipeline**.

A single adapter (`ai_evaluation.py`) converts AI evaluation artifacts into the standard
AVERA verification_results format. The baseline comparator, risk classifier, gate policy,
and memory ledger all operate identically — because from their perspective, a failed pedestrian
detection scenario is indistinguishable from a failed BMS voltage test.

This is the foundation of **AVERA as AI Change Verification Infrastructure**.

---

## Demonstrated Scenario

**Fixture:** `fixtures/adas-model-update-regression`

| Property | Value |
|---|---|
| Component | ADAS Perception Module (YOLOv8, TDA4VM) |
| Model update | v2.4.0 → v2.4.1 |
| Root cause | Retrain on expanded dataset + int8 quantization |
| Threshold violated | `detection_rate` = 0.94 < required 0.95 (REQ-SAFETY-012, ASIL-D) |

**Kernel verdict:**

```json
{
  "verdict": "confirmed_regression",
  "risk": "release_blocking",
  "confidence": "high",
  "confidence_score": 0.95,
  "affected_components": ["adas-perception-module"],
  "affected_requirements": ["REQ-SAFETY-012"],
  "evidence": {
    "detection_rate": {
      "baseline": 0.97,
      "current": 0.94,
      "operator": ">=",
      "threshold": 0.95
    }
  },
  "model_metadata": {
    "model_version": "2.4.1",
    "model_hash": "sha256:e7d3...",
    "certification_status": "pending_validation",
    "quantization": "int8",
    "changes_from_baseline": [
      "Retrained on adas-dataset-v7.2 with 15% additional night/rain scenarios",
      "Applied int8 post-training quantization for TDA4VM optimization",
      "Training data distribution shifted toward highway scenarios"
    ]
  }
}
```

---

## Files Added

### `src/avera/adapters/ai_evaluation.py`

Converts AI evaluation artifacts into AVERA verification_results format.

```python
from avera.adapters.ai_evaluation import load_ai_evaluation, model_card_to_metadata

# Load AI evaluation → AVERA verification_results
results = load_ai_evaluation("path/to/evaluation.json")
# Returns: {"runId": ..., "stage": ..., "tests": [...]}

# Load model card → report metadata
meta = model_card_to_metadata("path/to/model_card.json")
# Returns: {"model_version": ..., "certification_status": ..., ...}
```

**AI evaluation format** (`baseline_results.json`, `current_results.json`):

```json
{
  "runId": "eval-adas-perception-v2.4.1",
  "stage": "sil",
  "modelVersion": "2.4.1",
  "tests": [
    {
      "testId": "SC-SAFETY-012-night-rain",
      "name": "Pedestrian detection - night rain scenario",
      "requirement": "REQ-SAFETY-012",
      "component": "adas-perception-module",
      "metric": "detection_rate",
      "value": 0.94,
      "threshold": 0.95,
      "operator": ">=",
      "passed": false
    }
  ]
}
```

### `src/avera/ingestion/model_card.py`

Loads AI model card artifacts for embedding in AVERA reports.

```python
from avera.ingestion.model_card import load_model_card

meta = load_model_card("model_card_current.json")
# Returns: {model_id, model_version, model_hash, architecture, ...}
```

**Model card format** (`model_card_current.json`):

```json
{
  "model_id": "adas-perception-v2.4.1",
  "version": "2.4.1",
  "model_hash": "sha256:...",
  "architecture": "YOLOv8-medium-custom",
  "quantization": "int8",
  "certification_status": "pending_validation",
  "changes_from_baseline": ["..."]
}
```

### `src/avera/ingestion/verification_results.py` (modified)

Added AI format compatibility to `_test_result_from_mapping`. The change is purely additive:

- `testId` → `id` (if `id` absent)
- `passed: bool` → `status: "passed"/"failed"` (if `status` absent)
- `metric`/`value` inline fields → `metrics: {metric: value}` dict (if `metrics` absent)

Standard AVERA fixtures with `id`, `status`, and `metrics` fields are unaffected.

### `fixtures/adas-model-update-regression/` (new fixture)

Eight-file fixture pack proving the AI regression detection scenario:

```
baseline_results.json       ← 6 scenarios, all pass, model v2.4.0
current_results.json        ← 6 scenarios, 1 fail: detection_rate=0.94, model v2.4.1
requirements.csv            ← 6 requirements with metric/operator/threshold
component_map.json          ← adas-perception-module mapped to all requirements
model_card_baseline.json    ← certified model v2.4.0, float32
model_card_current.json     ← pending v2.4.1, int8, with changes_from_baseline
change_description.txt      ← human-readable change context
```

### `tests/test_ai_model_update_fixture.py` (new test)

14 tests in two classes:

- `TestAIModelUpdateFixture` — 6 full-pipeline tests confirming verdict, risk, components, requirements, evidence, change_description
- `TestAIEvaluationAdapter` — 8 unit tests on `load_ai_evaluation` and `model_card_to_metadata`

All 14 tests pass.

---

## Requirements CSV Format for AI Fixtures

AI fixtures use the same requirements format as automotive fixtures. Each metric threshold
becomes one requirement row:

```csv
id,component,requirement,metric,operator,threshold,safety_level
REQ-SAFETY-012,adas-perception-module,Pedestrian detection rate >= 0.95,detection_rate,>=,0.95,d
REQ-SAFETY-008,adas-perception-module,False positive rate <= 0.05,false_positive_rate,<=,0.05,c
```

`safety_level` maps directly to risk escalation: `d` → `release_blocking`, `c` → `high`, `b` → `medium`.

---

## How to Add a New AI Fixture

1. Create `fixtures/<your-fixture-name>/`

2. Write `baseline_results.json` and `current_results.json` in the AI evaluation format
   (see schema above, with `testId`, `passed`, `metric`, `value`, `threshold`, `operator`)

3. Write `requirements.csv` with columns:
   `id,component,requirement,metric,operator,threshold,safety_level`

4. Write `component_map.json`:
   ```json
   {
     "model/<component-id>": {
       "component": "<component-id>",
       "requirements": ["REQ-001", "REQ-002"]
     }
   }
   ```

5. Write `change_description.txt` with the human-readable change context

6. Optionally add `model_card_baseline.json` and `model_card_current.json`

7. Add expected outcome to `fixtures/expected_outcomes.json`:
   ```json
   "<your-fixture-name>": {
     "verdict": "confirmed_regression",
     "risk": "release_blocking",
     "confidence": "high"
   }
   ```

8. Run:
   ```bash
   PYTHONPATH=src python3 -B -m pytest tests/test_ai_model_update_fixture.py -v
   ```

---

## Regulatory Context

| Regulation | Requirement | AVERA Provides |
|---|---|---|
| FDA AI/ML-SaMD | Evidence at each model update | Structured proof chain with baseline/current comparison |
| EU AI Act | Risk assessment for high-risk AI | `risk` classification with `affected_requirements` |
| UNECE WP.29 | Safety proof for OTA AI updates | `verdict` + `evidence` + `model_metadata` in one report |
| ISO 26262 | Traceability from requirement to verification | `affected_requirements` mapped through `component_map` |

---

## Next Steps

1. **PyPI packaging** — `pip install avera[ai]` with optional AI adapter dependencies
2. **GitHub Action** — CI gate that blocks merge when `verdict == "confirmed_regression"`
3. **Medical device fixture** — FDA AI/ML-SaMD scenario with IEC 62304 requirements
4. **Aviation fixture** — DO-178C / ARP4754A scenario with neural network certification
5. **Continuous monitoring** — `avera watch` daemon for nightly model drift detection
