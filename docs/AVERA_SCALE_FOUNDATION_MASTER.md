# AVERA — Scale Foundation Master

**Date:** 7 May 2026
**Status:** Strategic architecture document — foundation for long-term global buildout
**Project:** AVERA

---

## Preface: What This Document Is

AVERA has passed its first test. As of 30 April 2026 the kernel is real:
63 tests pass, the full pipeline runs deterministically, the BMS and ADAS
domains both prove the architecture works, and the design-partner story is
ready.

The question now is not whether the kernel is valid. It is.

The question is: **how do we build from this kernel into something that
automotive, aerospace, robotics, and safety-critical engineering teams
worldwide can depend on for the next 10–30 years?**

This document answers that question in full. It is a strategic architecture
plan and a sequenced execution framework. Every decision here follows a single
principle:

> The kernel's proof discipline must survive every scale transition intact.

If a decision weakens conservative evidence handling, determinism, or
traceability, that decision is rejected. Scale serves the mission. The mission
is not sacrificed for scale.

---

## Part 1 — The Kernel as the Immutable Core

### 1.1 What the Kernel Is and Must Remain

The AVERA kernel is the reasoning machine. It is local-first, deterministic,
artifact-driven, and conservative by design. Every layer built above it must
treat it as a fixed contract, not as implementation detail.

Current kernel boundary (`src/avera/`):

```text
ingestion
  → normalized models
  → baseline comparator
  → risk classifier
  → report generator
  → evidence graph builder
  → gate policy evaluator
  → engineering memory ledger
  → traceability index
  → decision engine
  → trend index
  → stable artifact contracts
  → workspace pack exporter
```

This pipeline must remain the kernel. It must not be dissolved into a web
service, a database trigger, or a cloud function. It must remain callable as
a pure Python function chain from any execution environment.

### 1.2 Schema Versioning as a First-Class Contract

Every artifact emitted by the kernel carries `schema_version`. This is already
implemented. What must now be formalized:

**Versioning policy:**

- `schema_version` follows semver (`major.minor.patch`)
- minor version bumps are backward-compatible additions
- major version bumps require a migration path and are announced with a
  minimum 90-day deprecation window
- the kernel must always be able to read artifacts it produced in any prior
  minor version
- the kernel must never silently accept a malformed artifact and produce a
  wrong result — it must reject or warn

**Artifact version registry** (`src/avera/contracts/versions.py`):

A central registry that maps artifact type to the current schema version and
the set of supported historical versions. This file is the single source of
truth for compatibility guarantees.

### 1.3 Determinism Guarantees

Every run of the kernel on the same inputs must produce byte-identical JSON
output. This is already largely true. It must be formally enforced:

- all timestamp fields must be excluded from determinism scope (they are
  audit metadata, not reasoning output)
- all other fields must be deterministic given identical inputs
- the fixture matrix (`scripts/run_all_fixtures.py`) is the determinism
  regression test
- a dedicated `test_kernel_determinism.py` must be added that runs each
  fixture twice and compares outputs

### 1.4 The Kernel Must Never Own Product Logic

No UI logic, no user management, no cloud session state, no API routing must
ever enter `src/avera/`. The kernel owns reasoning. Everything else owns
product.

This separation is the reason AVERA can run inside a GitHub Action, a Jupyter
notebook, a REST service, a desktop app, or an air-gapped HIL rack — without
modification.

---

## Part 2 — Storage Evolution Path

The current file-based storage is correct for the kernel stage. It must evolve
in phases without changing the kernel API.

### Phase 1 — File-Based (Current, Complete)

```text
avera-report.json
avera-report.md
avera-evidence-graph.json
avera-memory.jsonl
avera-traceability-index.json
avera-decision.json
avera-trend-index.json
avera-workspace-pack.json
```

Suitable for: single engineer, local runs, demos, CI artifacts.

No action required. This layer is stable and must remain the canonical
offline and air-gapped path forever.

### Phase 2 — SQLite (Local Team, Q3 2026 Target)

When multiple engineers share a project, the JSONL ledger and file-per-run
pattern breaks. The solution is a local SQLite database that mirrors the
current artifact contracts as relational tables.

**Schema map:**

