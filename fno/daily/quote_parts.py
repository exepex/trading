"""The 3 pm quote parts inside the daily run (story O1, A4c's passed routine steps 2-3b, judge 169): NIFTY (Groww) and
NSE start together at the run's start, the other indices right after NIFTY's commit, each in its own window. They run
as child processes beside the desk's steps, and the run's one thread commits each part's own files when it ends, NIFTY
first, through E3's committer (its guard, pull and push attempts), never `research/data/quotes/` as a whole.

One git at a time: commits happen only in the run's one thread, between the desk's steps or while it waits
(`ServicingWaiter`), so a part's commit and a desk commit never interleave in the one checkout (criterion 4a)."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from ..alerts.sender import NOT_SENT, SENT, AlertSender
from ..constants import STEP_FAILED, STEP_REFUSED
from ..desk.daily_ports import CommitFailed, Committer
from ..models import IST
from ..quotes.recorder import MAX_EARLY_WAIT_SECONDS, WINDOW_START
from .processes import Process, Processes
from .steps import outcome

GROWW_QUOTES = ":(glob)research/data/quotes/groww/**/{name}_*"  # A4c's per-part paths, as CLAUDE.md gives them
INDICES = ("banknifty", "finnifty", "midcpnifty")
NOT_COMMITTED = (
    "F&O daily run {day}: quote part {name} NOT committed: {reason}. Hand fix (CLAUDE.md): git add {specs}, commit and "
    "push; never --no-verify"
)
PART_NOT_OK = (
    "F&O daily run {day}: 3 pm quote part {name} {status}: {reason}; the day's {name} record may be missing: check its "
    "sidecar and canonical marker"
)
OWN_ALERT = (SENT, NOT_SENT.split(":")[0])  # a line the part's own alert left ("alert sent ..." / "alert NOT sent ...")
STILL_RUNNING = "still running {minutes} minutes after the desk's exits: stopped, nothing more committed for it"
NEVER_STARTED = "never started: the part it waits for did not end in time"
FINISH_LIMIT = timedelta(minutes=20)
START_MARGIN = timedelta(minutes=3)  # inside A4's early limit by this much, for a slow start or a late clock
# A4's recorder refuses a start more than `MAX_EARLY_WAIT_SECONDS` before its window ("too early", nothing recorded):
# the earliest moment a 3 pm part may start, from A4's own constants (14:38 today)
EARLIEST_START = (
    datetime.combine(date.min, WINDOW_START) - timedelta(seconds=MAX_EARLY_WAIT_SECONDS) + START_MARGIN
).time()


@dataclass(frozen=True)
class QuotePart:
    name: str
    arguments: tuple[str, ...]  # the part's own `python -m fno` command, unchanged
    pathspecs: tuple[str, ...]  # its own files, and only its own
    starts_after: str | None = None  # starts once this part has ended and its commit was made or tried
    not_before: time | None = None  # never starts earlier than this (A4's early limit)


QUOTE_PARTS = (
    QuotePart("nifty", ("quotes", "record"), (GROWW_QUOTES.format(name="nifty"),), not_before=EARLIEST_START),
    QuotePart(
        "nse", ("quotes", "record", "--source", "nse"), ("research/data/quotes/nse/",), not_before=EARLIEST_START
    ),
    QuotePart("indices", ("quotes", "record-indices"), tuple(GROWW_QUOTES.format(name=n) for n in INDICES), "nifty"),
)
LEAD = QUOTE_PARTS[0].name  # NIFTY commits first: no other part commits before NIFTY's commit was made or tried


class QuoteParts:
    def __init__(
        self,
        parts: Sequence[QuotePart],
        processes: Processes,
        committer: Committer,
        changed: Callable[[Sequence[str]], list],
        alerts: AlertSender,
        clock: Callable[[], datetime],
    ):
        self.parts, self.processes, self.committer, self.changed, self.alerts, self.clock = (
            parts,
            processes,
            committer,
            changed,
            alerts,
            clock,
        )
        self.day: date | None = None
        self.running: dict[str, Process] = {}
        self.results: dict[str, dict] = {}
        self.closed = False  # past the finish limit: no part starts any more

    def start(self, day: date) -> list[str]:
        """Opens the day, once: every part that waits for no other starts now, or at its `not_before` if that is
        later (`start_due`); the names of those parts."""
        if self.day != day:
            self.day = day
            self.start_due()
        return [part.name for part in self.parts if part.starts_after is None]

    def start_due(self) -> None:
        """Starts each part whose time has come and that waits for no other; never runs git, so any wait of the run
        may call it, a command's included. Before the day is opened (a rerun whose log already holds `quotes` never
        opens it) there is nothing to start."""
        if not self.started:
            return
        for part in self.parts:
            due = part.not_before is None or self.clock() >= datetime.combine(self.day, part.not_before, IST)
            if not self.closed and part.starts_after is None and due and self._unstarted(part):
                self._start(part)

    @property
    def started(self) -> bool:
        return self.day is not None

    def busy(self) -> bool:
        return self.started and len(self.results) < len(self.parts)

    def service(self) -> None:
        """Starts the parts now due, commits every part that has ended (NIFTY's first), then starts the parts waiting
        for it."""
        self.start_due()
        for name, process in list(self.running.items()):
            code = process.poll()
            if code is not None and (name == LEAD or LEAD in self.results):
                self._finish(self._part(name), code, process.lines())
        for part in self.parts:
            if self.started and not self.closed and self._unstarted(part) and part.starts_after in self.results:
                self._start(part)

    def finish(self, wait: Callable[[datetime], None], not_before: datetime | None = None) -> dict[str, dict]:
        """Waits for the parts still running (servicing them), at most `FINISH_LIMIT`; their results. Past the limit
        a part still running is stopped (its files are not committed: they may be half-written), the parts that ended
        are committed and a part never started stays so."""
        limit = max(self.clock() + FINISH_LIMIT, not_before or self.clock())  # a stop at 14:35 waits past the windows
        self.service()
        while self.busy() and self.clock() < limit:
            wait(min(limit, self.clock() + timedelta(seconds=5)))
            self.service()
        self.closed = True
        for name, process in list(self.running.items()):
            if process.poll() is None:
                process.stop()
                del self.running[name]
                self._failed(name, STILL_RUNNING.format(minutes=int(FINISH_LIMIT.total_seconds() // 60)))
        self.service()
        for part in self.parts:
            if part.name not in self.results:
                self._failed(part.name, NEVER_STARTED)
        return self.results

    def _unstarted(self, part: QuotePart) -> bool:
        return part.name not in self.running and part.name not in self.results

    def _start(self, part: QuotePart) -> str:
        self.running[part.name] = self.processes.start(part.arguments)
        return part.name

    def _finish(self, part: QuotePart, code: int, lines: list[str]) -> None:
        del self.running[part.name]
        result = outcome(part.arguments, code, lines).result
        files = self.changed(part.pathspecs)
        try:
            result["commit"] = self.committer.commit(files, f"3 pm quotes {self.day} {part.name}") if files else None
        except CommitFailed as failed:
            result |= {"commit": None, "commit_error": str(failed)}
            specs = " ".join(f"'{spec}'" for spec in part.pathspecs)
            self.alerts.send(NOT_COMMITTED.format(day=self.day, name=part.name, reason=failed, specs=specs))
        self.results[part.name] = result
        if result["status"] in (STEP_FAILED, STEP_REFUSED) and not any(m in ln for ln in lines for m in OWN_ALERT):
            self._alert(part.name, result)  # a part that failed without alerting (a Groww outage): O2's case

    def _failed(self, name: str, reason: str) -> None:
        self.results[name] = {"status": STEP_FAILED, "reason": reason, "commit": None}
        self._alert(name, self.results[name])

    def _alert(self, name: str, result: dict) -> None:
        """Every part that did not record is alerted once: by itself, or here (owner, 16 Oct: every failure alerts)."""
        self.alerts.send(PART_NOT_OK.format(day=self.day, name=name, status=result["status"], reason=result["reason"]))

    def _part(self, name: str) -> QuotePart:
        return next(part for part in self.parts if part.name == name)
