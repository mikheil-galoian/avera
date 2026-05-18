# AVERA Decision Log

**Date created:** 21 April 2026  
**Purpose:** Preserve major AVERA decisions across future sessions

## Decision 33

**Decision:** Real external artifacts should enter AVERA through thin adapters before the stable workspace contract is changed.

**Reason:** The kernel is already proven on a stable local workspace boundary. The safest path toward real evidence is to normalize external formats into that boundary first. The first active example is `adapt-junit`, which converts JUnit / xUnit XML into AVERA verification-results JSON.

## Decision 34

**Decision:** The second adapter layer should prioritize simulation-results CSV and prove itself through a normal adapted workspace, not only through an isolated converter command.

**Reason:** AVERA is an automotive evidence product, so simulation-heavy metrics are a better second bridge than a generic log parser. A realistic adapted workspace proves not just conversion, but the whole intended path: external artifact -> stable AVERA workspace -> normal analysis flow.

## Decision 48

**Decision:** The first external AVERA pilot must be governed by an explicit safety checklist that keeps scope local-first, owner-bounded, artifact-bounded, and human-reviewed.

**Reason:** The current project risk is no longer missing internal structure, but letting the first real pilot expand into a broad platform promise, integration sale, or data grab before a narrow proof loop exists. A dedicated safety checklist protects the first pilot from scope inflation and keeps claims aligned with what the product can actually prove today.

## Decision 49

**Decision:** AVERA should maintain organization-specific outreach packets for a short list of validation-heavy target companies instead of relying only on generic outward-facing materials.

**Reason:** The current bottleneck is execution of real outreach, not absence of documentation. Company-specific packets reduce friction, keep the pilot framing concrete, and make it easier to move from internal readiness to external conversations.

## Decision 1

**Decision:** The project direction is named `AVERA`.

**Reason:** AVERA is short, brandable, and can stand for `Automotive Verification, Evidence & Risk Architecture`. It is broad enough for a long-term automotive engineering platform while still preserving the core evidence and verification promise.

## Decision 2

**Decision:** AVERA is positioned as an automotive engineering evidence architecture, not a generic AI assistant.

**Reason:** Generic AI assistants are likely to commoditize. Durable value comes from traceability, evidence, baseline comparison, risk reasoning, and engineering memory.

## Decision 3

**Decision:** AVERA is a separate standalone project direction.

**Reason:** AVERA targets automotive engineering across software, requirements, validation, safety risk, lifecycle evidence, and long-term engineering memory. It should not depend on or be framed as a vertical of another project.

## Decision 4

**Decision:** The first AVERA product should be `AVERA Change Impact`.

**Reason:** Change impact is narrow enough to build as an MVP, but central enough to grow into requirements traceability, simulation evidence, safety review, and field feedback correlation.

## Decision 5

**Decision:** The first demo domain should be Battery Management System verification.

**Reason:** BMS scenarios are technically meaningful, easy to explain, and naturally support numeric threshold evidence such as maximum cell temperature during fast charging.

## Decision 6

**Decision:** AVERA should begin with local workspace/reporting workflows rather than a dashboard.

**Reason:** Local reports are faster to validate and avoid premature UI/platform expansion.

## Decision 7

**Decision:** AI should be treated as an interface over evidence, not as the source of engineering truth.

**Reason:** Automotive engineering requires auditable evidence and human responsibility. AI-generated explanations must be grounded in artifacts, not treated as proof by themselves.

## Decision 8

**Decision:** AVERA should avoid claims of automatic certification or universal safety approval.

**Reason:** The product can organize and explain evidence, but certification and safety approval require formal processes, accountable humans, and domain-specific validation.

## Decision 9

**Decision:** The first AVERA evidence graph should connect `change -> requirement -> verification result -> failure evidence -> risk`.

**Reason:** This is the smallest useful proof chain for an automotive change impact workflow.

## Decision 10

**Decision:** Broader automotive areas such as CAD/CAE, manufacturing, service, warranty, fleet telemetry, and supplier accountability are future phases, not MVP requirements.

**Reason:** The 20-30 year vision needs those areas, but the first proof-of-function must stay narrow enough to build and validate.

## Decision 11

**Decision:** AVERA core starts as a local-first Python evidence kernel.

