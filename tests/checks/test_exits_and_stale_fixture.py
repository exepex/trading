"""Story C3 criterion 3: with failed data checks, an open trade due to exit is a pending exit with an alert, filled at
the next valid quotes through E4's exit path; no fill is ever made from stale prices, price rules do not fire on them
and protection is not judged from them. A missing NSE file, or a big move with no shock flag, stops new trades only:
exits still run (judge 81). An unreadable snapshot's alert names the exits it holds up. Plus the judge's check: the
committed, deliberately stale snapshot is refused by the real checks."""

import json
from datetime import date, timedelta
from pathlib import Path

import pytest

from fno.books.account import PaperAccount
from fno.checks.gate import DataGate
from fno.checks.schedule import PackSnapshotSchedule
from fno.checks.wiring import build_data_checks
from fno.constants import (
    BOOK1_RULES,
    DATA_UNVERIFIED,
    OUTCOME_CLOSED,
    OUTCOME_OPENED,
    OUTCOME_PENDING_EXIT,
    OUTCOME_REFUSED,
)
from fno.desk.common_pack import CommonPack
from fno.desk.exit_rules import StopLoss, TimeExit
from fno.desk.records import DeskRecords
from fno.desk.snapshot import RecordedExecutionSnapshots
from fno.desk.wiring import open_desk_journal
from fno.storage.raw_store import LocalFolderStore
from tests.desk.builders import DAY, at, enter, fly_order, fly_rows, passed, write_snapshot

from .builders import CALENDAR, ExecutionWindow, gate, nse_files, pack_of

NEXT, LATER = DAY + timedelta(days=1), DAY + timedelta(days=2)
DUE = {"t1": [TimeExit(13)]}  # 13 days before the 27 Oct expiry: due from 14 Oct
STALE = Path(__file__).parents[1] / "fixtures" / "c3_stale"


@pytest.fixture
def opened(root, store, snapshots, entry_desk):
    write_snapshot(store, "exec", fly_rows(), at(15, 15), at(15, 15, 40))
    assert enter(root, snapshots, entry_desk, fly_order()).outcome == OUTCOME_OPENED


def review_at(root, store, snapshots, alerts, exit_desk, clock, day, sid, started, rules, rows=None, nse=None,
              spots=None):  # fmt: skip
    write_snapshot(store, sid, rows or fly_rows(), at(*started, day=day), at(*started[:2], 40, day=day), day=day)
    clock.set(at(15, 25, day=day))
    pack = pack_of(store, day, sid, **({"spots": spots} if spots else {}))
    snapshot, report = gate(snapshots, alerts, day, ExecutionWindow(sid, store), nse=nse).check(pack)
    with open_desk_journal(BOOK1_RULES, root) as journal:
        return exit_desk.review(BOOK1_RULES, snapshot, journal, rules, report), report


def closing_fills(root):
    return [r for r in DeskRecords(PaperAccount(root, BOOK1_RULES)).fill_rows() if r["action"] == "close"]


def test_a_due_exit_on_stale_data_is_pending_with_an_alert_then_fills_at_the_next_valid_quotes(
    root, store, snapshots, alerts, exit_desk, clock, opened
):
    [result], report = review_at(root, store, snapshots, alerts, exit_desk, clock, NEXT, "next", (14, 30), DUE)
    assert report.prices_unverified and result.outcome == OUTCOME_PENDING_EXIT
    assert result.reason.startswith(DATA_UNVERIFIED) and "retried at the next valid quotes" in result.reason
    assert closing_fills(root) == [] and len(result.alerts) == 1  # the desk's own alert, beside the gate's
    assert any("t1 pending_exit" in sent for sent in alerts.sent)
    [result], report = review_at(root, store, snapshots, alerts, exit_desk, clock, LATER, "later", (15, 15), DUE)
    assert report.ok and result.outcome == OUTCOME_CLOSED and len(closing_fills(root)) == 4


def test_price_rules_and_protection_are_never_judged_from_stale_prices(root, store, snapshots, alerts, exit_desk,
                                                                       clock, opened):  # fmt: skip
    rows = fly_rows({(25200, "CE"): {"valid": False, "reason": "no trade today"}})  # a protective leg unquotable
    [result], _ = review_at(root, store, snapshots, alerts, exit_desk, clock, NEXT, "next", (14, 30),
                            {"t1": [StopLoss(0.0)]}, rows)  # fmt: skip
    assert result.outcome == "held" and result.reason.startswith(DATA_UNVERIFIED)
    events = [e["outcome"] for e in DeskRecords(PaperAccount(root, BOOK1_RULES)).event_rows("t1")]
    assert events == [OUTCOME_OPENED] and closing_fills(root) == []  # no exit order, no protection_unverified