| Current artifact      | SQLite table(s)                              |
|-----------------------|----------------------------------------------|
| `avera-report.json`   | `analysis_runs`, `verdicts`, `evidence_items`|
| `avera-memory.jsonl`  | `memory_records`                             |
| `traceability-index`  | `traceability_links`                         |
| `decision.json`       | `decisions`, `corrective_actions`            |
| `trend-index.json`    | `trend_summaries`                            |
| `workspace-pack.json` | `workspace_packs`, `manifests`               |

**Key rules:**
- the SQLite layer is a mirror of the file artifacts, never a replacement
- the kernel still emits JSON files; a separate sync layer writes to SQLite
- reads from SQLite, writes from kernel — no kernel modification required
- the SQLite file lives next to the workspace or in a shared project directory

**Module location:** `src/avera/storage/sqlite_store.py`

### Phase 3 — PostgreSQL (Hosted / Team, Q1 2027 Target)

When teams span multiple machines, a shared PostgreSQL instance replaces the
local SQLite file. The schema is identical; only the connection layer changes.

**Configuration via `avera.config.json`:**

```json
{
  "storage": {
    "backend": "postgresql",
    "dsn": "postgresql://user:pass@host:5432/avera"
  }
}
```

The storage backend is pluggable. The kernel is not touched. Product layers
route through a storage interface (`src/avera/storage/interface.py`) that
dispatches to file, SQLite, or PostgreSQL depending on configuration.

### Phase 4 — Distributed (Enterprise, 2027+)

Large OEM programs produce thousands of analysis runs per week. At that scale:

- object storage (S3, GCS, Azure Blob) holds large artifact files (signal
  traces, simulation exports, log archives)
- PostgreSQL holds structured analysis metadata and relationship indexes
- a read replica handles reporting and trend queries
- the kernel runs in a containerized worker pool (see Part 9)

The kernel itself is unchanged. Only the storage layer and the execution
wrapper scale.

---

## Part 3 — API Layer

The kernel must be reachable from multiple execution contexts without
duplication of reasoning logic.

### 3.1 Python SDK (Immediate Priority)

The current `src/avera/core.py` `analyze()` function is already a Python SDK
entry point. What must be added:

- full docstring coverage on every public function
- typed return types using `TypedDict` or dataclasses
- a stable `__all__` in `src/avera/__init__.py` defining the public surface
- a `CHANGELOG.md` tracking SDK changes by version

This is the primary integration surface for teams embedding AVERA in their
own Python automation.

### 3.2 REST API (FastAPI, Q3 2026 Target)

A thin FastAPI wrapper around the kernel exposes AVERA to non-Python
environments — CI systems, dashboards, external tools.

**Structure:** `src/avera_api/` (separate from kernel)

**Endpoints:**

```
POST   /analyze             — run analysis, return report
POST   /validate-workspace  — validate workspace shape
GET    /report/{run_id}     — retrieve a generated report
GET    /decision/{run_id}   — retrieve decision artifact
GET    /traceability/{run_id} — retrieve traceability index
GET    /trend               — retrieve trend index
POST   /gate                — evaluate gate on a report
GET    /query               — query traceability (component, requirement, test)
GET    /memory              — query engineering memory ledger
GET    /pack/{run_id}       — retrieve workspace pack
GET    /health              — health check
```

**Design rules:**
- the API layer calls kernel functions — it never reimplements reasoning
- every response includes `schema_version` from the underlying artifact
- authentication is handled at the API layer (see Part 7)
- the API layer is optional — the kernel runs without it

### 3.3 CLI as First-Class Interface (Always)

The CLI (`src/avera/cli.py`) must remain the primary operator interface. It
must never be downgraded to a development-only tool.

**Why:** Air-gapped automotive environments, CI runners, HIL rack automation,
and offline pilot deployments all depend on the CLI. The REST API is an
additional surface, not a replacement.

Every new kernel capability must have a CLI command before or simultaneously
with an API endpoint.

### 3.4 gRPC (Enterprise Integration, 2027+)

For high-throughput integration with PLM platforms, CI orchestrators, and
automotive toolchain APIs, a gRPC interface provides better performance and
contract enforcement than REST.

**Proto definition:** `proto/avera.proto`

