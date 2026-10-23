"""The certifier (story DR1): reads every version of a session, checks its integrity (the bytes match the SHA-256
saved with them) and the dataset's checks for the level, lets the rules choose one version among those that pass and
writes the record. No version passing, or no choice, means no record and a named reason: a reader that needs the
record stops (owner, 23 Oct 2026: "We don't have to run the forecasting until we get a proper quality data")."""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from dataclasses import dataclass

from ..storage.raw_store import RawFileStore
from .constants import (
    ALREADY,
    CERTIFIED_LINE,
    CONFLICT,
    INTEGRITY,
    NO_VERSIONS,
    NONE_PASSED,
    NOT_CERTIFIED,
)
from .models import CheckResult, Record, Verdict
from .record_folder import RecordFolder
from .rules import DatasetRules
from .staging import VersionSource


@dataclass(frozen=True)
class Outcome:
    recorded: bool
    line: str
    record: Record | None = None


class Certifier:
    def __init__(self, rules: DatasetRules, versions: VersionSource, drive: RawFileStore, records: RecordFolder,
                 note: Callable[[str, Record], str] | None = None):  # fmt: skip
        """`drive`: reads each version by its path; `note`: an extra word for the line (the shadow's comparison)."""
        self.rules, self.versions, self.drive, self.records, self.note = rules, versions, drive, records, note

    def certify(self, session: str, level: str) -> Outcome:
        name = self.rules.name
        held = self.records.chosen(name, session, level)
        if held is not None:
            return Outcome(True, ALREADY.format(dataset=name, session=session, level=level, sha=held.sha256[:12]))
        verdicts, passing = [], []
        for version in self.versions.versions(session):
            data, problem = self._bytes(version)
            checks = self._checks(session, level, version.sha256, data, problem)
            verdicts.append(Verdict(version, tuple(checks)))
            if verdicts[-1].passed:
                passing.append((version, data))
        if not verdicts:
            return self._refused(session, level, NO_VERSIONS)
        if not passing:
            failures = "; ".join(f"{v.version.path.rsplit('/', 1)[-1]}: {v.failure()}" for v in verdicts)
            return self._refused(session, level, NONE_PASSED.format(failures=failures))
        choice = self.rules.choose(session, level, passing)
        if choice.version is None:
            return self._refused(session, level, choice.reason)
        record = Record(name, session, level, choice.version, choice.reason, self.rules.version, tuple(verdicts))
        return self._written(record, len(passing), len(verdicts))

    def _checks(self, session: str, level: str, sha256: str, data: bytes | None, problem: str) -> list[CheckResult]:
        if data is None:
            return [CheckResult(INTEGRITY, False, problem)]
        if hashlib.sha256(data).hexdigest() != sha256:
            return [CheckResult(INTEGRITY, False, "bytes differ from their receipt")]
        return [CheckResult(INTEGRITY, True), *self.rules.checks(session, level, data)]

    def _bytes(self, version) -> tuple[bytes | None, str]:
        try:
            data = self.drive.get(version.path)
        except Exception as failure:  # noqa: BLE001 - an unreadable version fails its integrity check, never the run
            return None, f"unreadable ({type(failure).__name__})"
        return data, "" if data is not None else "not in Drive"

    def _written(self, record: Record, passed: int, total: int) -> Outcome:
        name, session, level, sha = record.dataset, record.session, record.level, record.chosen.sha256
        held = self.records.write(record)
        if held is None or held.sha256 != sha:
            got = held.sha256[:12] if held else "nothing"
            line = CONFLICT.format(dataset=name, session=session, level=level, held=got, sha=sha[:12])
            return Outcome(False, line, record)
        reason = record.reason + (f"; {self.note(session, record)}" if self.note else "")
        line = CERTIFIED_LINE.format(dataset=name, session=session, level=level, sha=sha[:12], passed=passed,
                                     total=total, reason=reason)  # fmt: skip
        return Outcome(True, line, record)

    def _refused(self, session: str, level: str, reason: str) -> Outcome:
        line = NOT_CERTIFIED.format(dataset=self.rules.name, session=session, level=level, reason=reason)
        return Outcome(False, line)
