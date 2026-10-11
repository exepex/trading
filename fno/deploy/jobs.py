"""The two recurring jobs the desk needs, described once for every operating system."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

WATCHDOG_JOB = "FNO Desk Watchdog"
SYNC_JOB = "FNO End of Day Sync"
WATCHDOG_EVERY_MINUTES = 5
SYNC_TIME = "16:00"  # local time; set the machine to India Standard Time
WEEKDAYS = ("MON", "TUE", "WED", "THU", "FRI")


@dataclass(frozen=True)
class ScheduledJob:
    name: str
    command: list[str]  # program and arguments
    every_minutes: int | None = None  # run repeatedly, or
    weekdays_at: str | None = None  # run on weekdays at HH:MM


def desk_jobs(python: Path, entry_script: Path) -> list[ScheduledJob]:
    """A watchdog that (re)starts the desk if it is not running, and the end-of-day save to GitHub."""
    run = [str(python), str(entry_script), "deploy"]
    return [
        ScheduledJob(WATCHDOG_JOB, [*run, "ensure-running"], every_minutes=WATCHDOG_EVERY_MINUTES),
        ScheduledJob(SYNC_JOB, [*run, "sync"], weekdays_at=SYNC_TIME),
    ]