The gRPC interface mirrors the REST surface but operates on binary-encoded
messages and supports streaming analysis results for long-running jobs.

---

## Part 4 — Integration Ecosystem

AVERA's long-term value depends on how easily it accepts inputs from the
real tools automotive engineering teams use every day.

### 4.1 Input Adapter Roadmap

**Already implemented:**
- JUnit XML (`src/avera/adapters/junit.py`)
- requirements CSV/JSON (`src/avera/adapters/requirements.py`)
- simulation result CSV/JSON (`src/avera/adapters/simulation.py`)
- generic log adapter (`src/avera/adapters/logs.py`)

**Next tier (Phase 3 — Q4 2026):**

| Source                          | Format                    | Adapter target                        |
|---------------------------------|---------------------------|---------------------------------------|
| xUnit (NUnit, MSTest)           | XML variants              | `adapters/xunit.py`                   |
| CTest                           | XML + JSON                | `adapters/ctest.py`                   |
| CAPL scripts / CANoe reports    | XML + CSV                 | `adapters/canoe.py`                   |
| MATLAB/Simulink test reports    | XML/MLDATX                | `adapters/simulink.py`                |
| dSPACE ControlDesk exports      | CSV + XML                 | `adapters/dspace.py`                  |
| ETAS INCA exports               | CSV + XML                 | `adapters/inca.py`                    |
| DOORS NG exports                | CSV + ReqIF               | `adapters/doors.py`                   |
| Jama Connect exports            | CSV + JSON                | `adapters/jama.py`                    |
| Polarion ALM exports            | XML + CSV                 | `adapters/polarion.py`                |
| CAN trace (MDF4 → CSV bridge)   | CSV                       | `adapters/can_trace.py`               |
| AUTOSAR ARXML component maps    | XML                       | `adapters/arxml.py`                   |

**Adapter contract:**
Every adapter must produce a standard AVERA workspace-compatible artifact set.
No adapter may modify the kernel. Adapters are pure data translators.

**Adapter SDK:**
Third-party teams must be able to write their own adapters using a published
adapter interface (`src/avera/adapters/interface.py`). This interface defines:

```python
class AveraAdapter(Protocol):
    def name(self) -> str: ...
    def supported_input_formats(self) -> list[str]: ...
    def to_verification_results(self, path: Path) -> dict: ...
    def to_requirements(self, path: Path) -> list[dict]: ...
    def to_component_map(self, path: Path) -> dict: ...
```

### 4.2 CI/CD Integration

**GitHub Actions (Q3 2026):**

```yaml
# .github/workflows/avera-analysis.yml
- uses: avera-eng/avera-action@v1
  with:
    project: fixtures/bms-fast-charge
    out: reports
    fail-on: block
```

**GitLab CI (Q4 2026):**

```yaml
avera-analysis:
  image: averaeng/avera:latest
  script:
    - avera analyze --project $PROJECT_DIR --out reports
    - avera gate --report reports/avera-report.json
```

**Jenkins plugin (Q4 2026):** A Jenkins plugin that reads the workspace pack
and publishes an AVERA report badge and artifact summary to the build page.

**Azure DevOps task (Q1 2027):** Azure Pipelines task extension.

**The gate exit code contract is the integration surface.** Gate returns
exit code 0 (pass), 1 (review), or 2 (block). CI systems use exit code 2 to
block merge or promotion. This is already implemented and must not change.

### 4.3 PLM/ALM Platform Integrations

These are Phase 4–5 integrations. They require bidirectional data flow, which
means they must be product-layer features, not kernel changes.

**Jama Connect:** Export change impact analysis results back to Jama as
review items linked to the affected requirements.

**Siemens Polarion:** Synchronize AVERA verdicts and traceability links
into Polarion work items.

**IBM DOORS Next:** Fetch requirements from DOORS, run analysis, push
coverage gap findings back.

**JIRA:** Create JIRA tickets for confirmed regressions and escalations,
pre-filled from the decision engine's corrective action output.

All PLM integrations use the workspace pack or the REST API as the data
source. No PLM connector touches the kernel.

---

## Part 5 — Standards Compliance Layer

AVERA's strategic position in the automotive market depends on explicit
alignment with the standards that govern safety-critical software development.

