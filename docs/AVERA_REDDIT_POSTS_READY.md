# AVERA Reddit Posts — Ready to Publish

**Date:** 20 May 2026  
**Status:** Ready to copy-paste  
**Order:** Post one per day, starting with r/embedded

---

## POST 1 — r/embedded
**URL:** https://www.reddit.com/r/embedded/submit

**Title:**
```
We built a local tool that turns verification artifacts into a structured release-review path — curious how your teams handle this today
```

**Text:**
```
The problem we kept running into: when a software change touches safety-relevant functions, assembling the evidence trail for release review is manual and fragmented. Engineers collect test logs, JUnit/xUnit reports, simulation outputs, and requirement traceability data from different tools — then manually format it into something a reviewer can trust.

We built AVERA to automate that assembly. It normalizes verification log CSV, JUnit/xUnit XML, simulation CSV, and requirements exports into one structured, traceable evidence pack per change — with a SHA-256 audit chain. No toolchain changes, runs fully local.

Currently supports ISO 26262 (automotive), DO-178C (aviation), EN 50128 (railway), IEC 62304 (medical devices).

Live demo: https://avera-production.up.railway.app

I'm genuinely curious how teams here handle this today:
- What artifact exports do you rely on for regression triage or release review?
- Where does the trust break down?
- If you could fix one part of that workflow, what would it be?

Not selling anything — looking for engineers who want to tell us where this breaks in the field.
```

---

## POST 2 — r/softwaretesting
**URL:** https://www.reddit.com/r/softwaretesting/submit

**Title:**
```
How do you assemble verification evidence for a safety-critical release review? We built a tool to automate it — curious what breaks for others
```

**Text:**
```
Background: in safety-critical domains (automotive, aviation, railway, medical), every software change needs a traceable evidence pack before release — test logs, pass/fail deltas vs. baseline, simulation results, requirement coverage proof.

Most teams we've talked to do this manually. It takes hours per change, and the trust problem is real: reviewers get inconsistent artifacts with no chain of custody.

We built AVERA to fix that. It ingests your existing exports (verification log CSV, JUnit/xUnit XML, simulation CSV, requirements export) and normalizes them into one structured evidence pack per change, with a SHA-256 audit chain.

Standards covered: ISO 26262, DO-178C, EN 50128, IEC 62304.

Live demo: https://avera-production.up.railway.app

Questions for the community:
- How do you currently trace a failing test back to a requirement for a release reviewer?
- Do you have a standard format for regression evidence, or is it ad-hoc per team?
- What would make you trust automated evidence assembly?
```

---

## POST 3 — r/automotive
**URL:** https://www.reddit.com/r/automotive/submit

**Title:**
```
We built a local verification evidence tool for ISO 26262 software changes — live demo inside, looking for feedback from ADAS/BMS teams
```

**Text:**
```
If you work on automotive software (ADAS, BMS, ECU) and have gone through an ISO 26262 release review, you know the pain: collecting test logs, simulation outputs, traceability matrices, and pass/fail deltas from different tools and manually assembling them into something a safety reviewer can trust.

We built AVERA to automate that evidence assembly. It takes your existing artifact exports and normalizes them into one structured, traceable evidence pack per software change — with SHA-256 hash-chained audit log, regression triage, and requirement coverage proof.

Demo scenarios include:
- BMS fast-charge thermal regression (ASIL-B)
- ADAS pedestrian detection simulation delta
- Requirement coverage proof with traceability chain

Live demo: https://avera-production.up.railway.app

We're looking for Tier 1/Tier 2 teams who want to run a narrow 2-week pilot with one artifact family they already export. No infrastructure changes, no process disruption.

If you've dealt with this problem, I'd love to hear what the worst part of your current workflow is.
```

---

## POST 4 — r/aviationmaintenance / r/aerospace
**URL:** https://www.reddit.com/r/aerospace/submit

**Title:**
```
Built a DO-178C evidence pack tool for avionics software changes — looking for feedback from anyone who's done a DER review
```

**Text:**
```
Anyone who's prepared a DER review package for avionics software knows the artifact assembly problem: test logs, JUnit/xUnit reports, simulation outputs, and requirement traceability data all come from different tools, then someone manually formats it into an evidence pack the DER can trust.

We built AVERA to automate that. It normalizes your existing artifact exports into one structured, traceable evidence pack per software change — baseline vs. current comparison, pass/fail delta, requirement coverage proof, SHA-256 audit log.

One of our demo scenarios is a FADEC overspeed regression with a full DO-178C evidence pack: https://avera-production.up.railway.app

Questions:
- What artifact formats does your team actually export for DO-178C evidence? (test reports, simulation logs, DOORS exports?)
- Where does the manual assembly take the most time?
- Has a DER ever rejected evidence because of format/traceability issues rather than actual test failures?

Looking for avionics teams who want to run a 2-week pilot with one artifact family. No toolchain changes required.
```

---

## Posting Schedule

| Day | Subreddit | Expected audience |
|-----|-----------|-------------------|
| Today | r/embedded | Embedded/safety engineers |
| Day 2 | r/softwaretesting | QA/verification leads |
| Day 3 | r/automotive | ADAS/BMS teams |
| Day 4 | r/aerospace | Avionics/DO-178C |

## After Each Post

1. Check replies within 24h
2. If someone asks a real workflow question → reply with a follow-up question (never pitch first)
3. If someone shows pain → log in `AVERA_PILOT_CONTACT_TRACKER_V0.md`
4. If someone asks for a demo → send: https://avera-production.up.railway.app
