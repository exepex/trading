"""One whole desk day with a live AI book, for story F1t's end-to-end tests: E3's real `DailyRun` and desk steps, E3's
real D3 collection from this repository's history (commits dated by the test clock), C4's real recorded-pass gate and
E4's real fills; F1t's real steps, firer, routine side and collector. Only the outside is faked: the routine trigger
(it schedules the fake routine's seal and reveal on the clock), the remote observer (it reads `HEAD` at each deadline
on the clock), the execution capture and the decider (it writes the D3 run a real decider would)."""

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

from fno.ai.history import RepoHistory
from fno.ai.observed_receipts import Observation, ObservationFile
from fno.ai_trading.book_dispatch import ExitRulesByBook, OrdersByBook
from fno.ai_trading.collect import DecisionCollector
from fno.ai_trading.fire import DecisionFirer
from fno.ai_trading.paths import WORK_FOLDER, common_pack_path, observations_path
from fno.ai_trading.ports import DayPacks
from fno.ai_trading.promote import Promoter
from fno.ai_trading.steps import AiCollectStep, AiFireStep
from fno.ai_trading.timing import decision_timing_from_config
from fno.composition import build_record_scanner, open_account_writer
from fno.config import load_app_config
from fno.constants import BOOK1_RULES, BOOK2_HYBRID
from fno.daily.steps import Alerted
from fno.desk.committed_decisions import D3CommittedDecisions
from fno.desk.daily_ports import Committer, OrderBuilder
from fno.desk.pending_commit import PendingCommitter
from fno.desk.private_pack import PrivatePack
from fno.desk.recorded_c4 import RecordedC4Pass
from fno.desk.timetable import timetable_from_config
from fno.playbook.history import PlaybookGit
from tests.desk.builders import fly_order
from tests.timetable.fakes import C4, Clock, Decisions, Rules, daily_run

from .builders import FakeDecider, private_body, registry
from .day import KeepPointer, NoStop, SameCards
from .fakes import DecisionRoutine

CFG = load_app_config()
TIMING = decision_timing_from_config(CFG, timetable_from_config(CFG))
C4_PASSED = {"c4": {"ok": True, "checks": [{"check": "fixture", "ok": True}]}, "candidate": "built"}
C4_FAILED = {"c4": {"ok": False, "checks": [{"check": "envelope", "ok": False}]}, "candidate": "built"}


def git(root: Path, *args: str, when: datetime | None = None) -> str:
    env = dict(os.environ) | (
        {"GIT_COMMITTER_DATE": when.isoformat(), "GIT_AUTHOR_DATE": when.isoformat()} if when else {}
    )
    return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True, env=env).stdout


class ScriptedClock(Clock):
    """E3's test clock and waiter, which also runs what the outside world does at its moment (a routine's seal, the
    remote observer's reading) when the run waits past it."""

    def __init__(self, day):
        super().__init__()
        self.now, self.events = datetime.combine(day, self.now.timetz()), []

    def sleep(self, seconds: float) -> None:
        self.advance(seconds)

    def on(self, moment: datetime, action) -> None:
        self.events = sorted([*self.events, (moment, len(self.events), action)], key=lambda e: e[:2])

    def until(self, moment: datetime) -> None:
        while self.events and self.events[0][0] <= moment:
            when, _, action = self.events.pop(0)
            self.now = max(self.now, when)
            action()
        super().until(moment)


class ClockCommitter(Committer):
    """Commits for real in the test repository, dated by the test clock (E3's collector reads committer times)."""

    def __init__(self, root: Path, clock: ScriptedClock):
        self.root, self.clock = Path(root), clock

    def commit(self, paths, message, own_unpushed=None):
        existing = [str(p) for p in paths if Path(p).exists()]
        if existing:
            git(self.root, "add", "-f", *existing)
        git(self.root, "commit", "-q", "--allow-empty", "-m", message, when=self.clock())
        return git(self.root, "rev-parse", "HEAD").strip()


class RunOrders(OrderBuilder):
    """The book's order builder (F5's part): one fly order whose `decision_id` names the run's record."""

    def orders(self, book, run, decided_at):
        return (fly_order("b1", book=book, decided_at=decided_at),)