### 5.1 ISO 26262 — Functional Safety

ISO 26262 Part 6 (software) requires:

- software change impact analysis
- regression verification evidence
- traceability from safety requirements to tests
- review and approval records

**AVERA's role:**
- the `affected_requirements` field in every report already connects changes
  to requirements
- the traceability index already maps component → requirement → test
- the evidence graph already exports the proof chain
- the engineering memory ledger is an append-only audit trail

**What must be built (Phase 5):**
- an ISO 26262 report template that structures existing AVERA output into the
  evidence format auditors expect
- ASIL-level tagging on requirements (A, B, C, D) fed from the component map
- gate policy extensions that enforce stricter thresholds for ASIL-C and ASIL-D
  items
- a `--compliance iso26262` flag on `avera validate-artifact` that checks
  evidence completeness against Part 6 tables

### 5.2 ASPICE — Process Assessment

ASPICE SWE.4 (software unit verification) and SWE.5 (software integration
testing) require structured test result evidence with traceability.

**AVERA's role:**
- every `avera analyze` run produces ASPICE-compatible verification evidence
- the traceability index satisfies the traceability requirement
- the engineering memory ledger provides the history auditors need

**What must be built (Phase 5):**
- an ASPICE report template that maps AVERA artifacts to ASPICE practice
  indicators
- a `--compliance aspice` validation mode
- process capability level indicators derived from trend data

### 5.3 ISO/SAE 21434 — Cybersecurity Engineering

As vehicles become software-defined, cybersecurity evidence becomes as
important as functional safety evidence.

**AVERA's role for 21434:**
- change impact analysis for cybersecurity-relevant components
- evidence of regression testing for security-relevant functions
- traceability from cybersecurity requirements to verification tests

**What must be built (Phase 5):**
- a cybersecurity domain module with `security_relevance` tagging
- TARA (Threat Analysis and Risk Assessment) result ingestion
- cybersecurity-specific verdict vocabulary
- a `--compliance iso21434` validation mode

### 5.4 UN R155 / R156 — Type Approval

UN R155 (cybersecurity) and R156 (software updates) require OEMs to maintain
evidence of security management across the vehicle lifecycle.

**AVERA's role:** The engineering memory ledger and workspace pack are the
building blocks of a lifecycle evidence repository that supports R155/R156
conformance demonstrations.

---

## Part 6 — Multi-Domain Architecture

The kernel's domain-neutral design is its most important long-term asset. The
BMS and ADAS scenarios already prove the architecture is not domain-specific.

### 6.1 Domain Module Architecture

Each domain is a configuration and policy extension, not a kernel modification.

**Domain module structure:**

```text
src/avera/domains/
  bms/
    __init__.py
    policy.py          — gate thresholds and verdict rules for BMS
    requirements.py    — BMS-specific requirement field extensions
    signal_norms.py    — expected signal trace ranges for BMS scenarios
    verdicts.py        — BMS-specific verdict labels (if any)
  adas/
    policy.py
    requirements.py
    signal_norms.py
  powertrain/
    ...
  chassis/
    ...
  cybersecurity/
    ...
  body/
    ...
```

A domain module can override:
- gate policy thresholds
- verdict rule priority
- signal norm expectations
- report template sections

A domain module cannot:
- change the kernel pipeline order
- introduce new reasoning logic outside `src/avera/`
- bypass the conservative classification principle

### 6.2 Domain Expansion Roadmap

| Domain             | Priority | Target    | Notes                                      |
|--------------------|----------|-----------|--------------------------------------------|
| BMS                | Done     | —         | Fast-charge, coverage, regression, mixed   |
| ADAS               | Done     | —         | Pedestrian detection regression proven     |
| Powertrain         | High     | Q3 2026   | ECU calibration changes, dyno test results |
| Chassis            | High     | Q4 2026   | Steering, braking, suspension ECUs         |
| Cybersecurity      | High     | Q1 2027   | Security test results, TARA linkage        |
| Body Electronics   | Medium   | Q2 2027   | Lighting, comfort, access systems          |
| ADAS++ (L3/L4)     | High     | Q2 2027   | Autonomy stack, scenario test results      |
| OTA Updates        | Medium   | Q3 2027   | Delta validation, rollback evidence        |
| Commercial Trucks  | Medium   | 2027      | FMCSA-relevant evidence patterns          |
| Off-Highway/Ag     | Low      | 2028      | Different regulatory landscape             |
| Robotics           | Medium   | 2028      | Non-automotive but kernel-compatible       |
| Rail               | Low      | 2028+     | EN 50128/50657 standards alignment         |

