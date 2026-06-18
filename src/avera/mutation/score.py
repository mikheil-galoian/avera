"""Score mutation results into a test-adequacy confidence signal.

Given which mutants were killed (a test failed) vs survived (all tests still
passed), compute a mutation score and a conservative verdict on whether the
changed region is actually verified by the tests.

A high survivor rate in changed code is a blind spot: the tests cannot detect a
fault there, so a green suite is **not** evidence the change is safe. This is the
non-test lens AVERA needs to catch regressions that slip past tests.
"""

from __future__ import annotations

from dataclasses import dataclass, field

MUTATION_CONFIDENCE_SCHEMA_VERSION = "avera.mutation_confidence.v0.1"

# Verdicts (deterministic thresholds on the mutation score).
VERIFIED = "verified"               # tests kill most injected faults
PARTIALLY_VERIFIED = "partially_verified"
UNVERIFIED = "unverified"           # tests miss most/all injected faults — blind spot
NO_MUTANTS = "no_mutants"           # nothing mutable in the region


@dataclass(frozen=True)
class MutationConfidence:
    schema_version: str
    total: int
    killed: int
    survived: int
    mutation_score: float            # killed / total, 0..1
    verdict: str
    survivors: list[str] = field(default_factory=list)  # descriptions of surviving mutants

    @property
    def is_blind_spot(self) -> bool:
        return self.verdict in (UNVERIFIED, PARTIALLY_VERIFIED)

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "total": self.total,
            "killed": self.killed,
            "survived": self.survived,
            "mutation_score": self.mutation_score,
            "verdict": self.verdict,
            "survivors": list(self.survivors),
        }


def _verdict(score: float, total: int) -> str:
    if total == 0:
        return NO_MUTANTS
    if score >= 0.8:
        return VERIFIED
    if score >= 0.5:
        return PARTIALLY_VERIFIED
    return UNVERIFIED


def mutation_confidence(
    killed_flags: list[bool],
    survivor_descriptions: list[str] | None = None,
) -> MutationConfidence:
    """Build a confidence result from per-mutant kill flags.

    Parameters
    ----------
    killed_flags:
        One bool per mutant — True if the test suite killed it (a test failed).
    survivor_descriptions:
        Optional human-readable descriptions of the surviving mutants.
    """
    total = len(killed_flags)
    killed = sum(1 for k in killed_flags if k)
    survived = total - killed
    score = round(killed / total, 4) if total else 0.0
    return MutationConfidence(
        schema_version=MUTATION_CONFIDENCE_SCHEMA_VERSION,
        total=total,
        killed=killed,
        survived=survived,
        mutation_score=score,
        verdict=_verdict(score, total),
        survivors=list(survivor_descriptions or []),
    )
