"""Fake ports for REC1b's tests: each answers what it is given, or fails like a real unreadable input."""

from dataclasses import dataclass, field
from datetime import date, datetime

from fno.recommend.constants import CandidateSourceName, SourceState
from fno.recommend.contracts import CandidateSource
from fno.recommend.ports import (
    CandidateSourcePort,
    ConditionsPort,
    DayConditions,
    EligibilityPort,
    EvidencePort,
    InputFailed,
    SeenDecision,
    SourceReading,
)
from fno.recommend.refs import RecordRef
from fno.recommend.rungs import EvidenceReports, ForwardOutcome
from tests.recommend.builders import sha

CLEAR = DayConditions(False, False, False, (RecordRef("journal/runs/2026-11-02.json", sha(30)),))


def seen(version: str, traded: bool = False, n: int = 40, road: str = "") -> SeenDecision:
    return SeenDecision(version, RecordRef(f"decisions/{version}{road}.json", sha(n)), traded)


@dataclass
class FakeSource(CandidateSourcePort):
    name: CandidateSourceName
    decisions: tuple[SeenDecision, ...] = ()
    status: str | None = None  # a step status: the source is unavailable
    fails: str = ""

    def read(self, day: date) -> SourceReading:
        if self.fails:
            raise InputFailed(self.fails)
        state = SourceState.UNAVAILABLE if self.status else SourceState.COMPLETE
        used = (RecordRef(f"{self.name}/{day}.json", sha(50)),)
        return SourceReading(CandidateSource(self.name, state, self.status),
                             () if self.status else self.decisions, used)  # fmt: skip


@dataclass
class FakeEvidence(EvidencePort):
    rated: tuple[str, ...] = ()
    history: tuple[ForwardOutcome, ...] = ()
    passed: dict = field(default_factory=dict)
    fails: str = ""

    def versions(self, day: date) -> tuple[str, ...]:
        if self.fails:
            raise InputFailed(self.fails)
        return self.rated

    def outcomes(self, day: date, made_at: datetime) -> tuple[ForwardOutcome, ...]:
        return self.history

    def reports(self, version: str) -> EvidenceReports:
        return self.passed.get(version, EvidenceReports())


@dataclass
class FakeConditions(ConditionsPort):
    found: DayConditions = CLEAR
    fails: str = ""

    def conditions(self, day: date) -> DayConditions:
        if self.fails:
            raise InputFailed(self.fails)
        return self.found


@dataclass
class FakeEligibility(EligibilityPort):
    names: frozenset = frozenset()

    def eligible(self, day: date) -> frozenset[str]:
        return self.names
