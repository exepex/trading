"""One session's instructor run (story MS-INS, part e): every trade and ticket closed that session attributed and
classified, with REF's and RC1's results on its road-slot; then every earlier classification still waiting (cause 11
before its expiry settled, or a modifier before the controls closed) checked again, and a changed one written as a new
record naming the old. Written write-once to the instructor's own files; a dry run writes nothing."""

import hashlib
from dataclasses import dataclass, replace
from datetime import date, timedelta

from ....models import IST
from ..attribution.attribute import attribute
from ..causes.classify import Classifier
from ..contracts import Attribution, Cause, Classification, HeldPath, Modifier
from ..ports import InstructorKind, InstructorStore
from ..reader import PathReader
from .controls import control_nets, controls_for

RECHECK_DAYS = 90  # how far back a waiting classification is checked again when no first counted session is set


@dataclass(frozen=True)
class SessionResult:
    session: date
    attributions: tuple[Attribution, ...]
    classifications: tuple[Classification, ...]  # this session's closed paths, then the corrections of earlier ones
    unreadable: tuple[date, ...]


def waiting(record: Classification) -> bool:
    """Its cause 11 or its modifier waited for data (cause 13 waits for MS-P1j, so it never triggers a re-check)."""
    return Cause.EXIT_WHIPSAW in record.not_testable or record.modifier == Modifier.NOT_TESTABLE


def record_sha256(record: Classification) -> str:
    return hashlib.sha256(record.to_bytes()).hexdigest()


class InstructorRun:
    def __init__(self, reader: PathReader, classifier: Classifier, store: InstructorStore, rate: float,
                 rules_sha256: str, first_counted: date | None = None):  # fmt: skip
        self.reader, self.classifier, self.store, self.rate = reader, classifier, store, rate
        self.rules_sha256, self.first_counted = rules_sha256, first_counted

    def for_session(self, session: date, write: bool = False) -> SessionResult:
        closed = self.reader.closed_on(session)
        attributions = {p.outcome.position_id: self._attribute(p) for p in closed.paths}
        nets = self._nets(closed.paths, session)
        found = [self.classifier.classify(p, attributions[p.outcome.position_id], controls_for(p, nets))
                 for p in closed.paths]  # fmt: skip
        records = tuple(found) + self._rechecks(session)
        kept = tuple(a for a in attributions.values() if a is not None)
        if write:
            self.store.write(session, InstructorKind.ATTRIBUTION, kept)
            self.store.write(session, InstructorKind.CAUSES, records)
        return SessionResult(session, kept, records, closed.unreadable)

    def _attribute(self, path: HeldPath) -> Attribution | None:
        return attribute(path, self.rate, self.rules_sha256)

    def _nets(self, paths: tuple[HeldPath, ...], session: date) -> dict:
        """The controls' closed results from the earliest entry among `paths` up to `session`."""
        first = min((p.outcome.entry.filled_at.astimezone(IST).date() for p in paths), default=session)
        return control_nets(self.reader.closed_between(first, session).paths)

    def _rechecks(self, session: date) -> tuple[Classification, ...]:
        origin = self.first_counted or session - timedelta(days=RECHECK_DAYS)
        latest: dict[str, Classification] = {}
        for day in self.reader.sessions(origin, session - timedelta(days=1)):
            for record in self.store.read(day, InstructorKind.CAUSES) or ():
                latest[record.position_id] = record  # a later file's record replaces an earlier one
        return tuple(new for old in latest.values() if waiting(old) and (new := self._again(old, session)))

    def _again(self, old: Classification, session: date) -> Classification | None:
        path = next((p for p in self.reader.closed_on(old.closed_on).paths
                     if p.outcome.position_id == old.position_id), None)  # fmt: skip
        if path is None:
            return None
        new = self.classifier.classify(path, self._attribute(path), controls_for(path, self._nets((path,), session)),
                                       corrects=record_sha256(old))  # fmt: skip
        return None if replace(new, corrects=old.corrects) == old else new
