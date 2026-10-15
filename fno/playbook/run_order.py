"""One order for a day's decision runs (story D3b, decisions 60 and 61), used by every reader that needs "first":
E3's collector, the run log's list, Book 1's records and S1's first counted decision. Nothing else sorts run folders.

- **Ancestry first.** When one run's commit is an ancestor of another's, it landed first, whatever the clocks say (a
  checkout with a fast clock that pulled the other's run still commits after it).
- **Commit time** (the commit that added the run's `records.sha256`, E3's own timing source) orders runs on parallel
  branches, then the run counter as a number (`-r10` after `-r2`, never by folder name).
- **Uncommitted runs** come after every committed one, by counter; they have no commit, so no reader can take one as
  the first decision or the first counted one.

A correction is a run any of whose records names the record it corrects (D3 criterion 4): shown, never collected. A
record that cannot be read makes its run unreadable: shown with the file, never collected, and never a reason to stop
the other runs or books."""

from __future__ import annotations

import json
import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Protocol

from ..desk.pack_items import available_time
from .decision_store import INPUTS_FILE, SUMS_FILE

RUN_COUNTER = re.compile(r"-r(\d+)$")


class RunCommits(Protocol):
    def added_in(self, path: str) -> tuple[str, str] | None: ...

    def is_ancestor(self, older: str, newer: str) -> bool: ...


@dataclass(frozen=True)
class OrderedRun:
    path: Path
    commit: str | None  # the commit that added its records.sha256; None while it is not committed
    committed_at: datetime | None

    @property
    def run_id(self) -> str:
        return self.path.name


def run_counter(run: Path) -> int:
    found = RUN_COUNTER.search(run.name)
    if found is None:
        raise ValueError(f"{run.name} is not a decision run ID (<date>-r<n>)")
    return int(found.group(1))


def ordered_runs(root: Path, runs: Sequence[Path], git: RunCommits) -> list[OrderedRun]:
    placed = [_placed(Path(root), run, git) for run in runs]
    committed = [r for r in placed if r.commit is not None]
    pending = sorted((r for r in placed if r.commit is None), key=lambda r: run_counter(r.path))
    before = {(o.path, r.path) for o in committed for r in committed if o is not r and _landed_before(o, r, git)}
    order: list[OrderedRun] = []
    while committed:
        ready = [r for r in committed if not any((o.path, r.path) in before for o in committed if o is not r)]
        first = min(ready, key=lambda r: (r.committed_at, run_counter(r.path)))
        order.append(first)
        committed.remove(first)
    return order + pending


def corrections(run: Path) -> list[dict]:
    """What each of the run's records corrects, with its reason, and each record that cannot be read; empty for a
    readable original run."""
    found = []
    for path in sorted(run.glob("*.json")):
        if path.name == INPUTS_FILE:
            continue
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as problem:
            found.append({"unreadable": path.name, "reason": f"{type(problem).__name__}: {problem}"})
            continue
        if isinstance(record, dict) and record.get("corrects"):
            found.append({"corrects": record["corrects"], "reason": record.get("reason", "")})
    return found


def _placed(root: Path, run: Path, git: RunCommits) -> OrderedRun:
    added = git.added_in((run / SUMS_FILE).relative_to(root).as_posix())
    moment = available_time(added[1]) if added else None
    return OrderedRun(run, added[0], moment) if added and moment is not None else OrderedRun(run, None, None)


def _landed_before(older: OrderedRun, newer: OrderedRun, git: RunCommits) -> bool:
    return older.commit != newer.commit and git.is_ancestor(older.commit, newer.commit)
