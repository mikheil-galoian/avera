#!/usr/bin/env python3
"""Blind-replay harness — prove (or falsify) AVERA on a real revert from a real repo.

Given a public repo and a merged ``Revert "..."`` commit, this reconstructs the
regression and runs AVERA *blind* on the result diff:

  good state   = the revert applied      (bug fixed)        -> baseline tests
  current state = revert undone           (bug re-applied)   -> current tests

AVERA receives ONLY the two JUnit result sets — never the bad commit, never where
the bug is. It must independently decide ``confirmed_regression`` + ``block``.

This is a falsification engine, not a demo: the most valuable outcome is a case
where AVERA *fails* to catch a real regression — that is a true finding to fix.
Two regression kinds exist and both are recorded honestly:
  - test flips pass->fail at the bad code  -> AVERA can catch from results alone.
  - regression slips past the existing tests (0 new failures) -> NOT catchable
    from results; this is the mutation-lens's territory, recorded as 'slipped'.

Usage:
  python scripts/blind_replay.py <repo_url> <revert_commit_sha>
      [--tests <pytest target>] [--runner <python>] [--corpus <path.jsonl>]

Notes:
  * Runs a third-party test suite = arbitrary code execution. Run only on repos
    you trust, ideally sandboxed.
  * Defaults assume a pip-installable / zero-dep pure-Python lib whose suite runs
    under the runner's pytest. Repos that won't set up are logged and skipped.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

_AVERA_SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(_AVERA_SRC))


def _sh(cmd: list[str], cwd: Path | None = None, ok=(0,)) -> subprocess.CompletedProcess:
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if r.returncode not in ok:
        raise RuntimeError(f"cmd failed ({r.returncode}): {' '.join(cmd)}\n{r.stderr[-800:]}")
    return r


def _avera_blind(baseline_xml: Path, current_xml: Path) -> dict:
    """Run the AVERA pipeline on two JUnit files and return a result summary."""
    from avera.adapters import adapt_junit_xml
    from avera.compare.baseline_comparator import compare_runs
    from avera.classify.risk_classifier import classify_risk
    from avera.core import assessment_to_public_report
    from avera.gates.policy import evaluate_gate
    from avera.gates.policy_loader import load_builtin_policy

    base = adapt_junit_xml(str(baseline_xml), run_id="replay-base", stage="baseline")
    curr = adapt_junit_xml(str(current_xml), run_id="replay-curr", stage="current")
    a = classify_risk(comparison=compare_runs(baseline=base, current=curr))
    report = assessment_to_public_report(a)

    def tid(x):
        return getattr(x, "test_id", None) or getattr(x, "id", None)

    gates = {}
    for name in ("general", "automotive", "aviation", "medical", "railway"):
        try:
            g = evaluate_gate(report, policy=load_builtin_policy(name))
            gates[name] = getattr(g, "status", None) or getattr(g, "decision", None)
        except Exception as exc:  # policy missing in a checkout, etc.
            gates[name] = f"error:{exc}"
    return {
        "baseline_count": len(base["tests"]),
        "current_count": len(curr["tests"]),
        "verdict": a.verdict,
        "risk": a.risk,
        "confidence": a.confidence,
        "confidence_score": round(a.confidence_score, 3),
        "introduced": [tid(x) for x in a.introduced_failures],
        "gates": gates,
    }


def replay(repo_url: str, revert_sha: str, *, tests: str, runner: str, good_ref: str | None = None) -> dict:
    bad_re = re.compile(r"This reverts commit ([0-9a-f]{7,40})", re.I)
    # The baseline ("good") state defaults to the revert commit itself — this
    # reproduces the project's HISTORICAL test coverage at that moment ("did
    # their own tests catch it?"). Pass --good <merge-or-fix-sha> to baseline on
    # a state that already includes the regression test ("does AVERA block once
    # a test expresses the bug?"). Both framings are honest and recorded.
    base_ref = good_ref or revert_sha
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td) / "repo"
        _sh(["git", "clone", "-q", repo_url, str(repo)])
        body = _sh(["git", "show", "-s", "--format=%B", revert_sha], cwd=repo).stdout
        m = bad_re.search(body)
        bad = m.group(1) if m else None

        # baseline = good state
        _sh(["git", "checkout", "-q", base_ref], cwd=repo)
        base_xml = Path(td) / "baseline.xml"
        b = subprocess.run([runner, "-m", "pytest", tests, "-q", f"--junitxml={base_xml}",
                            "-p", "no:cacheprovider"], cwd=repo, capture_output=True, text=True)
        if not base_xml.exists():
            raise RuntimeError(f"baseline tests did not run:\n{b.stdout[-600:]}\n{b.stderr[-400:]}")

        # current = bad state (undo the revert -> reintroduce the regression)
        _sh(["git", "revert", "--no-edit", revert_sha], cwd=repo)
        curr_xml = Path(td) / "current.xml"
        subprocess.run([runner, "-m", "pytest", tests, "-q", f"--junitxml={curr_xml}",
                        "-p", "no:cacheprovider"], cwd=repo, capture_output=True, text=True)
        if not curr_xml.exists():
            raise RuntimeError("current tests did not run")

        res = _avera_blind(base_xml, curr_xml)

    # Classify the case honestly.
    if res["introduced"]:
        outcome = "caught" if res["verdict"] == "confirmed_regression" and \
            any(v == "block" for v in res["gates"].values()) else "missed"
    else:
        outcome = "slipped"  # no test expressed the regression — not result-catchable
    return {
        "repo": repo_url, "revert": revert_sha, "bad_commit": bad,
        "baseline_ref": base_ref, "tests": tests, "outcome": outcome, **res,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("repo_url")
    ap.add_argument("revert_sha")
    ap.add_argument("--tests", default="")
    ap.add_argument("--good", default=None, help="baseline ref (default: the revert commit)")
    ap.add_argument("--runner", default=sys.executable)
    ap.add_argument("--corpus", default=str(Path(__file__).resolve().parents[1] / "reports" / "blind_corpus.jsonl"))
    args = ap.parse_args()
    try:
        rec = replay(args.repo_url, args.revert_sha, tests=args.tests, runner=args.runner, good_ref=args.good)
    except Exception as exc:
        rec = {"repo": args.repo_url, "revert": args.revert_sha, "outcome": "setup_failed", "error": str(exc)[:500]}

    print(json.dumps(rec, indent=2, ensure_ascii=False))
    corpus = Path(args.corpus)
    corpus.parent.mkdir(parents=True, exist_ok=True)
    with corpus.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"\n[corpus] appended → {corpus}")
    return 0 if rec.get("outcome") in {"caught", "slipped"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
