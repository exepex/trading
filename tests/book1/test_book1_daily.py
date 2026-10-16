"""Story E5 end to end through E3's real daily run: Book 1 decides and commits at 15:00, E3's D3 reader collects it at
the 15:12 deadline (criterion 4, every fixture day), the run's orders are replayed through D2, C4's recorded pass gates
the fill (criterion 5: a decision failing C4, or with no C4 pass yet, never becomes a fill), E4 fills at the 15:15
capture, and the exit review uses Book 1's playbook time exits."""

from datetime import date, datetime, time

import pytest

from fno.books.account import PaperAccount
from fno.books.book1_exits import PlaybookExitRules
from fno.books.book1_orders import ReplayedOrders
from fno.books.book1_records import decided_exit_days, opening_trades
from fno.checks.gate import DataGate
from fno.checks.wiring import build_data_checks
from fno.composition import open_account_writer
from fno.constants import BOOK1_RULES, BOOKS, OUTCOME_OPENED
from fno.desk.committed_decisions import D3CommittedDecisions
from fno.desk.daily_run import DailyRun
from fno.desk.daily_steps import DeskSteps
from fno.desk.entries import EntryDesk
from fno.desk.execution_capture import CommittedExecutionSchedule, RecorderExecutionCapture
from fno.desk.exits import ExitDesk
from fno.desk.pending_commit import PendingCommitter
from fno.desk.recorded_c4 import RecordedC4Pass
from fno.desk.records import DeskRecords
from fno.desk.snapshot import RecordedExecutionSnapshots
from fno.models import IST
from fno.playbook import decision_record
from fno.playbook.opportunities import OpportunityFinder
from fno.quotes.recorder import RecordResult
from fno.research_engine.cycles import TradingDays
from fno.storage.raw_store import LocalFolderStore
from tests.checks.builders import CALENDAR, nse_files
from tests.decisions.builders import SAME_CODE, doc, snapshot
from tests.desk.builders import CHARGES, row, write_snapshot
from tests.desk.conftest import FakeSettlements
from tests.playbook.evaluation_builders import EXPIRY, price
from tests.timetable.fakes import TIMETABLE, Clock, Commits, FakePacks, LocalSync, Versions, marking_step

from .builders import DAYS, EXITS, book1, book1_doc, clock_at, priced_evaluator

PASSED = {"mode": "playbook", "ok": True, "checks": [{"check": "max_loss", "ok": True, "reason": "", "numbers": {}}]}
FAILED = {"mode": "playbook", "ok": False, "checks": [{"check": "leg_price", "ok": False, "reason": "", "numbers": {}}]}


class ChainCapture:
    """The execution capture of D2's fixture chain: every strike's quote half a rupee either side of its mid."""

    def __init__(self, clock, store):
        self.clock, self.store = clock, store

    def __call__(self):
        day, started = self.clock().date(), self.clock()
        self.clock.advance(40)
        rows = [row(k, kind, price(k, kind) - 0.5, price(k, kind) + 0.5, expiry=EXPIRY)
                for k in range(24_000, 26_050, 50) for kind in ("CE", "PE")]  # fmt: skip
        snapshot_id = f"exec_{started:%Y%m%d_%H%M%S}"
        write_snapshot(self.store, snapshot_id, rows, started, self.clock(), day=day)
        return RecordResult("recorded", snapshot_id, True, len(rows))


class Loader:
    def __init__(self, playbook):
        self.playbook = playbook

    def load(self):
        return self.playbook


@pytest.fixture
def root(tmp_path):
    for book in BOOKS:
        with open_account_writer(book, tmp_path) as writer:
            writer.start(DAYS[0])
    return tmp_path