**Reason:** Python is the best fit for local engineering artifacts, CSV/JSON evidence, simulation outputs, and future signal analysis. Local-first execution keeps the MVP independent of cloud accounts, GitHub, or hosted services.

## Decision 12

**Decision:** Evidence graph v0 should be emitted as deterministic JSON before introducing SQLite or a graph database.

**Reason:** File-based graph output keeps the first architecture inspectable, testable, and easy to revise while preserving a path toward durable engineering memory.

## Decision 13

**Decision:** Fixture expansion is the next validation priority.

**Reason:** AVERA must prove conservative behavior across successful changes, preexisting failures, insufficient evidence, and confirmed regressions before expanding to more domains or interfaces.

## Decision 14

**Decision:** AVERA reports should include explainability fields: `rules_triggered`, `confidence_factors`, and `risk_drivers`.

**Reason:** Automotive engineering review needs to see why a verdict was produced. Explainable reports reduce blind trust in the classifier and make future rule refinement safer.

## Decision 15

**Decision:** The first local runner validates all fixtures and writes reports per scenario under `reports/fixtures/`.

**Reason:** A fixture matrix gives AVERA a repeatable acceptance loop without requiring pytest, CI, cloud services, or external tooling.

## Decision 16

**Decision:** AVERA classifier v0.3 includes `worsened_preexisting_failure`, `environment_failure`, and `requirements_coverage_gap`.

**Reason:** AVERA must distinguish new regressions from old issues, environment failures, and missing verification coverage. This keeps the product conservative and closer to real engineering review.

## Decision 17

**Decision:** Evidence graph v0.2 includes rule, confidence-factor, and risk-driver nodes.

**Reason:** The graph should preserve why a verdict was produced, not only what the verdict was. This is necessary for long-term traceability and review trust.

## Decision 18

**Decision:** AVERA reports should preserve both a categorical confidence label and a numeric `confidence_score`.

**Reason:** Reviewers need the stable human-facing label (`low`, `medium`, `high`) while future automation needs a sortable numeric confidence value for dashboards, gates, and long-term trend analysis.

## Decision 19

**Decision:** Signal trace summaries are attached to CLI reports and evidence graphs when `signal_trace.csv` is present.

**Reason:** Automotive evidence often depends on measured signals over time. Summaries keep the first CLI lightweight while preserving a bridge toward richer simulation, HIL, and telemetry analysis.

## Decision 20

**Decision:** AVERA includes a deterministic local gate policy before any dashboard or hosted workflow.

**Reason:** Engineering teams need machine-readable pass/review/block behavior for CI and release review. A local gate keeps the MVP useful without depending on GitHub, cloud services, or UI infrastructure.

## Decision 21

**Decision:** `avera analyze` returns success when report generation succeeds; blocking/review exit codes belong to `avera gate`.

**Reason:** Analysis and policy enforcement are separate responsibilities. This prevents high-risk findings from masking real CLI/runtime errors in fixture runners and future CI workflows.

## Decision 22

**Decision:** AVERA exports a derived workspace pack instead of treating the pack as a new source of truth.

**Reason:** The portable bundle should help review, handoff, and archival without competing with the underlying evidence artifacts that generated it.

## Decision 23

**Decision:** The first workspace pack includes report, graph, memory slice, traceability, decision, and manifest.

**Reason:** This is the smallest useful portable bundle that preserves proof, context, and actionability for an engineering review.

## Decision 24

**Decision:** AVERA includes a local query layer over the traceability index before any UI shell.

**Reason:** The kernel needs a stable way to answer targeted evidence questions so future agents and future UI surfaces can stay thin over proven local contracts.

## Decision 22

**Decision:** AVERA engineering memory should be stored as an append-only local JSONL ledger.

**Reason:** JSONL is simple, inspectable, diff-friendly, and easy to append without rewriting historical records. That makes it a good fit for durable local engineering memory and later audit review.

## Decision 23

**Decision:** The first memory record types should be `analysis` and `gate`.

**Reason:** Those two events capture the core AVERA accountability loop: the evidence-producing analysis run and the policy decision that follows it.

## Decision 24

**Decision:** `avera analyze` and `avera gate` are the two write points for the memory ledger.

**Reason:** Keeping memory writes attached to the existing analysis and gate workflow preserves a clean source of truth and avoids hidden side effects from unrelated commands.

