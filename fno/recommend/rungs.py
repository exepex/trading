"""The rung rule (story REC1a, `research/recommend/RUNG_RULE.md`): a version's evidence rung on day d from its
forward outcomes, point in time (judge 620 S2 and m2): a session counts only when it is before d, counted, from
forward paper trading, and GitHub's push receipt of its receipt reached `main` strictly before the decision. An
unknown receipt does not count (fails closed), so a doubt only lowers a rung."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime

from .constants import EvidenceRung, OutcomeSource

RUNG_RULE_PATH = "research/recommend/RUNG_RULE.md"
# The card's SHA-256, pinned to its bytes by tests/recommend/test_rung_rule_card.py; a record carries it
RUNG_RULE_SHA256 = "ba2f079a2a7d3eb0e8452b125227a7ad2b59855fad2bf950a692a5540c70b7e5"
WATCHING_SESSIONS = 30
CALIBRATION_MIN_OUTCOMES = 100
CALIBRATION_MIN_SESSIONS = 60
CALIBRATION_BINS = 5
DAY_CONDITION_STEP = 1


@dataclass(frozen=True)
class ForwardOutcome:
    """One closed outcome of a version, as its sealed record and the counting rule give it."""

    version: str
    session: date
    source: OutcomeSource
    counted: bool  # the counting rule's verdict (MS-P1h `CountingRule`, or S1's order rule for the books)
    receipt_at: datetime | None  # GitHub's push receipt of its receipt commit; None: GitHub could not answer


@dataclass(frozen=True)
class EstablishedTest:
    """Rung 3's three conditions, each read from its own frozen report; all False until such a report exists."""

    sample_plan_met: bool = False
    lower_bound_above_zero: bool = False
    second_window_agrees: bool = False

    def passed(self) -> bool:
        return self.sample_plan_met and self.lower_bound_above_zero and self.second_window_agrees


@dataclass(frozen=True)
class VersionEvidence:
    """What a record shows per version, so a reader can recount it."""

    version: str
    rung: EvidenceRung
    counted_sessions: int
    first_session: date | None
    last_session: date | None


def counted_sessions(outcomes: Iterable[ForwardOutcome], version: str, day: date, made_at: datetime) -> list[date]:
    """The version's distinct sessions that count for a decision on `day` at `made_at`, oldest first."""
    return sorted({o.session for o in outcomes if o.version == version and _counts(o, day, made_at)})


def evidence(outcomes: Iterable[ForwardOutcome], version: str, day: date, made_at: datetime,
             review_done: bool, established: EstablishedTest) -> VersionEvidence:  # fmt: skip
    sessions = counted_sessions(outcomes, version, day, made_at)
    rung = rung_for(len(sessions), review_done, established)
    return VersionEvidence(version, rung, len(sessions), sessions[0] if sessions else None,
                           sessions[-1] if sessions else None)  # fmt: skip


def rung_for(sessions: int, review_done: bool, established: EstablishedTest) -> EvidenceRung:
    if sessions == 0:
        return EvidenceRung.UNPROVEN
    if sessions < WATCHING_SESSIONS or not review_done:
        return EvidenceRung.EXPLORATORY
    return EvidenceRung.ESTABLISHED if established.passed() else EvidenceRung.WATCHING


def lowered(rung: EvidenceRung, conditions: int) -> EvidenceRung:
    """The day's shown rung: one step down per true day condition, never below 0, never up."""
    return EvidenceRung(max(EvidenceRung.UNPROVEN, rung - DAY_CONDITION_STEP * max(conditions, 0)))


def calibration_shown(outcomes: int, sessions: int) -> bool:
    return outcomes >= CALIBRATION_MIN_OUTCOMES and sessions >= CALIBRATION_MIN_SESSIONS


def _counts(outcome: ForwardOutcome, day: date, made_at: datetime) -> bool:
    return (outcome.source is OutcomeSource.FORWARD and outcome.counted and outcome.session < day
            and outcome.receipt_at is not None and outcome.receipt_at < made_at)  # fmt: skip
