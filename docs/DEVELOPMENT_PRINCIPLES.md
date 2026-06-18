# AVERA — Development Principles

AVERA is a tool that issues a **verdict about someone else's code** and is then
cited as **evidence** in a release decision. For this class of tool, value comes
from *trust*, not features. These principles are the standing doctrine: every
change to the core is measured against them. They are deliberately few and
opinionated.

## 1. Fail-closed by default

A gate that decides "ship / don't ship" must, on any malformed, unknown, or
ambiguous input, **stop — never pass**. The two failure modes are not symmetric:

- A **false pass** (a real regression let through) destroys trust permanently.
- A **false block** (a clean change stopped) is annoying and recoverable.

So the bias is always toward safety. Unknown risk → maximum severity. Non-finite
confidence → review. Unrecognised status token → treated as failure. This is not
over-caution; it is the only correct asymmetry for a safety gate.

## 2. Specification before code

A new core rule begins as a **precise definition and a checkable property**, then
an implementation that conforms — not as an `if` added to a chain. The verdict
function is the reference: it is a total decision table
(`classify/verdict_spec.py`) proven over its entire input space
(`tests/test_verdict_specification.py`). "Proven" — enumerated and shown total,
consistent, and safe — replaces "seems to work."

The K3 hole existed because a rule's ordering had a gap no example test hit. A
specification closes that whole class of bug; examples cannot.

## 3. Determinism and reproducibility in the decision path

Same inputs → same verdict → same `integrity_root`, on any machine, forever.
Nothing in the **decision path** may be non-deterministic or non-reproducible.
In particular: **no LLM in the gate.** AI may help a human *interpret* evidence;
it never *decides* the release. Every artifact stays inspectable JSON.

## 4. Adversarial verification

The standard is not "we tested it" but "we tried to break it and could not."
Load-bearing invariants get an independent attacker with a runnable repro. Found
holes become tracked rows with a severity and a fix or a dated plan
(`AVERA_ADVERSARIAL_HARDENING.md`). Defensible means **audited and transparent**,
not assumed perfect.

## 5. Honest scope — state what is *not* guaranteed

A defensible tool says plainly where its guarantees end. AVERA formalises the
**deterministic evidence-classification** layer. It does **not** yet resolve the
genuinely **statistical** questions — is one timeout flaky infra or a real
slowdown? is a metric move signal or noise? Those need repeated measurement and
significance testing and are named as open, not papered over. No overclaiming.

## 6. Tool-qualification posture (regulated domains)

In ISO 26262 (-8, Tool Confidence Level) and DO-178C (via DO-330), the more a tool
is *trusted to decide unchecked*, the higher its qualification burden. AVERA is
designed to keep that burden low: its output is **independently re-checkable by a
human** (inspectable manifest, hash-chained audit, re-derivable integrity root).
It is a **verification aid whose conclusions can be audited**, not an oracle to be
believed blindly. This is what makes its output acceptable to a safety reviewer —
and it is a design constraint, not a marketing line.

## 7. Minimal core — let rigor be *pulled*, not *pushed*

Once the core is strong, further hardening and formalisation hit diminishing
returns and can become perfectionism disguised as diligence — "building in a
mirror." The binding constraint then is **contact with reality**: a real project's
real history, a real practitioner trying to break the concept on their workflow,
a real audit. New rigor, new adapters, new domains should be **pulled by a
demonstrated need**, not pushed speculatively. The wedge (pass/fail CI + triage of
AI-generated PRs) is the minimal claim; regulated-domain depth is added when a
real case demands it.

---

**In one line:** for this kind of project, the right development posture is
fail-closed, specification-first, deterministic, adversarially-verified, and
honest about its limits — and past a certain point the next correct step is not
more internal rigor but a test against reality.
