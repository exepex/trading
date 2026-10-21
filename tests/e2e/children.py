"""Story O2: the daily run's child commands, as the suite's one replaced process seam (`ChildProcesses`).

A 3 pm quote part is a separate process in the real run: it keeps its own time (it waits for its window and retries on
its own), and its files appear in the checkout as it writes them, committed by the run once it ends. Here each part
runs at its start on its own clock (copied from the run's, never moving it), writing into its own staging folder, and
its files reach the checkout's quote folder when the run sees it end. Its own alerts go to the same fake Slack; an
unsent one is printed by the run as the real `ChildProcess` relays it. NIFTY's part runs A4's real `record_today` over
the fake Groww. Book 1's decision runs in the run's time, as the run waits for it."""

from __future__ import annotations

import shutil
import tempfile
import traceback
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from fno.daily.processes import KEPT_LINES, UNSENT, Process, Processes, alerted_in
from fno.quotes.recorder import NSE_DATASET, QuoteSnapshotRecorder

from .outside import SPOT, FakeClock, market_rows

Outcome = tuple[int, list[str]]  # the exit code and the lines it printed


@dataclass(frozen=True)
class Background:
    """A part with its own clock: `work(clock, staging)` runs when it starts and writes into `staging`."""

    work: Callable[[FakeClock, Path], Outcome]


@dataclass(frozen=True)
class Foreground:
    """A command the run waits for: `work()` runs once the run's clock reaches `minutes` after its start."""

    minutes: float
    work: Callable[[], Outcome]


class ScriptedProcess(Process):
    def __init__(self, clock: FakeClock, ends_at: datetime, finish: Callable[[], Outcome], report=print):
        self.clock, self.ends_at, self.finish, self.report = clock, ends_at, finish, report
        self.code, self.printed, self.stopped = None, [], False

    def poll(self):
        if self.code is None and not self.stopped and self.clock() >= self.ends_at:
            try:
                self.code, self.printed = self.finish()
            except Exception:  # noqa: BLE001 - a crashing command exits 1 with its traceback, as a real child does
                self.code, self.printed = 1, traceback.format_exc().splitlines()
            for line in self.printed:  # as `ChildProcess` relays a child's unsent alerts
                if UNSENT in line:
                    self.report(line)
        return self.code

    def lines(self):
        return [line for line in self.printed if UNSENT not in line][-KEPT_LINES:]  # as ChildProcess keeps them

    def alerted(self):
        return alerted_in(self.printed)

    def stop(self):
        self.stopped = True


class Children(Processes):
    """`script[arguments]` is a `Background` or `Foreground`; `desk book1` is matched without its day. A command not
    in the script is a test error, never a silent pass."""

    def __init__(self, clock: FakeClock, script: dict, quotes_folder: Path):
        self.clock, self.script, self.quotes_folder, self.started = clock, script, quotes_folder, []

    def start(self, arguments, hold=None) -> Process:
        """`hold` (a 3 pm part's lock, F1) is not kept: a part here has done its work when it starts, so none outlives
        a killed run, as a real one dies with the routine's container."""
        key = tuple(arguments)
        entry = self.script[key[:2] if key[:2] == ("desk", "book1") else key]
        self.started.append((self.clock(), key))
        if isinstance(entry, Foreground):
            return ScriptedProcess(self.clock, self.clock() + timedelta(minutes=entry.minutes), entry.work)
        own_clock, staging = FakeClock({}, self.clock()), Path(tempfile.mkdtemp(prefix="part-"))
        try:
            outcome = entry.work(own_clock, staging)
        except Exception:  # noqa: BLE001 - as above: the part crashed
            outcome = (1, traceback.format_exc().splitlines())
        return ScriptedProcess(self.clock, own_clock(), lambda: self._land(staging, outcome))

    def _land(self, staging: Path, outcome: Outcome) -> Outcome:
        """The part's files appear in the checkout (as they would have, written in place), then it has ended."""
        shutil.copytree(staging, self.quotes_folder, dirs_exist_ok=True)
        shutil.rmtree(staging, ignore_errors=True)
        return outcome


def groww_snapshot(store, day, name: str, at: datetime) -> None:
    """A complete Groww attempt of `name` (the csv to Drive, the sidecar committed) and its canonical marker."""
    from tests.desk.builders import write_snapshot

    snapshot_id = f"{name}_{at:%Y%m%d_%H%M%S}"
    write_snapshot(store, snapshot_id, market_rows(at), at, at + timedelta(seconds=30), day=day, spot=SPOT)
    store.put(QuoteSnapshotRecorder.path(day, f"{name}_{day:%Y%m%d}.canonical"), snapshot_id.encode())


def weekly_snapshot(store, day, at: datetime) -> None:
    """A4f's NIFTY weekly attempt: its sidecar and canonical marker, in the weekly dataset (its csv goes to Drive)."""
    from fno.quotes.weekly import WEEKLY_DATASET, WEEKLY_STEM

    snapshot_id = f"{WEEKLY_STEM}_{at:%Y%m%d_%H%M%S}"
    for name, data in (
        (f"{snapshot_id}.meta.json", b"{}"),
        (f"{WEEKLY_STEM}_{day:%Y%m%d}.canonical", snapshot_id.encode()),
    ):
        store.put(QuoteSnapshotRecorder.path(day, name, WEEKLY_DATASET), data)


def nse_snapshot(store, day, at: datetime) -> None:
    """NSE's public attempt and its canonical marker, all committed."""
    snapshot_id = f"nifty_{at:%Y%m%d_%H%M%S}"
    for name, data in ((f"{snapshot_id}.meta.json", b"{}"), (f"nifty_{day:%Y%m%d}.canonical", snapshot_id.encode())):
        store.put(QuoteSnapshotRecorder.path(day, name, NSE_DATASET), data)