def test_a_missing_nse_file_stops_new_trades_but_exits_still_run(root, store, snapshots, alerts, exit_desk, clock,
                                                                 entry_desk, opened):  # fmt: skip
    [result], report = review_at(root, store, snapshots, alerts, exit_desk, clock, NEXT, "next", (15, 15), DUE,
                                 nse=nse_files())  # fmt: skip
    assert not report.ok and not report.prices_unverified and result.outcome == OUTCOME_CLOSED
    order = fly_order("t2", decided_at=at(15, 5, day=NEXT))
    the_gate = gate(snapshots, alerts, NEXT, ExecutionWindow("next", store), nse=nse_files())
    _, report = the_gate.check(pack_of(store, NEXT, "next"), order.contracts())
    refused = enter(root, snapshots, entry_desk, order, "next", NEXT, checks=report)
    assert refused.outcome == OUTCOME_REFUSED and "previous session 2026-10-14 is not archived" in refused.reason


def test_a_3_percent_move_refuses_the_entry_but_the_due_exit_fills(root, store, snapshots, alerts, exit_desk, clock,
                                                                    entry_desk, opened):  # fmt: skip
    """Judge 81: a crash or budget day is exactly when exits must run; the spot check stops new trades only."""
    spots = (24_900 * 1.03,)
    [result], report = review_at(root, store, snapshots, alerts, exit_desk, clock, NEXT, "next", (15, 15), DUE,
                                 spots=spots)  # fmt: skip
    assert "+3.00% from the previous close" in report.reason() and not report.prices_unverified
    assert result.outcome == OUTCOME_CLOSED and len(closing_fills(root)) == 4
    order = fly_order("t2", decided_at=at(15, 5, day=NEXT))
    pack = pack_of(store, NEXT, "next", spots=spots)
    _, report = gate(snapshots, alerts, NEXT, ExecutionWindow("next", store)).check(pack, order.contracts())
    refused = enter(root, snapshots, entry_desk, order, "next", NEXT, checks=report)
    assert refused.outcome == OUTCOME_REFUSED and "beyond 2%" in refused.reason


def test_an_unreadable_snapshot_s_alert_names_every_due_exit(root, store, snapshots, alerts, exit_desk, clock, opened):
    """No desk event can be written without a readable snapshot, so the gate's alert is where held-up exits show."""
    write_snapshot(store, "next", fly_rows(), at(15, 15, day=NEXT), at(15, 15, 40, day=NEXT), day=NEXT, sha="e" * 64)
    with open_desk_journal(BOOK1_RULES, root) as journal:
        due = exit_desk.due_exits(journal, NEXT, DUE)
        assert exit_desk.due_exits(journal, NEXT, {"t1": [StopLoss(0.0)]}) == []  # a price rule cannot be judged
    pack = pack_of(store, NEXT, "next")
    snapshot, report = gate(snapshots, alerts, NEXT, ExecutionWindow("next")).check(pack, due_exits=due)
    assert snapshot is None and due == ["t1 (time_exit: 2026-10-15 is on or after 2026-10-14 (13 days before expiry "
                                        "2026-10-27))"]  # fmt: skip
    assert alerts.sent[-1].endswith(f"exits due, waiting for a readable snapshot: {due[0]}")


def test_the_desk_refuses_a_report_on_another_snapshot_or_missing_a_leg(root, store, snapshots, entry_desk,
                                                                        exit_desk, opened):  # fmt: skip
    snapshot = snapshots.snapshot(DAY, "exec")
    unchecked_leg = passed(snapshot, fly_order("t9").contracts()[:3])
    with pytest.raises(ValueError, match="did not check the quotes"):
        enter(root, snapshots, entry_desk, fly_order("t9"), checks=unchecked_leg)
    write_snapshot(store, "else", fly_rows(), at(15, 16), at(15, 16, 40))
    with open_desk_journal(BOOK1_RULES, root) as journal, pytest.raises(ValueError, match="data checks ran on else"):
        exit_desk.review(BOOK1_RULES, snapshot, journal, {}, passed(snapshots.snapshot(DAY, "else")))


def test_the_committed_stale_snapshot_is_refused_by_the_real_checks(alerts):
    """The judge's fixture: A4's files of a capture taken at 13:31 IST and a pack recording it; the recorder's window
    is 14:55-15:10, so the decision is no new trade, with one alert."""
    pack = CommonPack(date(2026, 10, 14), json.loads((STALE / "common.json").read_text()))
    checks = build_data_checks([nse_files(CALENDAR.previous_session(pack.day))], CALENDAR)
    snapshots = RecordedExecutionSnapshots(LocalFolderStore(STALE / "quotes"))
    snapshot, report = DataGate(checks, snapshots, PackSnapshotSchedule(), alerts).check(pack)
    assert snapshot is not None and [f.check for f in report.failures] == ["snapshot window"]
    assert "captured 13:31:02-13:31:40, outside its window 14:55:00-15:10:00" in report.reason()
    assert report.prices_unverified and len(alerts.sent) == 1 and alerts.sent[0].endswith(report.reason())
