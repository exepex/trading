"""Story E4: the fill code never reaches an order function (criterion 6), every desk write needs the book's lock, a
crash mid-write loses or repeats nothing, and quote age is marked unknown only when the provider gave no timestamp."""

import ast
import sys
import types
from pathlib import Path

import pytest

import fno.composition
import fno.providers
from fno.books.account import AccountError, PaperAccount
from fno.config import ROOT, load_config
from fno.constants import BOOK1_RULES, OUTCOME_CLOSED, OUTCOME_OPENED
from fno.desk.csv_log import IdempotentCsvLog, LogConflict
from fno.desk.exit_rules import TimeExit
from fno.desk.records import DeskEvent, DeskRecords
from fno.desk.snapshot import parse_execution_snapshot
from fno.desk.wiring import build_entry_desk, build_execution_snapshots, build_exit_desk, open_desk_journal
from fno.quotes.recorder import QuoteSnapshotRecorder

from .builders import DAY, DictStore, at, enter, fly_order, fly_rows, passed, write_snapshot

DESK = ROOT / "fno" / "desk"
ORDER_CALLS = ("place_order", "modify_order", "cancel_order", "order")


class Trap:
    """Any use of it (an order call, a quote request) fails the test."""

    calls: list[str] = []

    def __getattr__(self, name):
        Trap.calls.append(name)
        raise AssertionError(f"the fill code reached the provider: {name}")


def test_the_desk_imports_no_provider_or_broker_and_calls_no_order_function():
    for path in DESK.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = [n.module or "" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
        imports += [a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names]
        assert not [m for m in imports if "providers" in m or "growwapi" in m], path.name
        calls = [n.func.attr for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)]
        assert not set(calls) & set(ORDER_CALLS), path.name


def test_a_full_day_of_fills_and_exits_never_touches_a_provider(root, tmp_path, monkeypatch, clock):
    Trap.calls = []
    for module in (fno.providers, fno.composition):
        monkeypatch.setattr(module, "get_provider", lambda *a, **k: Trap())
    monkeypatch.setitem(sys.modules, "growwapi", types.SimpleNamespace(GrowwAPI=Trap()))
    folder = tmp_path / "quotes"
    store = build_execution_snapshots(folder).store
    write_snapshot(store, "exec", fly_rows(), at(15, 15), at(15, 15, 40))
    cfg = load_config(ROOT / "config.yaml")
    entry, exit_ = build_entry_desk(cfg), build_exit_desk(cfg)
    entry.clock = exit_.clock = clock
    snapshots = build_execution_snapshots(folder)
    assert enter(root, snapshots, entry, fly_order()).outcome == OUTCOME_OPENED
    next_day = DAY.replace(day=DAY.day + 1)
    write_snapshot(store, "next", fly_rows(), at(15, 15, day=next_day), at(15, 15, 40, day=next_day), day=next_day)
    clock.set(at(15, 20, day=next_day))
    snapshot = snapshots.snapshot(next_day, "next")
    with open_desk_journal(BOOK1_RULES, root) as journal:
        [result] = exit_.review(BOOK1_RULES, snapshot, journal, {"t1": [TimeExit(13)]}, passed(snapshot))
    assert result.outcome == OUTCOME_CLOSED and Trap.calls == []


def test_desk_writes_need_the_book_s_lock_held(root):
    with open_desk_journal(BOOK1_RULES, root) as journal:
        pass  # the lock is released on exit
    event = DeskEvent("e1", DAY, BOOK1_RULES, "fixture-fly-v1", "t1", "d1", "exec", "0" * 64, OUTCOME_OPENED, "test")
    with pytest.raises(AccountError, match="single-writer lock"):
        journal.record_event(event)
    assert DeskRecords(PaperAccount(root, BOOK1_RULES)).event_rows() == []


def test_the_desk_log_drops_a_line_cut_short_by_a_crash_and_refuses_a_reused_key(tmp_path):
    log = IdempotentCsvLog(tmp_path / "log.csv", tmp_path / "log.csv.tmp", ("id", "value"), "id")
    assert log.append({"id": "a", "value": "1"}) and not log.append({"id": "a", "value": "1"})
    with open(log.path, "a", encoding="utf-8") as fh:
        fh.write("b,2")  # a crash before the newline
    assert log.rows() == [{"id": "a", "value": "1"}]
    assert log.append({"id": "b", "value": "2"}) and [r["id"] for r in log.rows()] == ["a", "b"]
    with pytest.raises(LogConflict, match="different row"):
        log.append({"id": "a", "value": "9"})


def test_quote_age_is_unknown_without_a_provider_timestamp_and_known_with_one():
    store = DictStore()
    rows = fly_rows()
    rows[0]["quote_time"] = "2026-10-14T15:15:02+05:30"  # NSE's page time
    write_snapshot(store, "exec", rows, at(15, 15), at(15, 15, 40))
    path = QuoteSnapshotRecorder.path
    snapshot = parse_execution_snapshot(
        DAY, "exec", store.get(path(DAY, "exec.csv")), store.get(path(DAY, "exec.meta.json"))
    )
    assert [q.quote_age_unknown for q in snapshot.quotes.values()] == [False, True, True, True]


def test_the_desk_s_files_stay_inside_the_book_s_account_folder(root):
    records = DeskRecords(PaperAccount(root, BOOK1_RULES))
    folder = Path(root) / "journal" / BOOK1_RULES / "account"
    assert records.fills.path.parent == folder and records.events.path.parent == folder
