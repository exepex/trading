"""Story F8c: a fired AI book run whose minutes are not in the usage ledger once `ai collect` has recorded every timing
file is one #fno-desk alert. Its routine stopped before its reveal, or the timing publish failed. The meter already
counts such a session as not captured (`fno/budget/capture_coverage.py`, F8 criterion 7), so its level shows unknown,
never a guessed number; this makes the gap seen the same day."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from ..alerts.sender import AlertSender
from ..budget.capture_coverage import not_captured
from ..budget.usage_ledger import UsageLedger

NOT_CAPTURED = ("Omenix F&O AI books' minutes (BG1) {day}: {book}'s run NOT captured (no timing in the usage ledger: "
                "the routine stopped before its reveal, or its timing could not be published); the budget meter shows "
                "its minutes as not captured")  # fmt: skip
PRINTED = "usage not captured: {book} {day}: {result}"


def usage_gaps(root: Path, ledger: UsageLedger, day: date) -> list[tuple[str, str]]:
    """(day, book) of each run fired on `day` with no ledger row for its session."""
    missing = not_captured(root, f"{day:%Y-%m}", ledger.rows(), (day + timedelta(days=1)).isoformat())
    return [(fired_day, book) for fired_day, book, _ in missing if fired_day == day.isoformat()]


def alert_usage_gaps(root: Path, ledger: UsageLedger, day: date, alerts: AlertSender) -> list[str]:
    """One alert per fired run of `day` not captured; one printed line each, naming the run and the send's result. The
    line never repeats the alert's text: the forecast-capture job posts every `Omenix F&O AI` line of its log again."""
    lines = []
    for fired_day, book in usage_gaps(root, ledger, day):
        result = alerts.send(NOT_CAPTURED.format(day=fired_day, book=book))
        lines.append(PRINTED.format(day=fired_day, book=book, result=result))
    return lines
