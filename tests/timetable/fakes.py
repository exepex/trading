"""Fakes at the daily run's seams (story E3): a clock the waiter moves, commits kept in a list, packs, the books'
committed decisions, the recorder's execution capture, C4's gate and the exit rules."""

from __future__ import annotations

from datetime import date, datetime, timedelta

from fno.checks.gate import DataGate
from fno.checks.wiring import build_data_checks
from fno.config import load_app_config
from fno.desk.common_pack import CommonPack
from fno.desk.daily_ports import (
    AccountSync,
    CommittedDecision,
    Committer,
    DecisionSource,
    ExitRules,
    OrderBuilder,
    Packs,
    ValidityGate,
    VersionKeeper,
    Waiter,
)
from fno.desk.daily_run import DailyRun
from fno.desk.daily_steps import DeskSteps
from fno.desk.entries import EntryDesk
from fno.desk.execution_capture import CommittedExecutionSchedule, RecorderExecutionCapture
from fno.desk.exit_rules import StopLoss
from fno.desk.exits import ExitDesk
from fno.desk.snapshot import RecordedExecutionSnapshots
from fno.desk.timetable import timetable_from_config
from fno.desk.wiring import open_desk_journal
from fno.models import IST
from fno.quotes.recorder import RecordResult
from fno.storage.raw_store import LocalFolderStore
from tests.checks.builders import CALENDAR, nse_files
from tests.desk.builders import CHARGES, fly_rows, write_snapshot
from tests.desk.conftest import FakeSettlements

TIMETABLE = timetable_from_config(load_app_config())
HOLD = [StopLoss(1e9)]


class Clock(Waiter):
    def __init__(self):
        self.now = datetime(2026, 10, 14, 14, 50, tzinfo=IST)

    def __call__(self) -> datetime:
        return self.now

    def until(self, moment: datetime) -> None:
        self.now = max(self.now, moment)

    def advance(self, seconds: float) -> None:
        self.now += timedelta(seconds=seconds)


class Commits(Committer):
    def __init__(self, clock: Clock):
        self.clock, self.made, self.crash_on = clock, [], ""

    def commit(self, paths, message):
        if self.crash_on and self.crash_on in message:
            self.crash_on = ""
            raise RuntimeError("the run was killed after the fills")
        self.made.append((self.clock(), message))
        return f"c{len(self.made)}"


class Versions(VersionKeeper):
    def keep(self, day):
        return "Book 1 version v1 unchanged"


def pack_for(day: date) -> CommonPack:
    previous = CALENDAR.previous_session(day)
    items = [{"name": "spot:2026-10-27", "value": 25_000.0},
             {"name": f"close:{previous}", "value": {"nifty": 24_900.0, "vix": 12.0}}]  # fmt: skip
    return CommonPack(day, {"day": day.isoformat(), "provenance": {}, "items": items})


class FakePacks(Packs):
    def __init__(self):
        self.built: dict[date, CommonPack] = {}

    def build(self, day):
        self.built[day] = pack_for(day)
        return self.built[day]

    def stored(self, day):
        return self.built.get(day)

    def files(self, day):
        return ()


class Decisions(DecisionSource, OrderBuilder):
    """Each book's decision with its commit time and the time its push became visible on origin; read like D3's
    working tree: what is visible is what has been pushed by now (any later pull sees later pushes)."""

    def __init__(self, clock: Clock | None = None):
        self.clock, self.by_day, self.visible_at, self.orders_of = clock, {}, {}, {}
        self.observed_at: datetime | None = None

    def add(self, decision: CommittedDecision, orders, day: date, visible_at: datetime | None = None) -> None:
        self.by_day.setdefault((decision.book, day), []).append(decision)
        self.visible_at[decision.run_id + decision.book] = visible_at or decision.committed_at
        self.orders_of[(decision.book, decision.run_id)] = tuple(orders)

    def orders(self, book, run, decided_at):
        """The fake's `OrderBuilder` side: the orders each run decided (by its folder name, the run ID)."""
        return self.orders_of[(book, run.name)]

    def observe(self):
        self.observed_at = self.clock()
        return f"origin@{self.observed_at:%H%M%S}"

    def _visible(self, decision):
        return self.visible_at[decision.run_id + decision.book] <= self.clock()

    def committed(self, book, day, deadline):
        timely = [d for d in self.by_day.get((book, day), []) if self._visible(d) and d.committed_at < deadline]
        return timely[-1] if timely else None

    def recorded(self, book, day, run_id, commit):
        [decision] = [d for d in self.by_day[(book, day)] if (d.run_id, d.commit) == (run_id, commit)]
        return decision


class Capture:
    """The recorder's second capture: 40 seconds from the clock's time; `incomplete` days capture incompletely."""

    def __init__(self, clock: Clock, store: LocalFolderStore):
        self.clock, self.store, self.incomplete, self.taken = clock, store, set(), []
        self.incomplete_once: set[date] = set()  # the first capture of these days is incomplete, the retry is not

    def __call__(self) -> RecordResult:
        day, started = self.clock().date(), self.clock()
        snapshot_id = f"exec_{started:%Y%m%d_%H%M%S}"
        self.clock.advance(40)
        complete = day not in self.incomplete and day not in self.incomplete_once
        self.incomplete_once.discard(day)
        write_snapshot(self.store, snapshot_id, fly_rows(), started, self.clock(), complete=complete, day=day)
        self.taken.append((day, snapshot_id))
        return RecordResult("recorded", snapshot_id, complete, 4)


class C4(ValidityGate):
    def __init__(self, failing=()):
        self.failing, self.asked = set(failing), []

    def problems(self, decision, order):
        self.asked.append(order.proposal.trade_id)
        return ["C4: fixture failure"] if decision.book in self.failing else []


class Rules(ExitRules):
    def __init__(self, rules=None):
        self.by_trade = dict(rules or {})

    def rules(self, book):
        return {trade: self.by_trade.get(trade, HOLD) for trade in ("t1", "t2", "t3", "t4", "b1", "b2")}


class LocalSync(AccountSync):
    def __init__(self, root):
        self.root, self.writes = root, []

    def write(self, book, apply, message):
        self.writes.append(message)
        with open_desk_journal(book, self.root, TIMETABLE.lock_lease_seconds) as journal:
            return apply(journal)


def daily_run(root, tmp_path, alerts, books, decisions, validity, rules, clock=None):
    clock = clock or decisions.clock or Clock()
    decisions.clock = clock
    quotes = LocalFolderStore(tmp_path / "quotes")
    capture = Capture(clock, quotes)
    commits = Commits(clock)
    gate = DataGate(build_data_checks([nse_files(*CALENDAR.sessions(date(2026, 10, 1), date(2026, 10, 31)))],
                                      CALENDAR), RecordedExecutionSnapshots(quotes),
                    CommittedExecutionSchedule(root, TIMETABLE), alerts)  # fmt: skip
    steps = DeskSteps(root, books, TIMETABLE, Versions(), FakePacks(), decisions, decisions,
                      RecorderExecutionCapture(capture, quotes, tmp_path / "quotes", root, commits), gate, validity,
                      LocalSync(root), EntryDesk(CHARGES, clock), ExitDesk(CHARGES, alerts, FakeSettlements(), clock),
                      rules, alerts, clock)  # fmt: skip
    return DailyRun(steps, CALENDAR, commits, clock, clock), clock, capture, commits
