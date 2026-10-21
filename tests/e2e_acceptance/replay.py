"""Story O11: the recorded day through every built engine stage, in the day's order, wired from the composition roots
(packs, decision run, C4 validator, evaluator, weather, v4 forecasts, scorecards, scoreboards) and the daily run's
object graph as `fno/desk/daily_wiring.py` builds it, with its outside seams (git, Drive, Groww's recorder) replaced as
tests/timetable already replaces them. Each stage's output is kept for the tests to check."""

from __future__ import annotations

from dataclasses import dataclass, field

from fno import constants
from fno.books.account import PaperAccount
from fno.books.book1 import PENDING_MARKER, Book1
from fno.books.book1_exits import PlaybookExitRules
from fno.books.book1_inputs import LiveBook1Inputs
from fno.books.book1_orders import ReplayedOrders
from fno.books.book1_records import decided_exit_days
from fno.books.versions import VersionRow
from fno.books.versions import Versions as BookVersions
from fno.checks.gate import DataGate
from fno.checks.wiring import build_data_checks, build_trade_validator
from fno.composition import DESK_DECISION_TIME
from fno.config import load_app_config
from fno.constants import BOOK1_RULES
from fno.desk.committed_decisions import D3CommittedDecisions
from fno.desk.daily_run import DailyRun
from fno.desk.daily_steps import DeskSteps
from fno.desk.entries import EntryDesk
from fno.desk.execution_capture import CommittedExecutionSchedule, RecorderExecutionCapture
from fno.desk.exits import ExitDesk
from fno.desk.pack_store import PackStore
from fno.desk.pack_wiring import PACKED_BOOKS, build_common_pack_builder, build_private_pack_builder
from fno.desk.packs import WrittenPacks
from fno.desk.pending_commit import PendingCommitter
from fno.desk.recorded_c4 import RecordedC4Pass
from fno.desk.records import DeskRecords
from fno.desk.snapshot import RecordedExecutionSnapshots
from fno.desk.wiring import build_execution_snapshots
from fno.forecast_v4_rules.capture import capture_day
from fno.forecast_v4_rules.wiring import build_v4_forecasts, v4_writer
from fno.playbook.opportunities import OpportunityFinder
from fno.playbook.wiring import build_decision_run, build_rule_evaluator
from fno.price_distribution.recorder import LiveRecorder
from fno.price_distribution.sources import SnapshotChains
from fno.price_distribution.store import DriveDistributionStore
from fno.price_distribution.wiring import build_day_builder
from fno.quotes.recorder import RecordResult
from fno.research_engine.cycles import TradingDays
from fno.research_engine.implied_vol import Black76
from fno.scoreboard.committed_runs import CommittedRuns
from fno.scoreboard.protocol_status import protocol_status
from fno.scoreboard.sources import SnapshotMarks
from fno.scoreboard.wiring import board_from, matched_board_from
from fno.scorecard.scorecard import snapshot_marks
from fno.scorecard.wiring import build_scorecard_run
from fno.storage.data_store import DataStore
from fno.storage.receipts import ReceiptFolder
from fno.storage.wiring import build_session_calendar
from fno.weather.capture import capture_weather
from fno.weather.records import WeatherRecords
from fno.weather.wiring import build_weather_days, is_session, previous_regular
from tests.book1.builders import Commits as BookCommits
from tests.book1.builders import DiskRuns, clock_at
from tests.checks.builders import CALENDAR, nse_files
from tests.decisions.builders import CONTEXT, SAME_CODE
from tests.desk.builders import CHARGES, write_snapshot
from tests.desk.conftest import FakeSettlements
from tests.playbook.evaluation_builders import Counts, FixedValues, OwnShadowBooks
from tests.price_distribution.builders import MemoryDrive
from tests.risk.builders import book
from tests.timetable.fakes import TIMETABLE, Clock, Commits, LocalSync, Versions, marking_step
from tests.weather.fakes import FakeStore

from . import real_day as rd
from .lab_replay import LabReplay
from .o1_steps import day_steps

EXECUTION_ID = "exec_20261016_151500"
O1_START = rd.at(14, 5)  # the agreed O1 start (16 Oct log): the forecast steps run first, before G10's 14:30 cutoff