## Decision 25

**Decision:** AVERA should add a local traceability index as a derived layer over workspace artifacts and the memory ledger.

**Reason:** The project needs a deterministic way to connect component, requirement, test, failure, risk, and gate history before any UI shell exists. A derived index keeps the system evidence-first while making the relationship chain queryable for the core, CLI, and future interfaces.

## Decision 26

**Decision:** AVERA should add a dedicated decision engine above classifier, gate, traceability, and memory.

**Reason:** The project needs a deterministic layer that converts evidence-backed findings into an auditable operational decision without collapsing classifier output, policy enforcement, traceability, and memory into one opaque step. This keeps the system conservative and preserves reviewability as the product grows.

## Decision 27

**Decision:** AVERA should add a workspace pack/export layer that packages report, graph, memory slice, traceability, decision, and manifest artifacts into one portable bundle.

**Reason:** The project needs a stable handoff boundary between the local CLI and future UI or review workflows. A workspace pack preserves provenance, keeps the bundle derived from existing evidence, and makes exported runs easier to inspect without turning the pack into a new source of truth.

## Decision 28

**Decision:** AVERA decision engine recommendations should use policy v2 with `owner_routing`, `corrective_actions`, `verification_playbook`, and `escalation` as the primary outputs.

**Reason:** The engine now needs to do more than emit a coarse block/allow/review-style outcome. Engineering review is better served when the system can name the owner, suggest the corrective path, prescribe the next verification steps, and escalate explicitly when the evidence is still too weak or conflicted for a stronger recommendation.

## Decision 29

**Decision:** AVERA should add a Trend / Baseline Evolution Layer as a derived historical summary above traceability, decision, and workspace pack outputs.

**Reason:** The kernel already compares a single baseline against a current run. It now needs a conservative historical layer that can summarize component trends, requirement trends, test stability, and verdict/risk history across runs without turning history into a new source of truth.

## Decision 30

**Decision:** AVERA should define stable artifact contracts for report, graph, memory, traceability, decision, trend, and workspace pack outputs before expanding CLI export behavior further.

**Reason:** The core artifact families need a shared stability layer so validation, compatibility, packing, and future automation can rely on explicit schema and provenance rules instead of ad hoc expectations. This keeps derived outputs deterministic, reviewable, and safe to consume across commands and future interfaces.

## Decision 31

**Decision:** AVERA should scale in four horizons: stabilize the current kernel, prove second-domain portability, extend into shared review and memory workflows, then grow toward long-term mobility evidence infrastructure.

**Reason:** The project already has a real local evidence kernel, so the next execution model should build from implemented layers instead of restarting at abstract platform strategy. A staged scaling framework keeps product claims aligned with actual proof capability and preserves the conservative evidence architecture as scope expands.

## Decision 32

**Decision:** The current design-partner boundary is considered ready once the local runtime proves full-suite verification, a one-command demo launch, a working second domain, and a short external demo flow.

**Reason:** At this point the limiting factor is no longer whether the kernel exists, but whether the prototype is stable and explainable enough for real external conversations. This keeps AVERA focused on believable productization instead of premature platform expansion.

## Decision 33

**Decision:** The next execution layer after design-partner readiness is a pilot-readiness and full-version preparation phase built around runtime stabilization, shell hardening, realistic artifact adapters, domain expansion, and layered testing.

**Reason:** AVERA now has enough proof to stop behaving like a concept build. The next responsible step is to make the system steadier, more realistic, and more testable before claiming broader product readiness.

## Decision 34

**Decision:** The supported AVERA demo/runtime path is the repository `.venv` plus `scripts/runtime_doctor.py`, with a static ADAS showcase fallback when the live Streamlit shell is slow to cold-start.

**Reason:** The local kernel is already proven. The practical risk is now runtime friction during shell-heavy or external-demo sessions, so the project needs one explicit supported path and one explicit fallback.

## Decision 35

**Decision:** The first operational use of AVERA should be a narrow local-first pilot around change review, baseline-vs-current evidence, and human release triage.

**Reason:** The product is now strong enough for a first real workflow, but it still needs to stay constrained to one operator-driven review path so the kernel, runtime, and output contracts remain trustworthy during early use.

## Decision 36

**Decision:** AVERA should keep one single-file master document for ongoing development, shell evolution, pilot preparation, and release assembly.