### 6.3 Cross-Domain Evidence Chains

In software-defined vehicles, a single software change can touch BMS, ADAS,
and cybersecurity simultaneously. The traceability index must grow to support:

- cross-domain requirement links (one change → multiple domain impacts)
- cross-domain gate aggregation (the overall gate is the strictest of all
  domain gates)
- cross-domain evidence graph (a single graph that spans domain boundaries)

This is a Phase 6 feature. It requires no kernel changes — only enriched
component map schemas and a cross-domain aggregation layer above the current
per-domain analysis.

---

## Part 7 — Team and Enterprise Features

### 7.1 Multi-Project Support

The current kernel operates on one project folder per run. A product layer
must support:

- project registry (multiple named projects in one organization)
- shared engineering memory across projects in the same program
- project-level configuration (domain, gate policy, compliance mode)
- cross-project trend comparison

**Implementation:** The project registry lives in the storage layer (SQLite or
PostgreSQL). The kernel remains single-project per invocation. The product
layer orchestrates cross-project operations.

### 7.2 Authentication and Authorization (API Layer)

When the REST API is deployed in a shared environment:

- **Authentication:** API key (simple), OAuth 2.0 / OIDC (enterprise SSO)
- **Authorization:** role-based access control

**Roles:**

| Role              | Permissions                                              |
|-------------------|----------------------------------------------------------|
| `viewer`          | read reports, graphs, decisions, trends                  |
| `analyst`         | run analysis, validate workspaces                        |
| `reviewer`        | approve gate decisions, add manual review comments       |
| `admin`           | manage projects, users, configuration, compliance modes  |

The kernel itself has no authentication. Authentication is entirely an
API-layer concern.

### 7.3 Shared Engineering Memory

The current engineering memory ledger is a local JSONL file. In team
deployments, it must become a shared, queryable record store.

**Requirements:**
- append-only guarantee preserved (no record deletion via API)
- cross-run queries (show all `confirmed_regression` events for component X)
- cross-project queries (show all `release_blocking` decisions in the last 30
  days across all active programs)
- export for audit (generate a PDF or CSV of all memory records in a date
  range for a given project)

### 7.4 Review and Approval Workflows

In regulated environments, a human engineer must formally approve or dispute
an AVERA decision before it is recorded as final.

**Workflow:**

```text
avera analyze → decision engine → status: pending_review
  ↓
reviewer receives notification
  ↓
reviewer approves, disputes, or escalates
  ↓
decision record updated with reviewer identity, timestamp, comment
  ↓
memory ledger records the final state
```

This is a product-layer feature. The kernel's decision engine output is the
input to the review workflow. The workflow does not change the kernel output;
it records a human verdict alongside it.

---

## Part 8 — AI-Assisted Analysis (Conservative by Design)

AI assistance is the right next layer for AVERA — but only under strict
constraints that preserve the evidence-first principle.

### 8.1 What AI Can and Cannot Do in AVERA

**AI can:**
- suggest possible root causes for a `confirmed_regression` (based on change
  description and failure pattern)
- flag anomalies in signal traces that are below formal threshold violations
- identify patterns in engineering memory that suggest recurring failure modes
- generate a natural-language summary of the evidence for human review
- suggest which test cases should be added to close a `requirements_coverage_gap`

**AI cannot:**
- produce a verdict on its own
- override the classifier, gate, or decision engine
- certify a change as safe
- replace the conservative proof chain

Every AI output must be labeled `ai_suggestion` in the artifact, never
`evidence` or `verdict`. Human review is required before any AI suggestion
is acted upon.

### 8.2 AI Integration Points

**Root cause suggestion engine (`src/avera/ai/root_cause.py`):**
- input: change description, failure list, affected components, signal summary
- output: a list of candidate root causes with confidence levels, labeled
  as suggestions
