# AVERA — Project Roadmap (strategy-driven)

**Organizing principle:** the core is done; value is now gated not by features but by
two things — *adoption* and the *usefulness ceiling (flaky-vs-real)*. So the plan is
phased by **contact with reality**, and every technical step is **pulled by a demonstrated
need**, never pushed. The differentiation — deterministic verdict + evidence trail +
**no LLM in the decision** — is an **invariant across all phases**.

## Phase 0 — Defensible core ✅ DONE
19/19 adversarial holes closed, proven-total verdict spec, 6 domains, zero-config
`avera check` + GitHub Action, reproducible benchmark magnet, install path fixed,
first GTM launch (dev.to + Show HN + GitHub).

## Phase 1 — Drive activation to near-zero + get in front of real pain ⬅️ NOW
Goal: a stranger goes "curious → ran it on my repo" in <10 min, and we are in front of
the right people.
Concrete tasks (acceptance criteria):
- [x] **Install door works** — fresh `git clone` + `pip install -e .` + `avera check`
      verified in a clean venv.
- [x] **Baseline-in-CI pattern** — documented + a working example workflow
      (`docs/CI_BASELINE_PATTERN.md`, `examples/github-action-zero-config.yml`).
- [x] **Format breadth** — `avera check` verified on jest-style and go-style JUnit XML,
      not only pytest (`tests/test_format_breadth.py`).
- [ ] **Distribution discipline** — reply to any HN/dev.to engagement; send the 3 emails;
      Reddit as a *finding*, not an ad. (user's outward actions)
**EXIT GATE:** ≥1 real team/person runs `avera check` on their own repo and gives feedback.
**Do NOT:** new domains, AI layer, statistical layer — until there is a signal.

## Phase 2 — Solve the #1 everyday pain: flaky-vs-real (statistically)
*(pulled by Phase 1 feedback)*
Goal: lift everyday usefulness past the current ceiling.
Work: statistical flaky detection (repeated runs + significance test); confidence as a
calibrated probability validated on the benchmark data. **No AI — statistics.**
EXIT GATE: flaky/real separation works on real data; benchmark grows (needs sandbox).

## Phase 3 — AI advisory layer (around the core, never in it)
Goal: lower the human cost of acting on a verdict.
Work: root-cause / plain-language explanation on top of the already-deterministic
evidence; triage summary. Advisory, grounded, labeled, **never deciding**.
EXIT GATE: explanations are grounded (no hallucination), explicitly advisory.

## Phase 4 — Deepen a regulated beachhead (space/NASA or medical)
*(pulled by a real regulated contact)*
Work: structural-coverage gate (MC/DC), standards-clause traceability, the cFS entry.
Higher-value destination — after reputation is earned on the CI wedge.

## Invariants (hold on every phase)
1. **No LLM in the verdict.** Ever. It is the entire point.
2. **Fail-closed + specification-first** for any core change.
3. **Minimal-sufficient** — do not build "for the future".
4. **Agents for our own work** (research / review / drafting), never in the product decision.

## Branch point (critical, after Phase 1)
- **If** interested people actually run it and come back → build Phase 2. Pain = painkiller.
- **If** even interested people don't adopt → pain is vitamin-level. **STOP building** —
  change the angle (different segment / different packaging).

The next real step is not code — it is **Phase 1's exit gate** (one real run by an outside
team). Everything technical sits behind it.
