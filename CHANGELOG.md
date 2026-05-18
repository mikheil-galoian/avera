# CHANGELOG

All notable changes to AVERA are documented here.

This project follows [Semantic Versioning](https://semver.org/).  
Schema-breaking changes require a new `schema_version` string and a 90-day deprecation window.

---

## [0.1.0] — 2026-05-08

### Summary

First public release. AVERA is an AI Change Verification Infrastructure for
safety-critical systems. It takes baseline and current verification evidence,
compares them against requirements, and produces a classified, auditable report.

No cloud dependency. No accounts. Deterministic. Air-gapped capable.

### Added

#### Core kernel (10-layer pipeline)
- `avera.ingestion` — load verification results, requirements CSV, component map, signal trace, model card
- `avera.compare` — baseline/current comparison with delta classification
- `avera.classify` — risk classification (confirmed_regression, successful_change, preexisting_failure, insufficient_evidence, worsened_preexisting_failure, environment_failure, requirements_coverage_gap)
- `avera.reports` — JSON + Markdown report generation with schema versioning
- `avera.graph` — evidence graph builder (nodes: component, requirement, test, rule, confidence, risk, signal)
- `avera.gates` — gate policy (pass / review / block)
- `avera.memory` — append-only engineering memory ledger (JSONL)
- `avera.traceability` — traceability index (component → requirement → test → risk → gate history)
- `avera.decisions` — decision engine with owner routing, corrective actions, verification playbook
- `avera.trends` — trend index with verdict/risk/test stability history
- `avera.pack` — workspace pack export (report + graph + memory + traceability + decision + trend + manifest)
- `avera.query` — query engine for component/requirement/test/risk/gate
- `avera.contracts` — artifact schema validation + version registry

#### AI Change Verification (new in v0.1.0)
- `avera.adapters.ai_evaluation` — converts AI evaluation JSON (scenario-based metric tests) to AVERA verification_results format
- `avera.ingestion.model_card` — loads AI model card artifacts; embedded in report as `model_metadata`
- `avera.core` — auto-loads `model_card_current.json` when present in the analysis directory
- Fixture: `fixtures/adas-model-update-regression` — ADAS perception model v2.4.0 → v2.4.1 with ASIL-D regression

#### Adapters
- `avera.adapters.junit` — JUnit XML to AVERA verification_results
- `avera.adapters.simulation` — simulation result CSV to AVERA format
- `avera.adapters.logs` — log file adapter
- `avera.adapters.requirements` — requirements adapter

#### Fixture matrix (13 scenarios)
- BMS domain (8): fast-charge, successful-change, preexisting-failure, insufficient-evidence, worsened-preexisting, environment-failure, coverage-gap, mixed-results
- ADAS domain (3): pedestrian-detection-regression, simulation-adapted, model-update-regression (AI)
- Adapted (2): bms-log-adapted, bms-requirements-adapted

#### Infrastructure
- CLI: `avera analyze`, `avera gate`, `avera decision`, `avera trend`, `avera pack`, `avera query`, `avera validate-workspace`, `avera validate-artifact`, `avera demo-refresh`
- `scripts/run_all_fixtures.py` — full fixture matrix runner with expected outcomes verification
- `fixtures/expected_outcomes.json` — expected verdict/risk/confidence per fixture
- `src/avera/contracts/versions.py` — artifact schema version registry with backward-compatibility tracking
- `.github/workflows/avera-analysis.yml` — CI workflow: test suite + fixture matrix + AI verification gate + schema contracts

#### Documentation
- `docs/AVERA_AI_EXTENSION.md` — AI change verification guide for engineering teams
- `docs/AVERA_SCALE_FOUNDATION_MASTER.md` — global scaling architecture (12-part, 2026–2035)
- `docs/AVERA_ACTION_PLAN_2026_05_07.md` — sequenced execution plan (Blocks 1–6)
- `docs/outreach/AVERA_EMAIL_AI_TEAMS.md` — design partner outreach templates

#### Tests
- 63 tests across core pipeline, CLI, demo orchestration, artifact contracts
- 14 new tests in `tests/test_ai_model_update_fixture.py` for AI change verification
- Target: 77 tests passing

### Supported artifact schema versions

| Artifact | Current version | Supported versions |
|----------|-----------------|--------------------|
| report | 1.0 | 1.0 |
| graph | evidence_graph.0.3 | 0.1, 0.2, 0.3 |
| decision | 1.0 | 1.0 |
| trend | 1.0 | 1.0 |
| workspace_pack | 1.0 | 1.0 |
| model_card | 1.0 | 1.0 |
| ai_evaluation | 1.0 | 1.0 |

### Regulatory alignment

| Standard | Domain | Coverage |
|----------|--------|----------|
| ISO 26262 Part 8 | Automotive | Change impact analysis artifact, ASIL-linked requirements |
| UNECE WP.29 R156 | Automotive OTA | Model hash + verdict + evidence in one report |
| FDA AI/ML-SaMD | Medical AI | Baseline/current comparison with pre-defined performance thresholds |
| EU AI Act Art. 9 | High-risk AI | Risk classification linked to requirements with evidence chain |

---

## Roadmap

### [0.2.0] — Q3 2026 (planned)
- FastAPI REST wrapper (`avera_api`)
- Powertrain domain module
- SQLite storage backend
- Docker CLI image (`averaeng/avera:cli`)
- Adapter SDK interface (`avera.adapters.interface.AveraAdapter`)
- CANoe/CAPL adapter
- Kernel determinism regression tests

### [0.3.0] — Q4 2026 (planned)
- ISO 26262 compliance report template
- Chassis domain module
- GitLab CI + Jenkins integration examples
- API authentication (API key)
- ASPICE report template
- AI drift monitoring adapter

### [1.0.0] — Q1 2027 (planned)
- Cybersecurity domain (ISO/SAE 21434)
- PostgreSQL storage backend
- OIDC/SSO enterprise authentication
- Kubernetes manifests
- gRPC interface
- FDA AI/ML-SaMD compliance report template
