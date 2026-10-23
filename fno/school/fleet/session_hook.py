"""A step the fleet runs after the session's outcomes are sealed and before its counts are committed (story MS-P1j;
the instructor's session run, MS-INS part e, agreed with its builder 23 Oct 2026). It can never stop the school's own
record: a failure or a time-out is one #fno-desk alert naming its class, and the counts are still written and
committed. A step past its time is left to finish on its own; what it writes later (its counts file) is committed by
the next run of the session [reasoning only]."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

from ..constants import UnavailableReason
from .isolate import isolated

NOT_RUN = "school {name} not run for {session} ({why}); the session's own record and counts are unaffected"


@dataclass(frozen=True)
class IsolatedSessionStep:
    name: str
    work: Callable[[date], object]
    alert: Callable[[str], object]
    seconds: float = 300.0

    def __call__(self, session: date) -> None:
        done = isolated(lambda: self.work(session), self.seconds)
        if done.failed:
            why = "time limit" if done.failed is UnavailableReason.DEADLINE else done.error_class
            self.alert(NOT_RUN.format(name=self.name, session=session, why=why))


def no_step(session: date) -> None:
    """A run with no step after its outcomes (a replay, the tests)."""
