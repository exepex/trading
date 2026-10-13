"""A periodic pass over every recorded file's last-write time (story A8, judge 16): the release recorder re-reads only
the last few sessions, so a rewrite months later is caught here. It asks the source for headers only, one file at a
time through the polite session, and appends a row (`day, checked_at, last_modified`) only for a day whose write time
moved later than any recorded one. Those rows feed `latest_writes`, so the rule holds the moved days back too."""

from __future__ import annotations

import csv
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

from ..models import now_ist
from ..storage.raw_source import RawFileSource, RawSourceUnavailable

SWEEP_FIELDS = ("day", "checked_at", "last_modified")


@dataclass
class SweepResult:
    checked: int = 0
    moved: list[tuple[date, datetime, datetime]] = field(default_factory=list)  # day, recorded write, newer write
    unanswered: list[date] = field(default_factory=list)  # unreachable, or no Last-Modified given


def read_sweeps(path: Path) -> dict[date, datetime]:
    """Day -> the latest moved write time any sweep recorded."""
    if not path.is_file():
        return {}
    latest: dict[date, datetime] = {}
    for row in csv.DictReader(path.read_text(encoding="utf-8").splitlines()):
        day, written = date.fromisoformat(row["day"]), datetime.fromisoformat(row["last_modified"])
        latest[day] = max(written, latest.get(day, written))
    return latest


class LastWriteSweep:
    def __init__(
        self,
        source: RawFileSource,
        path_for: Callable[[date], str],
        log: Path,
        clock: Callable[[], datetime] = now_ist,
    ):
        self.source, self.path_for, self.log, self.clock = source, path_for, Path(log), clock

    def run(self, recorded: dict[date, datetime]) -> SweepResult:
        """Checks every day in `recorded` (day -> latest recorded write) once."""
        result = SweepResult()
        for day in sorted(recorded):
            try:
                written = self.source.last_written(self.path_for(day))
            except RawSourceUnavailable:
                written = None
            result.checked += 1
            if written is None:
                result.unanswered.append(day)
            elif written > recorded[day]:
                result.moved.append((day, recorded[day], written))
                self._append(day, written)
        return result

    def _append(self, day: date, written: datetime) -> None:
        new = not self.log.is_file()
        with self.log.open("a", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, lineterminator="\n")
            if new:
                writer.writerow(SWEEP_FIELDS)
            writer.writerow([day.isoformat(), self.clock().isoformat(), written.isoformat()])
