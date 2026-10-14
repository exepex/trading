"""The confirmatory family of protocol v4 (PROTOCOL_v4.md section 5): cumulative Holm over the 15 registered members at
each of at most two looks, with p = 1 for every member not judged at that look (ChatGPT review 98's caveat).

A member is judged at a look only when its slot has a registered forecaster, it has at least 2L scored pairs and it was
not closed earlier (a claim or a futility "no" at look 1 is final). Every decision states the look, its family-wise
rate, its timestamp and all 15 members, judged or not. Holm is written here, not imported from G4's unfrozen module,
so v4's freeze covers every line its decisions depend on.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime

from ..constants import V4_CLAIM, V4_FUTILE, V4_OPEN, V4_TOO_SMALL
from .terms import FAMILY, LOOK_ERROR_RATE

NOT_JUDGED_P = 1.0


@dataclass(frozen=True)
class MemberResult:
    """One member's statistics at a look. `p_value` None: not judged at this look (no registered forecaster, fewer
    than 2L pairs, or closed at an earlier look)."""

    p_value: float | None
    meets_minimum_effect: bool
    futile: bool


@dataclass(frozen=True)
class MemberVerdict:
    question: str
    slot: str
    judged: bool
    p_used: float  # the p-value Holm saw: NOT_JUDGED_P when not judged
    holm_significant: bool
    futile: bool  # judged, and the upper bound of its improvement is below the minimum effect
    verdict: str  # V4_CLAIM, V4_TOO_SMALL (significant, below the effect), V4_FUTILE or V4_OPEN


@dataclass(frozen=True)
class FamilyDecision:
    look: str
    error_rate: float
    decided_at: datetime
    members: tuple[MemberVerdict, ...]  # all of FAMILY, in its order

    def header(self) -> str:
        judged = sum(m.judged for m in self.members)
        return (
            f"protocol v4 family: {len(self.members)} members, {judged} judged, "
            f"{len(self.members) - judged} at p = 1; "
            f"look {self.look} at family-wise {self.error_rate:g}; decided at {self.decided_at.isoformat()}"
        )

    def lines(self) -> list[str]:
        """The header, then every member (judged or not): what each report prints, so membership is never implied."""
        rows = [
            f"{m.question} {m.slot}: p {m.p_used:.4f}{'' if m.judged else ' (not judged)'}, {m.verdict}"
            for m in self.members
        ]
        return [self.header(), *rows]


def holm(p_values: Sequence[float], rate: float) -> list[bool]:
    """Holm's step-down: sorted ascending, the i-th (1-based) is significant while p <= rate / (m - i + 1)."""
    m = len(p_values)
    significant = [False] * m
    for rank, i in enumerate(sorted(range(m), key=lambda j: p_values[j]), start=1):
        if p_values[i] > rate / (m - rank + 1):
            break
        significant[i] = True
    return significant


def judge_family(look: str, decided_at: datetime, results: Mapping[tuple[str, str], MemberResult]) -> FamilyDecision:
    """Every member of FAMILY is in the decision; a member missing from `results` is not judged (p = 1)."""
    if decided_at.tzinfo is None:
        raise ValueError("a decision timestamp needs its time zone")
    unknown = set(results) - set(FAMILY)
    if unknown:
        raise ValueError(f"not members of the registered family: {sorted(unknown)}")
    rate = LOOK_ERROR_RATE[look]
    stats = [results.get(member) for member in FAMILY]
    p_used = [s.p_value if s is not None and s.p_value is not None else NOT_JUDGED_P for s in stats]
    significant = holm(p_used, rate)
    members = tuple(
        _verdict(member, stat, p, sig) for member, stat, p, sig in zip(FAMILY, stats, p_used, significant, strict=True)
    )
    return FamilyDecision(look, rate, decided_at, members)


def _verdict(member: tuple[str, str], stat: MemberResult | None, p: float, significant: bool) -> MemberVerdict:
    judged = stat is not None and stat.p_value is not None
    if judged and significant:
        verdict = V4_CLAIM if stat.meets_minimum_effect else V4_TOO_SMALL
    elif judged and stat.futile:
        verdict = V4_FUTILE
    else:
        verdict = V4_OPEN
    return MemberVerdict(member[0], member[1], judged, p, judged and significant, judged and stat.futile, verdict)