class Observer:
    """The remote observer's child process: at each deadline (plus 0.4 s) it records the repository's `HEAD`."""

    def __init__(self, root: Path, clock: ScriptedClock, killed: bool = False):
        self.root, self.clock, self.killed, self.started = Path(root), clock, killed, []

    def start(self, arguments):
        self.started.append(arguments)
        deadlines = [datetime.fromisoformat(a) for a in arguments[5::2]]
        for deadline in deadlines if not self.killed else ():
            self.clock.on(deadline + timedelta(seconds=0.4), lambda d=deadline: self._read(d))
        return object()

    def _read(self, deadline):
        head = git(self.root, "rev-parse", "HEAD").strip()
        ObservationFile(self.root / observations_path(deadline.date())).append(
            Observation(deadline, self.clock(), self.clock(), head))  # fmt: skip


class Routine(KeepPointer):
    """The book's routine: fired, it seals at `seal_at` and reveals at the pointer's reveal time (unless told not)."""

    def __init__(self, root, clock, draft, seal_at=(15, 8), reveal=True):
        super().__init__()
        self.root, self.clock, self.draft, self.seal_at, self.do_reveal = Path(root), clock, draft, seal_at, reveal
        self.fake = DecisionRoutine(root, registry(root), clock)

    def fire(self, pointer):
        link = super().fire(pointer)
        day = pointer.day
        if self.seal_at:
            self.clock.on(datetime.combine(day, self._time(*self.seal_at), self.clock.now.tzinfo), self._seal)
        if self.do_reveal and self.seal_at:
            self.clock.on(pointer.reveal_from, self.fake.session().reveal)
        return link

    def _seal(self):
        session = self.fake.session()
        session.brief(self.texts[-1])
        answer = self.root / WORK_FOLDER / "answer.json"
        answer.write_text(json.dumps(self.draft), encoding="utf-8")
        session.seal(answer)

    @staticmethod
    def _time(hour, minute, second=0):
        return datetime(2000, 1, 1, hour, minute, second).time()


def start_repository(root: Path, day, books=(BOOK1_RULES, BOOK2_HYBRID)) -> None:
    for book in books:
        with open_account_writer(book, root) as writer:
            writer.start(day)
    registry(root)
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.email", "desk@example.invalid")
    git(root, "config", "user.name", "desk")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "accounts and prompts", when=datetime.combine(day, datetime.min.time()))


def build_day(root: Path, tmp_path: Path, alerts, day, routine_draft, *, c4=C4_PASSED, seal_at=(15, 8), reveal=True,
              observer_killed=False, decider=None, live=(BOOK2_HYBRID,)):  # fmt: skip
    """The run, its clock and the parts a test inspects."""
    start_repository(root, day)
    clock = ScriptedClock(day)
    run, _, capture, _ = daily_run(root, root, alerts, (BOOK1_RULES, *live), Decisions(), C4(), Rules(), clock)
    run.steps.decisions, run.steps.validity = D3CommittedDecisions(root, PlaybookGit(root)), RecordedC4Pass()
    run.steps.orders = OrdersByBook({book: RunOrders() for book in live})
    run.steps.exit_rules = ExitRulesByBook({book: Rules() for book in (BOOK1_RULES, *live)})
    run.committer = PendingCommitter(ClockCommitter(root, clock), root)

    def common(d):
        pack = run.steps.packs.stored(d)
        (root / common_pack_path(d)).parent.mkdir(parents=True, exist_ok=True)
        (root / common_pack_path(d)).write_bytes(pack.data)
        return pack

    packs = DayPacks(common, lambda book, d: PrivatePack(book, d, private_body(book, d)))
    routine = Routine(root, clock, routine_draft, seal_at, reveal)
    decider = decider or FakeDecider(root, changes={"opportunity_id": "d-b1", "validity": c4})
    reg = registry(root)
    firer = DecisionFirer(root, reg, {BOOK2_HYBRID: routine}, NoStop(), packs, SameCards(), build_record_scanner(),
                          ClockCommitter(root, clock).commit, clock)  # fmt: skip
    collector = DecisionCollector(root, RepoHistory(root), reg, Promoter(root, {BOOK2_HYBRID: decider}), packs,
                                  SameCards(), lambda: None)  # fmt: skip
    observer = Observer(root, clock, observer_killed)
    books = lambda d: live  # noqa: E731
    steps = {"ai_fire": AiFireStep(root, firer, TIMING, books, observer),
             "ai_collect": AiCollectStep(root, collector, TIMING, books, clock, clock)}  # fmt: skip
    run.day_steps = {name: Alerted(name, step, alerts) for name, step in steps.items()}  # as fno/daily/wiring.py
    return run, clock, routine, decider, observer, capture
