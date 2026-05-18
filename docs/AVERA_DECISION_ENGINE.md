# AVERA Decision Engine

**Project:** `AVERA`  
**Layer:** Core decision orchestration  
**Status:** Planned, following classifier, gate, traceability, and memory foundations  
**Last updated:** 28 April 2026

## Purpose

The AVERA decision engine is the layer that turns evidence-backed findings into a
conservative operational recommendation.

It does not replace classification, gating, traceability, or memory. Instead, it
consumes their outputs and chooses the next system action in a way that preserves
proof, provenance, reviewability, and owner accountability.

Core responsibility:

`evidence -> structured judgment -> action`

The decision engine is where AVERA answers:

- what decision should be made from the available evidence?
- is the result strong enough for automation, or does it need review?
- which prior history should influence the choice?
- what must be recorded so the decision can be audited later?
- who should own the follow-up work?
- what corrective action should be recommended?
- what verification playbook should be run next?
- when does the result require escalation?

## Role In The AVERA Stack

The decision engine sits above the classifier and gate, and alongside the
traceability index and memory ledger.

It uses:

- classifier verdicts and confidence
- gate outcomes and policy thresholds
- traceability links between change, requirement, test, failure, and risk
- memory history from earlier runs and prior decisions

It produces:

- a decision category
- a recommended next action
- owner routing
- corrective actions
- a verification playbook
- escalation guidance
- rationale for the decision
- references to the evidence and history used
- a record suitable for the memory ledger and later review

## Inputs

The decision engine should accept a structured decision context containing:

- analysis run identifier
- workspace or fixture identifier
- change description
- baseline and current verification results
- classifier verdict
- classifier confidence score
- gate status and gate reasons
- traceability lookups
- memory summary for the relevant artifact or scenario
- optional signal summaries, report artifacts, and provenance notes

Important input rule:

The decision engine should not infer a stronger decision than the evidence
supports. Missing or conflicting evidence should lower confidence or force a
manual review path.

## Outputs

The decision engine should return a structured decision result containing:

- `decision_category`
- `decision_action`
- `decision_confidence`
- `decision_rationale`
- `recommendation_policy_version`
- `owner_routing`
- `corrective_actions`
- `verification_playbook`
- `escalation`
- `supporting_evidence`
- `traceability_refs`
- `memory_refs`
- `follow_up_checks`
- `record_to_ledger`

The output should be deterministic for the same inputs and policy version.

## Relationship To Other Layers

### Classifier

The classifier identifies the evidence verdict, such as confirmed regression,
environment failure, preexisting failure, or insufficient evidence.

The decision engine uses that verdict as an input, but it should not silently
rewrite classifier meaning.

### Gate

The gate converts evidence into a policy outcome such as pass, review, or block.

The decision engine uses the gate as an execution policy signal and may refine
the next action, but it should not bypass the gate in a way that removes safety
or accountability.

### Traceability Index

The traceability index connects change, requirement, test, failure, and risk
history.

The decision engine uses traceability to justify why a decision applies to a
specific change, why a result looks preexisting, and which areas need more
checking.

### Memory

The memory ledger preserves previous analysis and gate decisions.

The decision engine reads memory for repeat-failure patterns, prior classification
history, and previously observed environment or coverage issues. It should also
write its own decision record back into memory so future runs can compare against
prior outcomes.

## Decision Categories

The decision engine should preserve these conservative categories as the
underlying classification buckets:

- `confirm_change_safe`
- `confirm_change_risky`
- `escalate_for_manual_review`
- `request_more_verification`
- `defer_due_to_insufficient_evidence`
- `carry_forward_preexisting_issue`
- `treat_as_environment_issue`
- `treat_as_coverage_gap`
- `flag_worsened_preexisting_issue`
- `record_confirmed_regression`

These categories are intentionally conservative. They are decision categories,
not marketing labels.

Suggested mapping:

- `confirm_change_safe` when evidence is strong, gate is passing, and traceability
  supports the result
- `confirm_change_risky` when the change is plausible but residual risk remains
- `escalate_for_manual_review` when evidence conflicts or judgment is not stable
- `request_more_verification` when more checks are needed before a final decision
- `defer_due_to_insufficient_evidence` when the input set is too thin for a strong
  call
- `carry_forward_preexisting_issue` when the failure predates the change
- `treat_as_environment_issue` when the signal points to setup or environment
  failure rather than product regression
- `treat_as_coverage_gap` when the workspace lacks adequate coverage for the
  affected area
- `flag_worsened_preexisting_issue` when an existing issue gets materially worse
- `record_confirmed_regression` when the evidence chain supports a new
  agent-caused fault

## Policy Shape

The decision engine should be policy-driven, not free-form.

Policy inputs can include:

- minimum confidence thresholds
- gate severity thresholds
- traceability completeness checks
- memory repetition checks
- override rules for known environment noise
- escalation rules for mixed or conflicting evidence
- owner routing rules for the relevant engineering domain
- corrective-action templates for recurring failure modes
- verification-playbook templates for high-risk or ambiguous evidence

Policy output should explain why a recommendation was chosen, not just which
category was returned.

## Recommendation Policy v2

Recommendation policy v2 is the richer product surface for the decision engine.

It should express four primary recommendation channels:

- `owner_routing` for assigning the follow-up work to the right team, owner, or
  reviewer
- `corrective_actions` for the concrete remediation steps that should follow the
  evidence
- `verification_playbook` for the checks that should be run to confirm the
  fix, narrow uncertainty, or validate a release candidate
- `escalation` for the cases that require manual review, higher authority, or a
  release hold

The recommendation policy should remain conservative. When evidence is mixed or
thin, the engine should prefer explicit escalation or verification over a
stronger recommendation than the evidence supports.

## Recordkeeping

Every decision should leave a durable trace.

The decision record should capture:

- what was decided
- why it was decided
- which inputs were used
- whether the decision came from a strong or weak evidence chain
- which owner was routed
- which corrective actions were recommended
- which verification playbook was selected
- whether escalation was triggered
- what follow-up work is required
- which memory record was written

This record should support later review in the CLI, report exports, and any
future UI.

## Roadmap

### Phase 1: Decision Engine Spec

- define the decision context schema
- define the decision result schema
- align category names with classifier and gate terminology
- define evidence requirements for each category

### Phase 2: Rule-Based Core

- implement deterministic category selection
- add confidence and policy threshold handling
- connect to classifier, gate, traceability, and memory inputs
- emit audit-friendly rationale text

### Phase 3: Memory-Aware Decisions

- compare new runs with prior decisions
- detect repeated environment or coverage patterns
- capture decision history for recurring change families

### Phase 4: Traceability-Driven Escalation

- use traceability gaps to force review or more verification
- surface missing links between change, requirement, test, and failure
- prefer explicit uncertainty over overconfident conclusions

### Phase 5: Operational Integration

- attach decision records to local reports
- expose a CLI command for decision evaluation
- persist decision history into the engineering memory ledger
- support downstream use by release review or future automation

## Non-Goals

- Do not turn the decision engine into a general-purpose agent planner.
- Do not let it override evidence with intuition.
- Do not use it as a replacement for the classifier or gate.
- Do not weaken conservative uncertainty handling in favor of decisive language.

## Working Principle

The decision engine should be explainable, deterministic, and conservative.

When the evidence is strong, it should say so clearly.
When the evidence is weak, it should leave room for more verification.
When the evidence is mixed, it should preserve the ambiguity instead of forcing a
false certainty.