def run_days(root, tmp_path, alerts, c4, monkeypatch, version=None, code=SAME_CODE):
    original = decision_record.RecordBuilder._opportunity  # C4 writes validity.c4 inside the run once it merges

    def with_c4(self, outcome, outcomes, files):
        record = original(self, outcome, outcomes, files)
        record["validity"]["c4"] = c4 if record["chosen_action"] == "trade" and record["mode"] == "book" else None
        return record

    monkeypatch.setattr(decision_record.RecordBuilder, "_opportunity", with_c4)
    playbook = snapshot(version or book1_doc())
    clock, quotes = Clock(), LocalFolderStore(tmp_path / "quotes")
    decider, git = book1(root, playbook, clock_at(datetime.combine(DAYS[0], time(15), IST)))
    gate = DataGate(build_data_checks([nse_files(*CALENDAR.sessions(date(2026, 10, 1), date(2026, 10, 31)))],
                                      CALENDAR), RecordedExecutionSnapshots(quotes),
                    CommittedExecutionSchedule(root, TIMETABLE), alerts)  # fmt: skip
    finder = OpportunityFinder(TradingDays(CALENDAR))
    exits = PlaybookExitRules(lambda book: decided_exit_days(root, book, finder),
                              lambda version: playbook.files.get(f"{version}.yaml"),
                              lambda book: DeskRecords(PaperAccount(root, book)), alerts)  # fmt: skip
    steps = DeskSteps(root, (BOOK1_RULES,), TIMETABLE, Versions(), FakePacks(),
                      D3CommittedDecisions(root, git), ReplayedOrders(priced_evaluator(), code),
                      RecorderExecutionCapture(ChainCapture(clock, quotes), quotes, tmp_path / "quotes", root,
                                               Commits(clock)),
                      gate, RecordedC4Pass(), LocalSync(root), EntryDesk(CHARGES, clock),
                      ExitDesk(CHARGES, alerts, FakeSettlements(), clock), exits, alerts, clock)  # fmt: skip
    marking = marking_step(root, (BOOK1_RULES,), quotes, alerts)
    run, logs = DailyRun(steps, CALENDAR, PendingCommitter(Commits(clock), root), clock, clock, marking), []
    for day in DAYS:
        git.clock.set(datetime.combine(day, time(15), IST))
        decider.decide(day)
        clock.now = datetime.combine(day, time(14, 50), IST)
        logs.append(run.run(day))
    return logs


def test_book1_s_records_are_collected_on_time_every_fixture_day_and_a_c4_pass_fills(root, tmp_path, alerts,
                                                                                     monkeypatch):  # fmt: skip
    logs = run_days(root, tmp_path, alerts, PASSED, monkeypatch)
    assert all("run_id" in log.result("decisions")[BOOK1_RULES] for log in logs)  # criterion 4: none late
    filled = {trade: r for log in logs for trade, r in log.result("fills").items()}
    assert filled and {r["outcome"] for r in filled.values()} == {OUTCOME_OPENED}
    opened = DeskRecords(PaperAccount(root, BOOK1_RULES)).fill_rows()
    assert opened and {(r["strategy"], r["decision_id"].split(":")[0]) for r in opened} == {("sc-a-v1", "sc-a-v1")}
    assert all(r["outcome"] == "held" for log in logs[1:] for r in log.result("exits")[BOOK1_RULES]["results"])
    # story D3b: every opened trade finds its opening run in the run log
    found = opening_trades(root, BOOK1_RULES)
    assert found.problems == {} and set(found.trades) == {r["trade_id"] for r in opened}


@pytest.mark.parametrize("c4", [None, FAILED])
def test_a_book1_decision_without_a_c4_pass_never_becomes_a_fill(root, tmp_path, alerts, monkeypatch, c4):
    """Criterion 5. `None` is today's reality until C4 merges: no Book 1 order fills at all."""
    logs = run_days(root, tmp_path, alerts, c4, monkeypatch)
    results = [r for log in logs for r in log.result("fills").values()]
    assert results and all(r["reason"].startswith("not filled: no completed C4 pass") for r in results)
    assert DeskRecords(PaperAccount(root, BOOK1_RULES)).fill_rows() == []


class OtherCode:
    """The running code is not the record's commit (a merge to fno/ after Book 1's 15:00 commit)."""

    def matches(self, commit):
        return False


@pytest.mark.parametrize("cause", ["code merged after the decision", "a stop nobody enforces"])
def test_a_refused_order_build_fails_closed_for_entries_only_and_the_day_goes_on(root, tmp_path, alerts, monkeypatch,
                                                                                cause):  # fmt: skip
    """Judge 84: a ReplayRefused (code merged after 15:00) or an unenforceable exit gives "not filled" and an alert
    for that book's entries; the snapshot, the fills step and every exit review still run."""
    if cause == "code merged after the decision":
        logs = run_days(root, tmp_path, alerts, PASSED, monkeypatch, code=OtherCode())
    else:
        stop = doc("sc-a", exits={**EXITS, "loss": "stop at 2x credit"})
        logs = run_days(root, tmp_path, alerts, PASSED, monkeypatch, version=stop)
    first = logs[0]
    assert list(first.steps) == ["versions", "pack", "decisions", "snapshot", "fills", "exits", "trade_marks"]
    refused = first.result("fills")[BOOK1_RULES]
    assert refused["outcome"] == "not filled" and "gives no orders" in refused["reason"]
    assert any(BOOK1_RULES in sent and "gives no orders" in sent for sent in alerts.sent)
    assert DeskRecords(PaperAccount(root, BOOK1_RULES)).fill_rows() == [] and "exits" in logs[-1].steps
