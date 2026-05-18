# AVERA Adapted Pilot Bundle

**Date:** 2 May 2026  
**Status:** Design-partner-ready adapted scenario bundle  
**Purpose:** Present the current adapted-evidence capabilities as one coherent pilot set instead of three disconnected scenarios

## Bundle Definition

This bundle groups the three adapted AVERA scenarios that prove external
artifacts can be normalized into the stable local review contract:

1. `adas-simulation-adapted`
2. `bms-requirements-adapted`
3. `bms-log-adapted`

## What This Bundle Proves

Together, these scenarios prove that AVERA can keep one stable kernel while
accepting different upstream artifact families:

- simulation CSV
- richer requirements export
- richer verification log CSV

## Recommended Showing Order

1. canonical `bms-fast-charge`
2. `adas-simulation-adapted`
3. `bms-requirements-adapted`
4. `bms-log-adapted`

This order moves from:

- familiar canonical story
- to cross-domain adapted evidence
- to upstream requirements normalization
- to log-heavy verification normalization

## Shell Behavior

The demo shell now exposes this set as:

- `Scenario Set -> Adapted`

That keeps the pilot-facing scenarios grouped together for showing and review.

## Operator Message

Use one sentence repeatedly:

`The adapters normalize external artifacts into a stable AVERA workspace, but the review engine stays the same.`

## Entry Documents

Use these together:

- [AVERA_ADAPTED_EVIDENCE_PILOT_PACKET.md](/Users/mac/Desktop/AVERA/docs/AVERA_ADAPTED_EVIDENCE_PILOT_PACKET.md)
- [AVERA_ADAPTED_EVIDENCE_RUNBOOK.md](/Users/mac/Desktop/AVERA/docs/AVERA_ADAPTED_EVIDENCE_RUNBOOK.md)
- [AVERA_EXTERNAL_DEMO_FLOW.md](/Users/mac/Desktop/AVERA/docs/AVERA_EXTERNAL_DEMO_FLOW.md)
