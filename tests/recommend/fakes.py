"""Fake ports for REC1b's tests: each answers what it is given, or fails like a real unreadable input."""

import hashlib
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
from fno.storage.raw_store import RawFileConflict
from fno.storage.receipt_publisher import PushedReceipt
from fno.storage.receipts import Receipt
from tests.recommend.builders import MADE_AT, sha

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


@dataclass
class FakeData:
    """O9's DataStore: write-once by path."""

    area: str = "data"
    files: dict = field(default_factory=dict)

    @property
    def drive(self) -> "FakeData":
        return self

    def get(self, drive_path: str) -> bytes | None:
        return self.files.get(drive_path.removeprefix(f"{self.area}/"))

    def put(self, path: str, data: bytes) -> Receipt:
        if self.files.get(path, data) != data:
            raise RawFileConflict(path)
        self.files[path] = data
        return Receipt(f"{self.area}/{path}", hashlib.sha256(data).hexdigest(), len(data), MADE_AT.isoformat(),
                       "test", "run")  # fmt: skip


@dataclass
class FakePublisher:
    """Commits and pushes a receipt for a file of `data`; `fails` refuses the push like a remote that said no."""

    data: FakeData
    pushed: dict = field(default_factory=dict)
    fails: bool = False

    def publish(self, drive_path: str, what: str) -> PushedReceipt:
        if self.fails:
            raise RuntimeError("push refused")
        file = self.data.files[drive_path.removeprefix(f"{self.data.area}/")]
        self.pushed[drive_path] = PushedReceipt("e" * 40, MADE_AT, hashlib.sha256(file).hexdigest())
        return self.pushed[drive_path]

    def published(self, drive_path: str) -> PushedReceipt | None:
        return self.pushed.get(drive_path)


@dataclass
class RecordingAlerts:
    lines: list = field(default_factory=list)

    def send(self, text: str) -> str:
        self.lines.append(text)
        return "alert sent to #fno-desk"