**Reason:** The project now has enough layers, docs, and operating logic that future work should not depend on reconstructing intent from many scattered files. A single master document reduces drift and makes the project easier to continue, review, and package.

## Decision 37

**Decision:** The third adapter layer should target richer requirements export variants and prove itself through a second adapted workspace of a different type.

**Reason:** After simulation evidence, the next strongest pilot boundary is upstream requirements variety. A BMS workspace built from an adapted requirements export proves that AVERA can normalize external requirement formats while preserving the same local evidence-first review flow.

## Decision 38

**Decision:** The next adapter after simulation and requirements should be a richer verification-log path, and the shell should expose an explicit adapted-pilot boundary when raw source artifacts are present.

**Reason:** The project now needs to show not only that external artifacts can be normalized, but also that reviewers can clearly see the raw-to-normalized boundary in the product. A log-driven workspace plus adapted-pilot shell mode makes that boundary visible and usable during pilot conversations.

## Decision 39

**Decision:** AVERA should consolidate its outward-facing and pilot-preparation materials into a dedicated readiness master document before first real pilot execution.

**Reason:** The project now has enough outreach, runtime, adapter, and pilot-intake material that the next bottleneck is not missing vision but fragmented readiness context. A single readiness base reduces drift, clarifies execution order, and gives the team one reference point before moving from preparation into real pilot conversations.

## Decision 40

**Decision:** The first real AVERA pilot should target a Verification / Validation team, with a Validation Lead as the preferred owner, and should start from a verification-log artifact family if available.

**Reason:** This is the current strongest bridge between AVERA's adapted evidence paths and a real engineering workflow. Verification logs are closest to live validation practice, and a Validation Lead can usually scope one narrow local-first pilot without forcing broad platform rollout too early.

## Decision 41

**Decision:** AVERA should create and maintain one explicit live pilot-run record before starting real external pilot motion.

**Reason:** Once the project moves from preparation into real outreach and pilot scoping, the team needs one document that tracks target, owner, artifact family, status, next action, and emerging objections. Without that, pilot execution risks becoming fragmented across packets and chat context.

## Decision 42

**Decision:** AVERA should separate the live outreach run from the broader pilot-run record, so first-contact motion and later pilot execution can be tracked independently.

**Reason:** The first external move has its own success criteria: reply, owner, artifact family, and follow-up. Keeping outreach as a distinct run prevents early signal from being mixed with later pilot execution details and makes the go-to-use path easier to manage.

## Decision 43

**Decision:** The next operational layer after pilot-outreach setup should include a target shortlist, a contact tracker, and a sample export request template.

**Reason:** Once outreach starts, the main risk is losing discipline in who to approach, how to track signal, and how to request the smallest useful real artifact set. These three tools keep the first pilot motion narrow, comparable, and executable.

## Decision 44

**Decision:** AVERA should assemble one dedicated launch kit that binds outreach, pilot-run, target, contact-tracking, and sample-export materials into a single operational entry point.

**Reason:** The project now has enough outward-facing and pilot-preparation pieces that the next risk is operational fragmentation. A dedicated launch kit reduces switching cost, keeps the first external motion coherent, and gives the team one practical bundle to execute from.

## Decision 45

**Decision:** After the launch kit, AVERA should add a seeded target/contact layer, a real pilot execution log, an English first-contact entry, and an explicit external-artifact examples base before the first live pilot starts.

**Reason:** These additions close the most practical remaining gaps without pretending that real external artifacts already exist. They make the project easier to operate internationally, easier to start from, and clearer about what real inputs are still needed from outside teams.

## Decision 46

**Decision:** AVERA should keep one compact set of channel-specific outreach drafts for email, DM, and Reddit before first external motion starts.

**Reason:** The project already has checklists and packets, but actual first movement benefits from ready-to-send language. A small draft set reduces friction, keeps the message consistent across channels, and makes outward motion easier without creating a heavy marketing layer.

## Decision 47

**Decision:** AVERA should explicitly add a Reddit-style post draft and a forwardable intro blurb as first-motion channel assets.

**Reason:** Warm introductions and community discovery are the two most realistic early channels for the project. Giving both channels ready-to-use language reduces hesitation and makes first external movement more practical without overstating product maturity.
