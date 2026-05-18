# AVERA Adapted Pilot Script (10 Minutes)

**Date:** 2 May 2026  
**Audience:** First pilot conversation around adapted evidence  
**Goal:** Show that AVERA can normalize different external artifact families into one stable review flow

## 0:00-1:00 - Frame

Say:

`AVERA is an evidence-first review layer. The important thing in this session is that the review engine stays the same even when the upstream artifacts change.`

## 1:00-3:00 - Canonical Baseline

Start with:

- `bms-fast-charge`

Show:

- verdict
- risk
- confidence
- release decision

Message:

`This is the stable review engine we already trust locally.`

## 3:00-5:00 - Adapted ADAS Simulation Path

Switch to:

- `adas-simulation-adapted`

Show:

- raw simulation CSV artifacts
- normalized `baseline_results.json` / `current_results.json`
- the same report / traceability / decision path

Message:

`External simulation evidence is adapted before review. The review kernel itself does not change.`

## 5:00-7:00 - Adapted BMS Requirements Path

Switch to:

- `bms-requirements-adapted`

Show:

- raw requirements export variant
- normalized `requirements.csv`
- the same requirement impact and release review path

Message:

`Upstream requirements variety is absorbed before the normal AVERA analysis begins.`

## 7:00-8:30 - Adapted BMS Log Path

Switch to:

- `bms-log-adapted`

Show:

- raw verification log CSV
- normalized verification JSON
- the same decision and handoff path

Message:

`Log-heavy evidence can still be normalized into the same review contract.`

## 8:30-10:00 - Close To Pilot

Ask:

1. which of these artifact families is closest to your current workflow?
2. where would you want the raw-to-normalized boundary to stay visible?
3. what would be the narrowest pilot worth trying first?

Close with:

`The next step is one narrow pilot on one artifact family, not a broad platform rollout.`
