"""Where a candidate's outcome is found (story REC1c, text amendment item 3): a school candidate's `OutcomeRecord` in
the dashcam's sealed `outcomes` files from its session to the check's day, matched on the sealed decision file's
SHA-256, the driver and the road; a later record that corrects an earlier one wins. A desk candidate that traded has
no outcome reader yet (none can exist before a desk version reaches `paper`): it fails loudly, never a guess."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from datetime import date

from ..books.version_registry import SCHOOL_BOOK_PREFIX
from ..school.constants import SLOT_1500, RecordKind
from ..school.contracts.records import OutcomeRecord
from ..school.contracts.seal import StaleSeal
from .check import FoundOutcome, OutcomeLookup
from .constants import CandidateSourceName
from .contracts import Candidate, source_of
from .ports import InputFailed
from .school_source import SealedDecisions

ROAD_MARK = "#"
DESK_NOT_BUILT = "{version}: a desk candidate traded, and the desk's outcome reader is not built (REC1c)"


class SealedOutcomes(OutcomeLookup):
    def __init__(self, dashcam: SealedDecisions, sessions: Callable[[date, date], Iterable[date]]):
        """`sessions(a, b)`: the NSE sessions from a to b, both included."""
        self.dashcam, self.sessions = dashcam, sessions
        self._read: dict[date, tuple[OutcomeRecord, ...]] = {}  # one read per session file per run

    def outcome(self, candidate: Candidate, session: date, until: date) -> FoundOutcome | None:
        if source_of(candidate.version) is not CandidateSourceName.SCHOOL:
            if candidate.traded:
                raise InputFailed(DESK_NOT_BUILT.format(version=candidate.version))
            return None
        _, _, road = candidate.decision.path.partition(ROAD_MARK)
        driver = candidate.version.removeprefix(SCHOOL_BOOK_PREFIX)
        found = [r for day in self.sessions(session, until) for r in self._outcomes(day)
                 if (r.decision_sha256, r.driver_id, r.road) == (candidate.decision.sha256, driver, road)]  # fmt: skip
        return None if not found else FoundOutcome(found[-1].net, found[-1].is_ticket)  # the latest correction wins

    def _outcomes(self, day: date) -> tuple[OutcomeRecord, ...]:
        if day not in self._read:
            seal = self.dashcam.find(day, SLOT_1500, RecordKind.OUTCOMES)
            try:
                records = self.dashcam.read(seal) if seal is not None else ()
            except (StaleSeal, ValueError, OSError) as damaged:  # never fewer outcomes: the whole check fails
                raise InputFailed(f"{seal.path}: {type(damaged).__name__}") from None
            self._read[day] = tuple(r for r in records if isinstance(r, OutcomeRecord))
        return self._read[day]
