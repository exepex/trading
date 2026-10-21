"""A written 15:45 report (story FL1-1, judge 422): its text, its alerts and what it covered, so the next report takes
up what this one could not. Coverage is kept per underlying and target day: `checked` (the seals of that day's
forecasts were checked and any missing or late one alerted) and `matched` (that day's forecasts were matched against
its official close). A target is checked on its own day (its seal deadlines have passed by 15:45) and matched once its
close is archived, which NSE does in the evening: so in the next report, or a later one if the archive is late."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .delivery import Attachment


def key(underlying: str, day: date) -> str:
    return f"{underlying} {day.isoformat()}"


@dataclass(frozen=True)
class WrittenReport:
    text: str
    alerts: tuple[str, ...]
    checked: tuple[str, ...] = ()
    matched: tuple[str, ...] = ()
    attachments: tuple[Attachment, ...] = ()  # the picture and the details file (FL1-1c), posted with the text
