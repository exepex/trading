"""The interface for reading one AI session's usage (story F8) and what every reader returns. Two readers exist: a
session export of the session tools (`usage_export.py`) and a routine's own timing of its run (`self_timed.py`)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime

from ..models import IST

NO_ZONE = "{what} {value!r} has no time zone"


class ExportRefused(ValueError):
    """The reading cannot be used without guessing; the message says why."""


@dataclass(frozen=True)
class DayUsage:
    day: date
    session_id: str
    model: str
    minutes: float
    turns: int
    tokens: dict[str, int] | None  # None: tokens unknown for the day (some turn carried none, or the reader has none)
    source: str  # where the figures came from, written to the ledger
    captured_at: str  # when they were read (ISO, with zone): later readings show whether a session is fully captured


class SessionUsageReader(ABC):
    @abstractmethod
    def days(self) -> list[DayUsage]:
        """One usage line per IST day on which the session had a finished turn, oldest first."""

    @abstractmethod
    def complete_before(self, today: date) -> date:
        """Days before this one are complete in this reading; later days must come from a later reading."""


def ist_time(value: str, what: str) -> datetime:
    """An ISO time with its zone, in IST; one without a zone is refused (never read in the computer's local time)."""
    try:
        moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise ExportRefused(f"{what} {value!r} is not an ISO time") from None
    if moment.tzinfo is None:
        raise ExportRefused(NO_ZONE.format(what=what, value=value))
    return moment.astimezone(IST)
