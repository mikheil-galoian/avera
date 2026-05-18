# Outreach Email — AI Safety Engineering Teams

**Template version:** 1.0  
**Date:** 8 May 2026  
**Target audience:** Engineers and technical leads implementing AI models in safety-critical systems  
**Ideal contacts:** Functional safety engineers, ADAS validation leads, AI/ML engineers in automotive/medical/industrial  
**Channels:** LinkedIn DM, direct email, conference follow-up

---

## Primary Template — Cold Outreach (LinkedIn / Email)

**Subject:** How do you prove an AI model update is safe before shipping?

---

Hi [Name],

I noticed you're working on [AI validation / ADAS safety / functional safety at Company] —
specifically the challenge of proving that an AI model update doesn't introduce a
safety-critical regression before it ships.

I've been working on exactly this problem. The core issue: teams have evaluation metrics,
but they don't have a proof chain that links those metrics to specific safety requirements,
assigns risk correctly, and produces a compliance-ready artifact.

I built something called AVERA — an open-source verification kernel that takes:
- your model's evaluation results (baseline vs. updated)
- your requirements (with ASIL/SIL levels and metric thresholds)
- a model card describing the change

...and produces a classified report with a verdict (`confirmed_regression` / `successful_change`),
evidence, and affected requirements — the same structure automotive teams already use for
traditional software changes.

The interesting property: zero modifications to the kernel were needed to handle AI model
changes. The same pipeline that detects a BMS voltage regression detects a detection_rate
regression in a YOLOv8 model. Because structurally they're the same problem.

I'm looking for 2–3 teams who would be willing to run it on a real model update scenario
and tell me where it breaks or doesn't fit their workflow. No commitment beyond that.

Would you be open to a 30-minute call to see if this maps to a problem you're actually facing?

Best,  
[Your name]

---

## Follow-up Template (after no response, 7 days later)

**Subject:** Re: How do you prove an AI model update is safe before shipping?

---

Hi [Name],

Following up briefly on my last message.

One concrete data point that might be relevant: we ran AVERA on an ADAS perception
model update — YOLOv8, int8 quantization, retrained on an expanded dataset.
The model evaluation showed 5 of 6 scenarios improved. But the night+rain pedestrian
detection rate fell from 0.97 to 0.94, violating a ≥ 0.95 threshold against
REQ-SAFETY-012 (ASIL-D).

AVERA detected this as `confirmed_regression`, `risk: release_blocking`, and produced
an evidence artifact linking the metric delta to the specific requirement, component,
and ASIL classification — in the format ISO 26262 Part 8 expects for change impact analysis.

This took 4 files (evaluation JSON + requirements CSV + component map + model card)
and a single CLI command. No infrastructure changes. No cloud dependency. Air-gapped.

If that's a problem you're solving — or one you expect to be forced to solve soon by
UNECE R156 or EU AI Act compliance timelines — I'd value your perspective.

[Your name]

---

## Short Version — Conference / Event Follow-up

**Subject:** AVERA — AI change verification, following our conversation at [Event]

---

Hi [Name],

Great to meet at [Event]. Following up on our conversation about proving AI model
update safety in regulated systems.

AVERA is the tool I mentioned — open-source kernel that runs on evaluation JSON +
requirements CSV and produces a classified, compliance-ready evidence report.

Quick start: `pip install avera` (coming this month) or clone https://github.com/averaeng/avera

If you want to run it on one of your own scenarios, I'd be happy to walk you through
the artifact format. 30 minutes is enough to see whether it fits.

[Your name]

---

## Prospect List — Priority Targets

### Tier 1 — Highest fit (direct pain, right timing)

| Company | Contact profile | Why now | Approach |
|---------|----------------|---------|----------|
| **TraceTronic** (Dresden) | Automotive test management engineers | Build tooling for automotive test workflows; know ISO 26262 deeply | Email → demo call |
| **ETAS** (Stuttgart) | Embedded tools engineers, Bosch ecosystem | AI integration in AUTOSAR-based toolchains; UNECE R156 pressure | LinkedIn → email |
| **dSPACE** (Paderborn) | Validation toolchain engineers | SIL/HIL for ADAS; already handle model-in-loop; need AI change proof | Conference or LinkedIn |
| **BTC Embedded Systems** | Safety verification specialists | Formal verification + testing; natural bridge to AI evidence | LinkedIn DM |

### Tier 2 — Strong fit, longer sales cycle

| Company | Contact profile | Why now | Approach |
|---------|----------------|---------|----------|
| **Continental** | ADAS platform / AI safety engineers | Building AI-enabled ADAS at scale; under WP.29 pressure | LinkedIn — target Principal/Staff engineers |
| **Bosch** (RBEI / CR/AE) | AI safety, autonomous systems | Active ASIL-D ADAS development; compliance team pressure | Partner through ETAS relationship |
| **ZF** | Active safety systems | L2+ ADAS + AI; compliance pressure from OEM customers | LinkedIn → warm intro preferred |
| **Aptiv** | ADAS software platforms | Significant AI validation investment | Conference relationship first |

### Tier 3 — Expansion markets (non-automotive)

| Company | Contact profile | Why now | Approach |
|---------|----------------|---------|----------|
| **Siemens Healthineers** | AI validation for medical imaging | FDA AI/ML-SaMD compliance is immediate pressure | Medical AI conference |
| **Philips Healthcare** | AI in diagnostic equipment | FDA Pre-Spec + EU AI Act | LinkedIn — target clinical AI leads |
| **GE Aviation** | AI for MRO / prognostics | DO-178C + neural network certification | Aviation safety conference |

---

## LinkedIn Search Strings

Use these to find the right contacts:

```
"ISO 26262" AND "ADAS" AND "validation"
"functional safety" AND "AI" AND "automotive"
"UNECE R156" AND "software update"
"AI/ML" AND "SaMD" AND "FDA"
"ASIL" AND "machine learning" AND ("regression" OR "verification")
"neural network certification" AND ("DO-178" OR "ARP4754")
```

---

## Objection Handling

**"We already have evaluation pipelines."**

> Evaluation pipelines run your metrics. AVERA classifies whether a metric delta
> constitutes a safety-critical regression and produces the evidence artifact that
> connects that verdict to your specific requirements. These are different problems.
> Evaluation tells you what happened. AVERA tells you what it means — in terms your
> compliance team can act on.

**"We handle this internally."**

> Most teams handle it manually — a safety engineer reviews the eval report, makes a
> judgment call, and writes a memo. AVERA makes that process deterministic, traceable,
> and reproducible across every model update. If your process is already that structured,
> it would be interesting to see how AVERA's output compares to what you're producing today.

**"We're not ready for another tool."**

> AVERA is a single Python function: `analyze(baseline, current, requirements, component_map)`.
> It runs on local files. No infrastructure. No accounts. No cloud. If you can run pytest,
> you can run AVERA. The integration question is just: can you export your evaluation
> results to JSON?

**"How does this handle [specific AI framework/tool]?"**

> Right now AVERA has a native evaluation format. Adapters for MLflow, W&B, and proprietary
> SIL harnesses are in the roadmap. In the short term, it takes about 30 lines to write
> a converter from any evaluation JSON format — and we'd be happy to build the adapter
> together during the design-partner phase.

---

*AVERA Outreach v1.0 — 8 May 2026*