- runs after the classifier, not before
- uses an LLM via a configured API endpoint (OpenAI, Anthropic, local Ollama)
- the kernel works identically when this module is absent or disabled

**Signal anomaly detector (`src/avera/ai/signal_anomaly.py`):**
- input: signal trace points
- output: flagged anomalous segments with brief description
- supplements the existing signal summary, never replaces threshold evidence

**Memory pattern recognizer (`src/avera/ai/memory_patterns.py`):**
- input: engineering memory ledger records for a component
- output: identified recurring failure patterns with first and last occurrence
- surfaces trends that the deterministic trend index may not capture

**Natural language report narrator (`src/avera/ai/narrator.py`):**
- input: full report JSON
- output: a narrative paragraph describing the analysis result in plain
  English
- intended for report consumers who are not verification engineers

### 8.3 AI Configuration

AI features are disabled by default. They are enabled in `avera.config.json`:

```json
{
  "ai": {
    "enabled": true,
    "provider": "anthropic",
    "model": "claude-sonnet-4-6",
    "features": ["root_cause", "narrator"],
    "max_suggestion_tokens": 500
  }
}
```

In air-gapped environments, `provider` can be set to `ollama` with a local
model. In environments where AI is prohibited, `"enabled": false` ensures
zero AI involvement at runtime.

---

## Part 9 — Global Deployment Architecture

### 9.1 Containerization (Q3 2026)

**Dockerfile structure:**

```dockerfile
FROM python:3.11-slim
WORKDIR /avera
COPY src/ src/
COPY pyproject.toml .
RUN pip install -e "."
ENTRYPOINT ["python", "-m", "avera"]
```

**Images:**

| Image tag              | Contents                              | Use case                    |
|------------------------|---------------------------------------|-----------------------------|
| `averaeng/avera:cli`   | kernel + CLI only                     | CI runners, HIL automation  |
| `averaeng/avera:api`   | kernel + CLI + REST API               | Hosted deployment           |
| `averaeng/avera:demo`  | kernel + CLI + REST API + Streamlit   | Design-partner demos        |

### 9.2 Air-Gapped and Local-First Guarantee

The `averaeng/avera:cli` image must run with zero internet access. All
automotive manufacturing environments are potentially air-gapped. The kernel
must work without any network calls, telemetry, or external service dependency.

This guarantee must be formally tested: a CI job runs the full fixture matrix
with the network interface disabled.

### 9.3 Kubernetes Deployment (Q1 2027)

For shared team deployments and enterprise rollouts:

```yaml
# avera-api deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: avera-api
spec:
  replicas: 3
  template:
    spec:
      containers:
        - name: avera-api
          image: averaeng/avera:api
          env:
            - name: AVERA_STORAGE_BACKEND
              value: postgresql
            - name: AVERA_DB_DSN
              valueFrom:
                secretKeyRef:
                  name: avera-db
                  key: dsn
```

**Scaling model:**
- analysis workers scale horizontally (each run is independent)
- the storage layer is shared state
- the kernel is stateless — it reads inputs, emits outputs, writes to storage

### 9.4 Multi-Region and Data Sovereignty

Automotive OEMs operate globally with strict data residency requirements.
Germany, Japan, the USA, and China all have different rules about where
engineering data can be stored.

**AVERA's response:**
- each region runs its own AVERA deployment with its own PostgreSQL instance
- no cross-region artifact replication by default
- cross-region trend aggregation (anonymized, schema-level only) is an opt-in
  feature
- the air-gapped CLI image satisfies the strictest data sovereignty requirements
  because no data leaves the local environment

### 9.5 Deployment Environments Supported

| Environment         | Image              | Storage          | Auth            |
|---------------------|--------------------|------------------|-----------------|
| Local laptop        | local Python       | file-based       | none            |
| CI runner           | `avera:cli`        | file-based       | none            |
| HIL rack (air-gap)  | `avera:cli`        | file-based       | none            |
| Engineering team    | `avera:api`        | SQLite / Postgres| API key         |
| Enterprise OEM      | `avera:api` on k8s | PostgreSQL       | OIDC/SSO        |
| Cloud SaaS          | `avera:api` on k8s | PostgreSQL + S3  | OIDC/SSO        |

