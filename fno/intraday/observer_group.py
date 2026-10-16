"""Several observers behind A16's one mark observer port (LM1's position monitor, A21's announcements poll): each runs
in order, isolated from the others, and within a hard time limit, so a hung member can never hold the mark's commit
or the next mark. A failure or a time-out is named by the member's class only and never skips the next member."""

from __future__ import annotations

import threading
from collections.abc import Sequence
from datetime import date, datetime

from .document import SnapshotDocument
from .observer import MarkObserver, MembersFailed

MEMBER_TIME_LIMIT_SECONDS = 10.0  # A21's agreed budget per mark (a 5 s request plus its Drive writes)
TIMED_OUT = "{member} timed out"


class ObserverGroup(MarkObserver):
    def __init__(self, members: Sequence[MarkObserver], limit_seconds: float = MEMBER_TIME_LIMIT_SECONDS):
        self.members, self.limit = tuple(members), limit_seconds

    def after_mark(self, day: date, mark: datetime, document: SnapshotDocument | None, status: str) -> None:
        failed = [name for member in self.members if (name := self._run(member, day, mark, document, status))]
        if failed:
            raise MembersFailed(failed)

    def _run(self, member: MarkObserver, *args) -> str:
        """'' when the member finished in time; otherwise its class name (and "timed out" when it hung)."""
        errors: list[BaseException] = []

        def call() -> None:
            try:
                member.after_mark(*args)
            except Exception as exc:  # isolation: kept by class name only
                errors.append(exc)

        worker = threading.Thread(target=call, daemon=True)  # a hung member is left behind, never waited for
        worker.start()
        worker.join(self.limit)
        name = type(member).__name__
        if worker.is_alive():
            return TIMED_OUT.format(member=name)
        return f"{name}: {type(errors[0]).__name__}" if errors else ""
