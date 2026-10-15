"""E8 rules 11 and 12: E8's own records are write-once files per account (a shadow version in its own folder), and a
handed-over entry's order is rebuilt from the decision run the run log recorded, never guessed."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from fno.constants import BOOK1_RULES, RUN_LOG_DECISIONS_STEP
from fno.desk.daily_ports import CommittedDecision
from fno.desk.owner_timing.outcomes import ENTRY
from fno.desk.owner_timing.pending import OrderMissing, PendingEntry, RunLogOrders
from fno.desk.owner_timing.timing_log import StoreTimingLog, TimingRecord
from fno.desk.run_log import RunLog
from fno.storage.raw_store import LocalFolderStore, RawFileConflict
from tests.desk.builders import DAY, at, fly_order
from tests.desk_owner_timing.fakes import ist
from tests.timetable.fakes import Decisions

DUE = ist(date(2026, 10, 15), 10, 15)


def record(account=BOOK1_RULES, reason="filled") -> TimingRecord:
    return TimingRecord(account, "verdict", "t1", ENTRY, 60, ist(DAY, 15, 16), DUE, DUE, "a16", "ab" * 32, "opened",
                        reason)  # fmt: skip


def test_records_and_alerts_are_kept_once_per_account_and_mark(tmp_path):
    store = LocalFolderStore(tmp_path)  # write-once, as Drive's own store
    log = StoreTimingLog(store, store)
    log.record(record())
    log.record(record("shadow:b1-v2"))
    log.alerted(BOOK1_RULES, "t1", ist(DAY, 15, 40))
    written = {p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*.json")}
    assert written == {
        "book1_rules/fills/t1-entry-20261015T1015.json", "shadow/b1-v2/fills/t1-entry-20261015T1015.json",
        "book1_rules/alerts/t1.json",
    }  # fmt: skip
    assert log.alert_time(BOOK1_RULES, "t1") == ist(DAY, 15, 40) and log.alert_time("book2_hybrid", "t1") is None
    log.record(record())  # a rerun writes the same bytes
    with pytest.raises(RawFileConflict):
        log.record(record(reason="something else"))


def logged(root, entry: dict) -> None:
    RunLog.open(root, DAY).record(RUN_LOG_DECISIONS_STEP, at(15, 12), at(15, 12), {}, {BOOK1_RULES: entry})


def decisions() -> Decisions:
    found = Decisions()
    run = CommittedDecision(BOOK1_RULES, "r1", "c1", at(15, 5), Path("r1"))
    found.add(run, (fly_order("t1"), fly_order("t2")), DAY)
    return found


def test_the_order_is_rebuilt_from_the_logged_decision_run(root):
    logged(root, {"run_id": "r1", "commit": "c1"})
    source = decisions()
    order = RunLogOrders(root, source, source).order(PendingEntry(BOOK1_RULES, "t2", DAY))
    assert order.proposal.trade_id == "t2"


@pytest.mark.parametrize(("entry", "trade_id"), [({}, "t1"), ({"run_id": "r1", "commit": "c1"}, "t9")],
                         ids=["no decision run logged", "trade not in the run"])  # fmt: skip
def test_an_order_that_cannot_be_rebuilt_is_refused(root, entry, trade_id):
    logged(root, entry)
    source = decisions()
    with pytest.raises(OrderMissing):
        RunLogOrders(root, source, source).order(PendingEntry(BOOK1_RULES, trade_id, DAY))