---

## Part 10 — Packaging, Distribution, and Developer Ecosystem

### 10.1 PyPI Package

```bash
pip install avera
pip install avera[demo]     # + Streamlit demo shell
pip install avera[api]      # + FastAPI REST layer
pip install avera[ai]       # + AI suggestion features
pip install avera[all]      # everything
```

**Release cadence:**
- patch releases: as needed for bug fixes
- minor releases: monthly, adding new features without breaking the kernel API
- major releases: maximum once per year, with a 90-day deprecation window

### 10.2 Adapter SDK on PyPI

Third-party teams publish their own adapters as separate packages:

```bash
pip install avera-adapter-polarion
pip install avera-adapter-canoe
pip install avera-adapter-jama
```

Each adapter follows the `AveraAdapter` protocol (see Part 4.1). AVERA
auto-discovers installed adapters through Python entry points.

### 10.3 GitHub Actions Marketplace

The `avera-action` GitHub Action makes it trivial to add AVERA analysis to
any automotive software repository:

```yaml
- uses: avera-eng/avera-action@v1
  with:
    project: ${{ inputs.project_dir }}
    out: avera-reports
    domain: bms
    compliance: iso26262
    fail-on: block
    upload-pack: true
```

The action uploads the workspace pack as a GitHub Actions artifact, making
the full analysis available for download from the build summary.

### 10.4 Documentation Site

The documentation site (`docs.avera.engineering`) publishes:

- Getting Started in 5 minutes
- Kernel API reference (auto-generated from docstrings)
- Adapter SDK guide
- CI/CD integration guides (GitHub, GitLab, Jenkins, Azure)
- Standards alignment guide (ISO 26262, ASPICE, ISO 21434)
- Compliance report templates
- Domain module guide
- REST API reference (auto-generated from FastAPI OpenAPI spec)
- Architecture decision log
- Changelog by version

### 10.5 Community and Commercial Model

**Open core:**
- the kernel (`src/avera/`) is open source (MIT or Apache 2.0)
- the CLI is open source
- the adapter SDK and base adapters are open source
- the GitHub Action is open source

**Commercial extensions:**
- the enterprise REST API (multi-tenant, RBAC, SSO) is commercial
- PLM/ALM connectors (Jama, Polarion, DOORS) are commercial
- the compliance report template pack (ISO 26262, ASPICE, 21434) is commercial
- shared engineering memory for team deployments is commercial
- AI-assisted analysis is commercial (usage-based pricing)
- dedicated support and SLA are commercial

This model is proven in developer tooling (GitLab, HashiCorp, Elastic). The
open kernel grows adoption. The commercial extensions capture value from
engineering organizations that need enterprise-grade features.

---

## Part 11 — Long-Term Engineering Memory at Scale

This is AVERA's deepest strategic moat.

### 11.1 From Local Ledger to Institutional Memory

The current JSONL ledger captures what happened on one engineer's machine.
At scale, engineering memory becomes the institutional record of how a vehicle
program's software has evolved across years, suppliers, and engineering teams.

**What multi-year engineering memory enables:**

- "This component has failed 14 times in the last 3 model years. Here is the
  pattern." — cross-program regression history
- "This requirement has never been fully verified in any of the 47 change
  impact analyses that touched it." — systematic coverage gap detection
- "The last 3 times a change touched this area, the gate blocked. The average
  resolution time was 12 days." — decision pattern intelligence
- "Similar failure patterns were observed in program X in 2024. Here is the
  evidence chain from that resolution." — cross-program learning

### 11.2 Memory Architecture at Scale

```text
Local run
  → analysis memory record (JSONL, current)
  → gate memory record (JSONL, current)
  ↓
Team memory layer (SQLite / PostgreSQL)
  → indexed by component, requirement, project, verdict, risk, date
  ↓
Program memory layer (PostgreSQL, shared across projects in a vehicle program)
  → cross-project trend views
  → recurring failure pattern detection
  ↓
Organization memory layer (read-only aggregated views, anonymized)
  → cross-program intelligence
  → anonymized benchmark data
```

Each layer adds read capabilities. None removes the append-only guarantee of
the base ledger.

