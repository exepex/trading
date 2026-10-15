"""AI forecasts whose audit is still open (story G11's input to G8's looks). A confirmatory look is recorded once, so it
refuses to run while any AI forecast of a day up to the look's date is still under audit: G11 writes such a day's v4
row only after its audit settles, and until then the day reads as a miss that would stay in the recorded look. G11
keeps the open audits in a committed file; a missing file means no AI book has an open audit."""

from __future__ import annotations

import csv
import io
from abc import ABC, abstractmethod
from datetime import date
from pathlib import Path

HEADER = ["day", "forecaster", "question"]
OPEN_AUDITS = "a look on {look} needs every AI audit up to that day settled: {count} still open, the earliest {first}"


class AuditFileError(ValueError):
    """The open-audits file breaks its format: the look stops rather than guess."""


class LookBlocked(RuntimeError):
    """A confirmatory look refused because AI audits up to its date are still open; nothing was recorded."""


class OpenAudits(ABC):
    @abstractmethod
    def open_days(self) -> list[date]:
        """The forecast day of every AI forecast whose audit is still open."""


class OpenAuditFile(OpenAudits):
    def __init__(self, path: Path):
        self.path = Path(path)

    def open_days(self) -> list[date]:
        if not self.path.is_file():
            return []
        reader = csv.reader(io.StringIO(self.path.read_text(encoding="utf-8")))
        if next(reader, None) != HEADER:
            raise AuditFileError(f"{self.path.name}: the header is not {','.join(HEADER)}")
        try:
            return [date.fromisoformat(row[0]) for row in reader if row]
        except ValueError as error:
            raise AuditFileError(f"{self.path.name}: a day is not YYYY-MM-DD") from error


def require_settled(audits: OpenAudits, look_day: date) -> None:
    """Raises LookBlocked when any open audit is of a day up to `look_day`."""
    due = sorted(day for day in audits.open_days() if day <= look_day)
    if due:
        raise LookBlocked(OPEN_AUDITS.format(look=look_day, count=len(due), first=due[0]))
