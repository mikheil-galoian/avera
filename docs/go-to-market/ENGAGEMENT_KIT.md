# Engagement kit — honest, ready replies

When someone responds on HN / dev.to / Reddit, the channel only "closes" if the
reply is fast, honest, and non-defensive. Below are ready answers to the questions
that actually come up. Keep the tone the same everywhere: state the limit before
the strength. This audience rewards honesty and punishes spin.

## The 2-minute "try it on your repo" recipe (paste when someone's interested)

```
git clone https://github.com/tc7kxsszs5-cloud/avera && cd avera
pip install -e .
# produce two JUnit files from your own project (any tool that emits JUnit):
#   pytest --junitxml=current.xml      (jest --reporters=jest-junit, gotestsum --junitfile=..., etc.)
# and one from a known-good ref as baseline.xml, then:
avera check --baseline baseline.xml --current current.xml --report-only
```
`--report-only` = advisory: it prints the verdict but never fails your build — so a
flaky test that flips can't cost you anything on the first try. Drop the flag for
the hard gate once you trust it. How to get the baseline in CI:
docs/CI_BASELINE_PATTERN.md.

**The outreach framing that follows from this:** ask people to *try to break it*
in `--report-only` mode and show you where it misfires — a misfire (esp. on a
flaky test) is the most useful reply, not an embarrassment. It tells you exactly
what to build next.

## Likely questions → honest answers

**"Isn't this just what my test suite already does?"**
The suite tells you a test is red. It does not tell you *this change* turned it red
vs it was already red vs it's a brand-new test vs flake. AVERA's job is that
separation — only baseline-pass / current-fail is flagged as an introduced
regression — plus a tamper-evident record of why the merge was allowed.

**"How is it different from required CI checks / branch protection?"**
Required checks block on *any* red. AVERA blocks specifically on a *proven introduced*
regression and is deterministic + reproducible (same inputs → same verdict → same
evidence hash), with an audit trail. It's the "why" behind the gate, not just a
red/green.

**"What about flaky tests?"**
Honest answer: it does **not** decide flaky-vs-real today — that stays a human call.
On a single diff, a flaky test flipping pass→fail looks like a real regression. So
for a first trial use `--report-only` (advisory — never fails the build); you see
the verdict without a false block. Solving flaky-vs-real properly is the #1 thing
I want to do next, and the right way is statistical (repeated runs + significance),
not an LLM guessing. I'd rather say "I don't know yet" than fake it.

**"Is this another AI PR reviewer?"**
No — and deliberately so. There is **no LLM in the decision**. It's a deterministic
diff + gate. AI agents are what *create* the problem (PR flood); the value here is
being the trustworthy non-AI check. (AI may later help *explain* a verdict, never
make it.)

**"Does it work with my stack?"**
If it emits JUnit/xUnit XML, yes — pytest, jest (jest-junit), go (gotestsum /
go-junit-report), JUnit, etc. Verified on pytest, jest, and go output
(tests/test_format_breadth.py). Other formats via an adapter.

**"Does my code leave the machine?"**
No. Local-first, nothing is uploaded, no LLM call in the path.

**"What does it NOT do?"** (lead with this if it comes up)
It won't catch a regression no test exercises (that's mutation analysis), won't
decide flaky-vs-real, and won't decide your release — it produces auditable
evidence; a human signs off. It is not a certified/qualified tool.

**"It missed a regression in my repo."**
That's the most valuable reply I can get — please share the case (the two JUnit
files if you can). The benchmark is built to grow on exactly those, and a miss is a
real finding, not an embarrassment.

## Rule
Never overclaim to win a thread. A conceded limit earns more trust here than a
defended exaggeration — and trust is the whole product.
