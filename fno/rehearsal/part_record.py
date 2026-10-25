"""Whether a 3 pm capture was a part of the replayed day (story REH1n): a rehearsal runs today's code, so it can ask for
a capture the day never had (21 Oct: NIFTY's weeklies, added on 22 Oct). A stem is a part of day D when the real record
(the source checkout's `main`, never the rehearsal's own store) holds a canonical marker or an attempt's file of it on
or before D (an attempt writes its sidecar at once, its marker only at the window's end: judge 635), or when D's run
log names its part and that part records only this one stem (`QuotePart.canonicals`; the run's first step commits its
plan at the run's start, before any capture: judge 639). The run log counts only once the first commit on `main`
holding it is at or before the replay clock (REH1p's rule). The rule never reads a later day's file."""

from __future__ import annotations

import json
import subprocess
from collections.abc import Callable, Mapping
from datetime import UTC, date, datetime
from functools import lru_cache
from pathlib import Path

from .manifest_rows import RECORD_MAIN

QUOTES = "research/data/quotes"  # `storage.wiring.QUOTES_FOLDER`, inside the record checkout
RUN_LOG = "journal/runs/{day}.json"  # O1's run log of the day
NOT_RECORDED = "rehearsal: {stem} not recorded on or before {day}"


class PartRecord:
    def __init__(self, record: Path, single_stem: Mapping[tuple[str, str], str], now: Callable[[], datetime]):
        """`single_stem`: (dataset, stem) -> its part's name, for the parts that record one stem only."""
        self.record, self.single_stem, self.now = Path(record), dict(single_stem), now

    def is_part(self, dataset: str, stem: str, day: date) -> bool:
        if any(_dated(name, stem) <= day for name in _names(self.record, dataset) if _dated(name, stem)):
            return True
        part = self.single_stem.get((dataset, stem))
        return part is not None and part in self._planned(day)

    def _planned(self, day: date) -> tuple[str, ...]:
        path = RUN_LOG.format(day=day.isoformat())
        first = _first_commit(self.record, path)
        if first is None or first[0] > self.now():
            return ()
        log = json.loads(_git(self.record, "show", f"{first[1]}:{path}") or "{}")
        return tuple(log.get("steps", {}).get("quotes", {}).get("inputs", {}).get("parts", ()))


def _dated(name: str, stem: str) -> date | None:
    """The day of `<stem>_<YYYYMMDD>.canonical` or `<stem>_<YYYYMMDD>_<HHMMSS>.<ext>`, else None."""
    if not name.startswith(f"{stem}_"):
        return None
    try:
        return datetime.strptime(name[len(stem) + 1 : len(stem) + 9], "%Y%m%d").date()
    except ValueError:
        return None


@lru_cache(maxsize=16)
def _names(record: Path, dataset: str) -> tuple[str, ...]:
    listed = _git(record, "ls-tree", "-r", "--name-only", RECORD_MAIN, "--", f"{QUOTES}/{dataset}")
    return tuple(line.rsplit("/", 1)[-1] for line in listed.splitlines())


def _first_commit(record: Path, path: str) -> tuple[datetime, str] | None:
    added = _git(record, "log", "--diff-filter=A", "--format=%ct %H", RECORD_MAIN, "--", path)  # a routine's own commit
    lines = added.splitlines()
    if not lines:
        return None
    stamp, commit = lines[-1].split()
    return datetime.fromtimestamp(int(stamp), UTC), commit


def _git(record: Path, *args: str) -> str:
    done = subprocess.run(["git", *args], cwd=record, capture_output=True, text=True, check=False)
    return done.stdout if done.returncode == 0 else ""
