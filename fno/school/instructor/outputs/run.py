"""One session's instructor run (story MS-INS, part e): every trade and ticket closed that session attributed and
classified, with REF's and RC1's results on its road-slot; then every earlier position checked again when its
classification was waiting for data (cause 11 before its expiry settled, or a modifier before the controls closed) or
its outcome has been corrected since (judge 522). A changed result is written as a new record naming the old: a new
classification, and for a corrected outcome a new attribution too. Orphan corrections are listed on every run.
Written write-once to the instructor's own files; a dry run writes nothing."""

from collections import defaultdict
from dataclasses import dataclass, replace
from datetime import date, timedelta

from ....models import IST
from ...contracts.records import OutcomeRecord
from ..attribution.attribute import attribute
from ..causes.classify import Classifier
from ..contracts import Attribution, Cause, Classification, HeldPath, Modifier, record_sha256
from ..ports import InstructorKind, InstructorStore
from ..reader import PathReader
from .controls import control_nets, controls_for

RECHECK_DAYS = 90  # how far back earlier positions are checked again when no first counted session is set


@dataclass(frozen=True)
class SessionResult:
    session: date
    attributions: tuple[Attribution, ...]  # this session's, then the corrections of earlier ones
    classifications: tuple[Classification, ...]  # this session's closed paths, then the corrections of earlier ones
    unreadable: tuple[date, ...]
    orphans: tuple[OutcomeRecord, ...] = ()  # corrections naming no outcome on file: an alert, never dropped


def waiting(record: Classification) -> bool:
    """Its cause 11 or its modifier waited for data (cause 13 waits for MS-P1j, so it never triggers a re-check)."""
    return Cause.EXIT_WHIPSAW in record.not_testable or record.modifier == Modifier.NOT_TESTABLE


class InstructorRun:
    def __init__(self, reader: PathReader, classifier: Classifier, store: InstructorStore, rate: float,
                 rules_sha256: str, first_counted: date | None = None):  # fmt: skip
        self.reader, self.classifier, self.store, self.rate = reader, classifier, store, rate
        self.rules_sha256, self.first_counted = rules_sha256, first_counted

    def for_session(self, session: date, write: bool = False) -> SessionResult:
        """A session already written is returned as written, whenever it is rerun: later runs see more (re-checks,
        closed controls), so recomputing could differ, and a written file is never rewritten. A later change arrives
        as a re-check correction on the next session's run."""
        orphans = self.reader.orphan_corrections()
        written = self.store.read(session, InstructorKind.CAUSES) if write else None
        if written is not None:
            kept = self.store.read(session, InstructorKind.ATTRIBUTION) or ()
            return SessionResult(session, tuple(kept), tuple(written), self.reader.closed_on(session).unreadable,
                                 orphans)  # fmt: skip
        closed = self.reader.closed_on(session)
        attributions = {p.outcome.position_id: self._attribute(p) for p in closed.paths}
        nets = self._nets(closed.paths, session)
        found = [self.classifier.classify(p, attributions[p.outcome.position_id], controls_for(p, nets))
                 for p in closed.paths]  # fmt: skip
        new_attributions, new_causes = self._rechecks(session)
        kept = tuple(a for a in attributions.values() if a is not None) + new_attributions
        records = tuple(found) + new_causes
        if write:
            self.store.write(session, InstructorKind.ATTRIBUTION, kept)
            self.store.write(session, InstructorKind.CAUSES, records)
        return SessionResult(session, kept, records, closed.unreadable, orphans)

    def _attribute(self, path: HeldPath) -> Attribution | None:
        return attribute(path, self.rate, self.rules_sha256)

    def _nets(self, paths: tuple[HeldPath, ...], session: date) -> dict:
        """The controls' closed results from the earliest entry among `paths` up to `session`."""
        first = min((p.outcome.entry.filled_at.astimezone(IST).date() for p in paths), default=session)
        return control_nets(self.reader.closed_between(first, session).paths)

    def _latest(self, session: date, kind: InstructorKind) -> dict[str, object]:
        origin = self.first_counted or session - timedelta(days=RECHECK_DAYS)
        latest = {}
        for day in self.reader.sessions(origin, session - timedelta(days=1)):
            for record in self.store.read(day, kind) or ():
                latest[record.position_id] = record  # a later file's record replaces an earlier one
        return latest

    def _rechecks(self, session: date) -> tuple[tuple[Attribution, ...], tuple[Classification, ...]]:
        causes, attributions = (
            self._latest(session, InstructorKind.CAUSES),
            self._latest(session, InstructorKind.ATTRIBUTION),
        )
        by_day: dict[date, list[Classification]] = defaultdict(list)
        for old in causes.values():
            by_day[old.closed_on].append(old)
        new_attributions, new_causes = [], []
        for day, olds in sorted(by_day.items()):
            paths = {p.outcome.position_id: p for p in self.reader.closed_on(day).paths}
            for old in olds:
                path = paths.get(old.position_id)
                corrected = path is not None and record_sha256(path.outcome) != old.outcome_sha256
                if path is None or not (corrected or waiting(old)):
                    continue
                attribution = self._attribute(path)
                if corrected and attribution is not None:
                    before = attributions.get(old.position_id)
                    new_attributions.append(replace(attribution, corrects=record_sha256(before) if before else ""))
                new = self.classifier.classify(path, attribution, controls_for(path, self._nets((path,), session)),
                                               corrects=record_sha256(old))  # fmt: skip
                if replace(new, corrects=old.corrects) != old:
                    new_causes.append(new)
        return tuple(new_attributions), tuple(new_causes)
