# Reddit post — ready to paste (framed as a finding, not an ad)

> Big dev subreddits auto-remove promo. So this is posted as a **finding/question**,
> not a launch. Lead with the result; put the repo link in the FIRST COMMENT, not
> the post body. Best fit: r/devops or r/QualityAssurance. Build a little comment
> karma first if the account is brand new.

## Title

```
I blind-tested whether a "regression gate" catches a real reverted bug — and it surfaced an honest limitation
```

## Body (text post, no link)

```
A passing test suite only proves no existing test failed — not that nothing
regressed. I wanted to know how well a deterministic baseline-vs-current diff
actually catches *introduced* failures, so I ran a blind test on real OSS history.

Method: take a real commit that was later reverted (so it provably broke
something), reconstruct the before/after test results, and feed ONLY those two
result sets to the checker — no hint where the bug is. It has to independently say
"this change introduced a regression".

On toolz commit f0831e7 it worked: it flagged the exact test that went pass->fail
and blocked. But the honest part is the limitation it exposed — historically that
bug slipped past the project's own CI because no test expressed it yet. So the
checker only catches a regression once a test exercises it (same scope as your own
suite); it does NOT catch a regression no test touches, and it doesn't decide
flaky-vs-real.

Two questions for this sub:
1. How do you currently tell "a real introduced regression" apart from "a flaky red
   / a new test that's just failing" in CI? Manually, or is something automating it?
2. For the regressions that slip past your suite entirely — is anyone using
   mutation testing or similar in CI, or is it too slow to be practical?

(I've been building a small deterministic tool around this idea — happy to drop the
repo + the reproducible benchmark in a comment if that's allowed here.)
```

## First comment (only if the post survives / someone asks)

```
Repo + the one-command reproducible benchmark (you can run the toolz case
yourself): https://github.com/tc7kxsszs5-cloud/avera — it's local-first and
deterministic, no LLM in the decision. Writeup with the reasoning:
https://dev.to/mikheil_galoian_da78478f9/green-ci-proves-nothing-failed-heres-a-deterministic-check-that-proves-nothing-regressed-14g3
```
