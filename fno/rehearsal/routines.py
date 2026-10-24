"""The four scheduled routines a rehearsal replays (story REH1c), each as CLAUDE.md runs it: its start time, its
commands in order (a background one is started first and waited for at the end), and the receipts the routine's
session commits by hand after them. CLAUDE.md is the source; a test holds each command to its routine's section."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, time, timedelta

from ..forecast_lab.constants import EVENING, MORNING


@dataclass(frozen=True)
class Command:
    args: tuple[str, ...]  # "{day}" and "{week_ago}" are the replayed day and the day a week before it
    background: bool = False
    live_key: str | None = None  # REH1k: its `forecast_lab.live_from` edition; before it, exercised, not failed

    def for_day(self, day: date) -> list[str]:
        week_ago = day - timedelta(days=7)
        return [a.format(day=day.isoformat(), week_ago=week_ago.isoformat()) for a in self.args]


@dataclass(frozen=True)
class Routine:
    name: str
    section: str  # its CLAUDE.md section
    start: time
    commands: tuple[Command, ...]
    receipts: tuple[str, ...] = ()  # the routine's own `git add` paths, committed after its commands


ROUTINES = {
    r.name: r
    for r in (
        Routine("daily", "Daily desk routine", time(14, 5), (Command(("daily", "run", "--day", "{day}")),)),
        Routine("preopen", "Pre-open capture (story A22)", time(8, 36),
                (Command(("global-cues", "preopen"), background=True), Command(("preopen", "record")))),
        Routine("morning", "Morning and evening forecast routines", time(8, 38),
                (Command(("data-librarian", "index-close", "--from", "{week_ago}")),
                 Command(("lab", "open"), live_key=MORNING),
                 Command(("records", "certify", "closes", "--since", "7", "--level", "certified", "--commit"))),
                ("receipts/data/forecast_lab/v1/morning/",)),
        Routine("evening", "Morning and evening forecast routines", time(19, 53),
                (Command(("closes", "read", "--commit")),
                 Command(("records", "certify", "closes", "--level", "provisional", "--commit")),
                 Command(("data-librarian", "fo-bhavcopy", "--from", "{day}", "--to", "{day}")),
                 Command(("data-librarian", "participant-oi", "--from", "{day}", "--to", "{day}")),
                 Command(("data-snapshot", "fii-dii-cash-by-session")),
                 Command(("lab", "close"), live_key=EVENING), Command(("lab", "release-check"))),
                ("receipts/data/forecast_lab/v1/evening/", "research/data/forecast_lab/release/")),
    )
}  # fmt: skip