@dataclass
class Outputs:
    pack: object = None
    log: object = None
    scorecards: list = field(default_factory=list)
    pauses: list = field(default_factory=list)
    board: object = None
    matched: object = None
    distribution_drive: object = None  # G13's Drive files of the day (Drive is an outside service: in memory)
    lab: object = None  # G13b's issue and FL1's 15:45 report (`LabReplay`: its Drive folder and #fno-forecast posts)


class RealRowsCapture:
    """E3's execution capture at 15:15: the day's real rows again, timed as the 15:15 capture (no later real capture is
    committed); the recorder's role, as tests/book1's ChainCapture plays it."""

    def __init__(self, clock, store):
        self.clock, self.store = clock, store

    def __call__(self):
        started = rd.at(15, 15)
        self.clock.until(started)
        rows = rd.real_rows()
        self.clock.advance(40)
        write_snapshot(self.store, EXECUTION_ID, rows, started, self.clock(), day=rd.DAY)
        return RecordResult("recorded", EXECUTION_ID, True, len(rows))


class RegisteredFirst:
    """Git's order for D6: the version row's commit comes before every decision commit."""

    def first_commit_containing(self, text, path):
        return "registered"

    def is_ancestor(self, older, newer):
        return older == "registered" or older == newer


class Replay:
    def __init__(self, root, monkeypatch, alerts, start=O1_START, capture=RealRowsCapture, listed=True, context=None,
                 entries=None):  # fmt: skip
        self.root, self.alerts, self.cfg = root, alerts, load_app_config()
        self.entries = entries or (lambda clock: EntryDesk(CHARGES, clock))  # E8 hands entries over when live
        self.start, self.capture, self.listed = start, capture, listed
        self.context = {**CONTEXT, **(context or {})}  # D3's record header fields of Book 1's run
        self.playbook = rd.approved_playbook()
        rd.build_repository(root)
        rd.replace_outside_services(monkeypatch, root, self.playbook, listed)
        self.commits = BookCommits(clock_at(rd.at(15, 0)))
        self.clock = Clock()
        self.run_commits = Commits(self.clock)  # the run's own commits (a test may make one fail)
        self.packs = WrittenPacks(build_common_pack_builder(root), build_private_pack_builder(root), PackStore(root),
                                  DESK_DECISION_TIME, PACKED_BOOKS)  # fmt: skip
        self.out = Outputs()

    def run(self) -> Outputs:
        self.clock.now = self.start
        self.out.log = self.daily_run().run(rd.DAY)
        self.out.pack = self.packs.stored(rd.DAY)
        if self.out.log.done("snapshot"):
            self.score()
        return self.out

    def weather(self, day) -> list[str]:
        """`fno weather capture` (O1's `weather` step)."""
        return capture_weather(build_weather_days(), WeatherRecords(self.root / "weather"), day, self.clock(),
                               is_session, v4_writer(self.root / "v4"), lambda: "normal", FakeStore(),
                               previous_regular)  # fmt: skip

    def forecasts_v4(self, day) -> list[str]:
        """`fno forecast-v4 capture` (O1's `forecasts_v4` step)."""
        written = capture_day(build_v4_forecasts(day), day, self.clock(), v4_writer(self.root / "v4"))
        return [f"{written} v4 rows written"]

    def price_distribution(self, day) -> list[str]:
        """`fno pricedist record --live` (O1's `price_distribution` step, G13), NIFTY only: 16 Oct had no A4c capture.
        A non-zero exit is O1's `failed`."""
        drive = self.out.distribution_drive = MemoryDrive()
        store = DriveDistributionStore(drive, DataStore(drive, "data", ReceiptFolder(self.root / "receipts"),
                                                        "pricedist", "replay"))  # fmt: skip
        recorder = LiveRecorder(SnapshotChains(rd.quote_store(self.root)), build_day_builder(self.cfg), store,
                                build_session_calendar(), (constants.NIFTY_SYMBOL,), day, self.clock)  # fmt: skip
        code, lines = recorder.record(day)
        if code:
            raise RuntimeError(lines[-1])
        return lines

    def decide(self, day) -> list[str]:
        """`fno desk book1` (O1's `book1` step, right after the pack): Book 1's decision, committed at 15:00."""
        return [self.book1().decide(day)]

    def book1(self) -> Book1:
        inputs = LiveBook1Inputs(self.root, rd.quote_store(self.root), self.cfg["risk_free_rate"], Black76(),
                                 lambda day, snapshot: FixedValues(), lambda market: (book(), Counts(),
                                                                                       OwnShadowBooks()),
                                 lambda day, hashes: {**self.context, **hashes})  # fmt: skip
        committer = PendingCommitter(self.commits, self.root, PENDING_MARKER)
        return Book1(self.root, CALENDAR, lambda: self.playbook, inputs,
                     build_decision_run(self.cfg, BOOK1_RULES, self.root), committer, DiskRuns(self.root, self.commits),
                     self.alerts)  # fmt: skip

    def daily_run(self) -> DailyRun:
        root, quotes, clock = self.root, rd.quote_store(self.root), self.clock
        nse = nse_files(rd.NSE_FILE_DAY) if self.listed else nse_files()
        gate = DataGate(build_data_checks([nse], CALENDAR), RecordedExecutionSnapshots(quotes),
                        CommittedExecutionSchedule(root, TIMETABLE), self.alerts)  # fmt: skip
        validator = build_trade_validator(self.cfg, BOOK1_RULES, root, log=False)
        orders = ReplayedOrders(build_rule_evaluator(self.cfg, root), SAME_CODE, validator)
        capture = RecorderExecutionCapture(self.capture(clock, quotes), quotes, root / rd.QUOTES, root,
                                           Commits(clock))  # fmt: skip
        steps = DeskSteps(root, (BOOK1_RULES,), TIMETABLE, Versions(), self.packs,
                          D3CommittedDecisions(root, self.commits), orders, capture, gate, RecordedC4Pass(),
                          LocalSync(root), self.entries(clock), ExitDesk(CHARGES, self.alerts, FakeSettlements(),
                                                                                clock),
                          self.exit_rules(), self.alerts, clock)  # fmt: skip
        marking = marking_step(root, (BOOK1_RULES,), quotes, self.alerts)
        lab = self.out.lab = LabReplay(root, self.cfg, clock, self.alerts)
        commands = {"weather": self.weather, "forecasts_v4": self.forecasts_v4, "book1": self.decide,
                    "price_distribution": self.price_distribution, "price_ranges": lab.price_ranges,
                    "lab_close": lab.lab_close}  # fmt: skip
        o1 = day_steps(commands, build_scorecard_run(self.cfg, root, self.alerts), build_execution_snapshots(
            root / rd.QUOTES), root, self.alerts)  # fmt: skip
        return DailyRun(steps, CALENDAR, PendingCommitter(self.run_commits, root), clock, clock, marking,
                        day_steps=o1)  # fmt: skip

    def exit_rules(self) -> PlaybookExitRules:
        finder = OpportunityFinder(TradingDays(CALENDAR))
        return PlaybookExitRules(lambda name: decided_exit_days(self.root, name, finder),
                                 lambda version: self.playbook.files.get(f"{version}.yaml"),
                                 lambda name: DeskRecords(PaperAccount(self.root, name)), self.alerts)  # fmt: skip

    def score(self) -> None:
        snapshots = build_execution_snapshots(self.root / rd.QUOTES)
        valid = self.out.log.result("snapshot")["valid"]
        marks = snapshot_marks(snapshots.snapshot(rd.DAY, EXECUTION_ID)) if valid else {}
        self.out.scorecards, self.out.pauses = build_scorecard_run(self.cfg, self.root, self.alerts).run(
            rd.DAY, marks, pause=False
        )  # the run's reviews step paused; this reads the same cards back
        served = self.served()
        self.out.board = board_from(
            self.root, self.cfg["charges"], CALENDAR, self.versions(served),
            SnapshotMarks(snapshots, CommittedRuns(self.root).snapshot_ids()), protocol_status(self.root),
        ).build(rd.DAY)  # fmt: skip
        self.out.matched = matched_board_from(
            self.root,
            self.cfg,
            CALENDAR,
            self.versions(served),
            snapshots,
            FakeSettlements(),
            protocol_status(self.root),
        ).build(rd.DAY)

    @staticmethod
    def versions(served: dict) -> BookVersions:
        """D6's registry: Book 1's version registered before any decision of the day."""
        row = VersionRow(BOOK1_RULES, CONTEXT["version_id"], rd.ACCOUNTS_START, "registered", served, "replay")
        return BookVersions([row], RegisteredFirst())

    def served(self) -> dict:
        runs = CommittedRuns(self.root)
        return next((record["served"] for run in runs.runs() for record in runs.records(run)), {})
