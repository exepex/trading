"""The polling loop of one GitHub run (story A19, scopes 6-8): poll every 5 minutes inside the window, flush a part
(heartbeat and items) with its receipts every 15 minutes, save the seen snapshot every 2 hours and at the end, and
stop at 330 minutes or when the window closes. With the overnight bridge on, a run outside the window sleeps until it
opens, so a run is alive at the window's start (judge 352 addendum 1)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta

from ..models import IST
from .episodes import Episodes
from .memory import SeenMemory
from .names import COVERAGE_GAP, DRIVE_WRITE, RECEIPT_COMMIT, RESTART_STOPPED, SNAPSHOT_WRITE
from .polling import FeedPoller
from .store import NewsStore
from .window import PollingWindow

POLL_EVERY = timedelta(minutes=5)
FLUSH_EVERY = timedelta(minutes=15)
SNAPSHOT_EVERY = timedelta(hours=2)
MAX_RUN = timedelta(minutes=330)
GAP_LIMIT = timedelta(minutes=15)
FINAL_TRIES, FINAL_PAUSE_SECONDS = 3, 20  # the last flush is retried: nothing after it can save the lines
HEALTHY_RUN = timedelta(minutes=10)  # a run this long closes a stopped-restart episode (scope 7)
NOT_COMMITTED = "NOT committed"
GAP = "Omenix F&O news: coverage gap from {start} to {end} IST ({minutes} min inside the window without a poll)"
SUMMARY = "news run: {polls} poll(s), {items} new item line(s), {parts} part(s), {snapshots} snapshot(s)"


@dataclass(frozen=True)
class RunPlan:
    window: PollingWindow
    bridge: bool
    max_run: timedelta = MAX_RUN


class NewsRun:
    def __init__(self, poller: FeedPoller, memory: SeenMemory, store: NewsStore, episodes: Episodes, committer,
                 plan: RunPlan, clock: Callable[[], datetime], sleep: Callable[[float], None], out=print):  # fmt: skip
        self.poller, self.memory, self.store, self.episodes, self.committer = poller, memory, store, episodes, committer
        self.plan, self.clock, self.sleep, self.out = plan, clock, sleep, out
        self.pending: list[dict] = []
        self.counts = {"polls": 0, "items": 0, "parts": 0, "snapshots": 0}
        self.sequence = 0  # one number per Drive write attempt: a retried write never reuses a name
        self.saved = True  # the last flush saved every line and committed every receipt and row
        self.started: datetime | None = None
        self.snapshot_owed = False  # a failed snapshot is retried at the next flush, not two hours later

    def run(self) -> timedelta:
        """Polls until the run's end; returns how long it lasted (the successor rule needs it)."""
        started = self.started = self.clock()
        deadline = started + self.plan.max_run
        try:
            self._check_gap(started)
            self._loop(started, deadline)
        finally:
            self._final_flush()
            self.out(SUMMARY.format(**self.counts))
        return self.clock() - started

    def _final_flush(self) -> None:
        for attempt in range(FINAL_TRIES):
            if attempt:
                self.sleep(FINAL_PAUSE_SECONDS)
            self._flush(self.clock(), snapshot=attempt == 0)
            if self.saved:
                return

    def _loop(self, started: datetime, deadline: datetime) -> None:
        window, next_poll = self.plan.window, started
        next_flush, next_snapshot = started + FLUSH_EVERY, started + SNAPSHOT_EVERY
        while (now := self.clock()) < deadline:
            if not window.is_open(now):
                if not self.plan.bridge:
                    return
                opening = window.next_open(now)
                self._wait(min(opening, deadline))  # the bridge: alive, polling nothing, until it opens or the run ends
                next_poll = opening
                continue
            if now >= next_poll:
                self.pending += self.poller.poll(now)
                self.counts["polls"] += 1
                next_poll = now + POLL_EVERY
            if now >= next_flush:
                self._flush(now, snapshot=now >= next_snapshot)
                next_flush = now + FLUSH_EVERY
                next_snapshot = now + SNAPSHOT_EVERY if now >= next_snapshot else next_snapshot
            closing = window.next_close(now)
            self._wait(min(t for t in (next_poll, next_flush, deadline, closing) if t is not None))

    def _wait(self, until: datetime) -> None:
        seconds = (until - self.clock()).total_seconds()
        if seconds > 0:
            self.sleep(seconds)

    def _check_gap(self, now: datetime) -> None:
        last = self.memory.last_heartbeat
        if last is None:
            return
        start = datetime.fromisoformat(last)
        missed = self.plan.window.time_open(start, now)
        if missed > GAP_LIMIT:
            text = GAP.format(start=f"{start.astimezone(IST):%d %b %H:%M}", end=f"{now.astimezone(IST):%d %b %H:%M}",
                              minutes=round(missed.total_seconds() / 60))  # fmt: skip
            self.episodes.event(COVERAGE_GAP, COVERAGE_GAP, text)

    def _flush(self, now: datetime, snapshot: bool) -> None:
        """Saves the pending lines, then always commits, so a failure row is committed even when Drive is down."""
        saved = self._save_part(now)
        if saved and (snapshot or self.snapshot_owed):
            self.snapshot_owed = not self._snapshot(now)
        if saved and self.started is not None and now - self.started >= HEALTHY_RUN:
            self.episodes.ok(RESTART_STOPPED)
        self.saved = self._commit() and saved

    def _save_part(self, now: datetime) -> bool:
        if not self.pending:
            return True
        try:
            self.store.put_part(now, self._next_sequence(), self.pending)
        except Exception as exc:  # any Drive failure: the lines stay pending for the next flush
            self.episodes.fail(DRIVE_WRITE, DRIVE_WRITE, f"part not saved to Drive ({type(exc).__name__})")
            return False
        self.episodes.ok(DRIVE_WRITE)
        self.counts["items"] += sum(1 for line in self.pending if line["line"] == "item")
        self.counts["parts"] += 1
        self.pending = []
        return True

    def _snapshot(self, now: datetime) -> bool:
        self.memory.prune(now)
        try:
            self.store.put_snapshot(now, self._next_sequence(), self.memory)
        except Exception as exc:  # retried at the next flush; its own step, so parts saving fine never close it
            self.episodes.fail(SNAPSHOT_WRITE, SNAPSHOT_WRITE, f"snapshot not saved to Drive ({type(exc).__name__})")
            return False
        self.episodes.ok(SNAPSHOT_WRITE)
        self.counts["snapshots"] += 1
        return True

    def _next_sequence(self) -> int:
        self.sequence += 1
        return self.sequence

    def _commit(self) -> bool:
        outcome = self.committer.commit("news capture")
        if NOT_COMMITTED in outcome:
            self.episodes.fail(RECEIPT_COMMIT, RECEIPT_COMMIT, ":".join(outcome.split(":")[:2]))  # short: no hint
            self.committer.commit("news capture: commit failure row")  # one more try carries the row itself
            return False
        self.episodes.ok(RECEIPT_COMMIT)
        return True