### 11.3 Engineering Memory as a Long-Term Product

Engineering memory that spans 10–30 years of vehicle programs is an
irreplaceable institutional asset. Organizations that use AVERA consistently
across programs accumulate a proof corpus that:

- supports future safety audits with historical evidence
- accelerates onboarding of new engineers into established failure patterns
- reduces regression rates because patterns are recognized before deployment
- provides the factual basis for supplier quality reviews

This is the reason AVERA's core principle — `engineering truth, preserved as
evidence` — is not a tagline. It is the value proposition that compounds over
decades.

---

## Part 12 — Sequenced Execution Plan

### Now (May–June 2026)

Priority 1: first design-partner pilot with a real engineering team.

What the pilot requires:
- clean `./start_demo.sh` launch path (already done)
- BMS and ADAS scenarios demonstrated (already done)
- ability to accept a real fixture from the partner's own data format
- post-pilot feedback captured in structured form

Priority 2: PyPI packaging.

```bash
pip install avera
```

This single command must work. It unlocks direct adoption without setup
friction.

Priority 3: schema versioning formalization. Add `CHANGELOG.md` and the
artifact version registry.

### Q3 2026

- GitHub Actions integration published
- FastAPI REST layer (basic, no auth)
- Powertrain domain module
- JUnit/xUnit/CTest adapter hardening
- SQLite storage backend
- Determinism regression tests

### Q4 2026

- Chassis domain module
- GitLab CI and Jenkins integrations
- CAPL/CANoe adapter
- ISO 26262 report template
- API authentication (API key)

### Q1 2027

- Cybersecurity domain module
- gRPC interface
- OIDC/SSO authentication
- PostgreSQL storage backend
- Kubernetes deployment manifests
- ASPICE report template

### Q2 2027

- ADAS++ (L3/L4) domain module
- Jama Connect adapter
- Cross-domain evidence chains
- AI root cause suggestions (opt-in)
- Documentation site v1

### Q3 2027 and Beyond

- Polarion ALM adapter
- DOORS Next adapter
- Multi-region deployment support
- OTA update domain module
- Program memory layer
- ISO/SAE 21434 compliance mode
- UN R155/R156 evidence support

### 2028–2030

- Commercial truck and off-highway domains
- Robotics domain
- Organization memory layer
- Cross-program benchmark intelligence
- Field feedback and lifecycle correlation

### 2030–2035 (Vision Layer)

```text
AVERA becomes the standard evidence infrastructure
for safety-critical engineered systems worldwide.

Every change to a safety-critical system leaves a durable,
traceable, proof-backed record — regardless of whether it
was made in Munich, Tokyo, Detroit, Seoul, or Shanghai.

Engineering truth, preserved as evidence.
Across domains. Across programs. Across decades.
```

---

## Immutable Principles for Every Transition

These principles must survive every scale transition, every funding round,
every partnership, every acquisition:

1. **The kernel is the proof machine.** It must never be compromised for
   product convenience.

2. **Determinism is non-negotiable.** The same inputs must always produce the
   same outputs. If a transition breaks this, the transition is wrong.

3. **Conservative by design.** AVERA should never claim more than the evidence
   supports. This is especially important as AI assistance is added. Weak
   evidence produces explicit uncertainty, not false confidence.

4. **Air-gapped must always work.** The CLI image must run with zero internet
   access, forever. Air-gapped automotive environments are not edge cases.
   They are the reality in regulated production.

5. **Schema stability is a promise.** Every user who depends on the JSON
   artifact shape is a partner. Breaking changes require explicit versioning,
   deprecation windows, and migration paths.

6. **Evidence is not marketing.** Report outputs describe what the analysis
   found. They do not claim regulatory compliance. They do not replace human
   engineering judgment. They inform it.

7. **The memory is append-only.** No analysis record, gate record, or decision
   record is ever deleted. Engineering accountability is permanent.

8. **The kernel stays in Python.** Python is the engineering data language.
   The kernel must remain accessible to mechanical engineers, validation
   engineers, and safety engineers who can read Python. It must not require
   a distributed systems engineer to understand.

---

*AVERA — Engineering Memory Infrastructure for Mobility*
*Document version 1.0 — 7 May 2026*
