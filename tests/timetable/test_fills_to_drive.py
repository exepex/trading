"""Story E2c criteria 1, 2, 4 and 5 on E3's daily run with the accounts in a fake Drive: a fixture day that opens a
fly (Book 1's t1, Book 2's b1) and a later day that closes t1, each day in a fresh container."""

import csv
import io
import re
from datetime import date

import pytest

from fno.books.account import EQUITY_HISTORY_FILE, POSITIONS_FILE, PaperAccount
from fno.constants import BOOK1_RULES, BOOK2_HYBRID, CASH_LEDGER_FILE, OUTCOME_CLOSED, OUTCOME_OPENED
from fno.desk.daily_run import RunStopped
from fno.desk.exit_rules import TimeExit
from fno.desk.records import EVENTS_FILE, FILLS_FILE, DeskRecords
from fno.desk.run_log import RunLog
from fno.desk.status import open_positions
from fno.storage.index_store import LocalIndexStore
from tests.desk.builders import FLY_QUOTES, at

from .drive_day import drive_run, fresh_container
from .fakes import C4, Decisions, Rules
from .test_daily_run import BOOKS, NORMAL, decided, run_day

CLOSE_DAY = date(2026, 10, 16)  # t1's time exit is due from 16 Oct (27 Oct expiry)
NUMBER = re.compile(r"(?<![\w.])-?\d+\.\d+(?![\w.])")  # decimals only: counts, strikes and times are integers


def opening_week(root, tmp_path, alerts, store=None):
    decisions = Decisions()
    decisions.add(*decided(BOOK1_RULES, "t1", NORMAL), NORMAL)
    decisions.add(*decided(BOOK2_HYBRID, "b1", NORMAL, (15, 6)), NORMAL)
    return drive_run(root, tmp_path, alerts, BOOKS, decisions, C4(), Rules({"t1": [TimeExit(11)]}), store)


def private_values(root) -> set[float]:
    """Every price, mark and open-book cash of the two days: the fills, the snapshot's quotes and their mids."""
    values = {v for bid, ask in FLY_QUOTES.values() for v in (bid, ask, (bid + ask) / 2)}
    for book in BOOKS:
        account = PaperAccount(root, book)
        for row in account.ledger_rows()[1:]:
            values |= {float(row[k]) for k in ("quoted_price", "fill_price", "amount_rs", "cash_after_rs")}
        values |= {float(row["price"]) for row in DeskRecords(account).fill_rows()}
    return {round(v, 2) for v in values}


def public_totals(root, book) -> list[dict]:
    return list(csv.DictReader(io.StringIO((root / "journal" / book / "daily_totals.csv").read_text())))


def test_no_committed_file_holds_a_price_a_mark_or_an_open_book_s_cash(root, tmp_path, alerts):
    """Criterion 1: both days end to end, the pack step and Book 1's private pack included."""
    run, clock, _, commits, files = opening_week(root, tmp_path, alerts)
    run_day(run, clock, NORMAL)
    fresh_container(root)
    assert run_day(run, clock, CLOSE_DAY).result("exits")[BOOK1_RULES]["results"][0]["outcome"] == OUTCOME_CLOSED
    files.download(CLOSE_DAY)
    # a flat book's cash is its closed equity by definition: public as closed equity, so not counted as leaked
    closed = {round(float(r["closed_equity_rs"]), 2) for book in BOOKS for r in public_totals(root, book)}
    secret = private_values(root) - closed
    committed = {p.relative_to(root).as_posix(): p.read_text(encoding="utf-8") for p in commits.paths}
    assert "journal/book1_rules/packs/2026-10-14/private.sha256" in committed
    assert not [name for name in committed if "/account/" in name or name.endswith("private.json")]
    ledger = (root / "journal/book1_rules/account/cash_ledger.csv").read_text()
    assert len(secret & _numbers(ledger)) > 10  # the scan does see prices and cash where they are
    leaks = {name: hits for name, text in committed.items() if (hits := secret & _numbers(text))}
    assert leaks == {}


def test_the_daily_totals_match_the_drive_account_by_hand(root, tmp_path, alerts):
    """Criterion 2: one entry on 14 Oct, the same trade closed on 16 Oct (net Rs -513.64 in the run log)."""
    run, clock, *_ = opening_week(root, tmp_path, alerts)
    run_day(run, clock, NORMAL)
    fresh_container(root)
    run_day(run, clock, CLOSE_DAY)
    rows = public_totals(root, BOOK1_RULES)
    assert list(rows[0]) == ["date", "closed_equity_rs", "open_trades", "closed_trades", "fills"]
    assert [list(r.values()) for r in rows] == [
        ["2026-10-14", "2000000.00", "1", "0", "4"],
        ["2026-10-16", "1999486.36", "0", "1", "4"],
    ]
    ledger = PaperAccount(root, BOOK1_RULES).ledger_rows()  # the Drive copy: opening plus the eight legs' amounts
    assert round(sum(float(r["amount_rs"]) for r in ledger), 2) == 1999486.36


class FailingWrites(LocalIndexStore):
    """Drive answering 503 once, for the first write of the named account file of Book 1."""

    def __init__(self, folder, name=None):
        super().__init__(folder)
        self.name = name

    def replace(self, path, data):
        if self.name and path == f"journal/{BOOK1_RULES}/account/{self.name}":
            self.name = None
            raise OSError("Drive answered 503")
        super().replace(path, data)


@pytest.mark.parametrize("name", [FILLS_FILE, CASH_LEDGER_FILE, POSITIONS_FILE, EQUITY_HISTORY_FILE, EVENTS_FILE])
def test_a_failed_drive_write_of_any_file_stops_the_run_and_the_rerun_fills_once(root, tmp_path, alerts, name):
    """Criterion 4 (judge 159): the push stops part way, after any of the five files; the rerun, in a new container,
    completes from what Drive holds and fills each leg exactly once."""
    store = FailingWrites(tmp_path / "drive")
    run, clock, _, commits, files = opening_week(root, tmp_path, alerts, store)
    store.name = name
    with pytest.raises(RunStopped):
        run_day(run, clock, NORMAL)
    assert len(alerts.sent) == 1 and "step fills" in alerts.sent[0] and "could not be written" in alerts.sent[0]
    assert not [m for _, m in commits.made if m.endswith("step fills")]
    fresh_container(root)
    log = run.run(NORMAL)  # later the same day
    assert log.result("fills")["t1"]["outcome"] == OUTCOME_OPENED and "exits" in log.steps
    fresh_container(root)
    files.download()
    account = PaperAccount(root, BOOK1_RULES)
    assert len(account.fills()) == len(DeskRecords(account).fill_rows()) == 4  # each leg once, in both files
    assert [e["outcome"] for e in DeskRecords(account).event_rows()] == [OUTCOME_OPENED]
    assert [p.trade_id for p in open_positions(DeskRecords(account))] == ["t1"]


class FailingReads(LocalIndexStore):
    def __init__(self, folder):
        super().__init__(folder)
        self.failing = False

    def get(self, path):
        if self.failing:
            raise OSError("Drive token expired")
        return super().get(path)


def test_a_stop_at_the_download_blocks_the_next_session_s_entries(root, tmp_path, alerts):
    """Judge 159 should-fix 1: a run stopped before any step (the download) leaves no log; once the desk has run
    before (12 Oct's log), the missing 13 Oct log blocks 14 Oct's entries, and 14 Oct's exits still run."""
    store = FailingReads(tmp_path / "drive")
    run, clock, *_ = opening_week(root, tmp_path, alerts, store)
    earlier = RunLog.open(root, date(2026, 10, 12))
    for step in ("versions", "exits"):
        earlier.record(step, at(15, 20, day=earlier.day), at(15, 20, day=earlier.day), {}, {})
    store.failing = True
    with pytest.raises(RunStopped, match="the download of the private paper records"):
        run_day(run, clock, date(2026, 10, 13))
    store.failing = False
    alerts.sent.clear()
    log = run_day(run, clock, NORMAL)
    assert "blocked" in log.result("fills") and "2026-10-13" in log.result("fills")["blocked"]
    assert len(alerts.sent) == 1 and list(log.steps)[-1] == "exits"


def stopped_before_exits(root, day):
    log = RunLog.open(root, day)
    log.record("versions", at(14, 58, day=day), at(14, 58, day=day), {}, {})  # and no step after it


@pytest.mark.parametrize("stopped", [True, False])
def test_a_last_session_stopped_before_its_exits_blocks_today_s_entries_only(root, tmp_path, alerts, stopped):
    """Criterion 5: 13 Oct's run stopped before its exits; on 14 Oct nothing opens, one alert, the exits still run."""
    run, clock, *_ = opening_week(root, tmp_path, alerts)
    previous = date(2026, 10, 13)
    if stopped:
        stopped_before_exits(root, previous)
    log = run_day(run, clock, NORMAL)
    assert list(log.steps)[-1] == "exits" and BOOK1_RULES in log.result("exits")
    if stopped:
        assert log.result("fills") == {"blocked": f"no new entry: the run of {previous} stopped before its exits "
                                                  "(they run today; the next session opens as usual)"}  # fmt: skip
        assert len(alerts.sent) == 1 and str(previous) in alerts.sent[0]
    else:
        assert log.result("fills")["t1"]["outcome"] == OUTCOME_OPENED and alerts.sent == []


def _numbers(text: str) -> set[float]:
    return {round(float(n), 2) for n in NUMBER.findall(text)}
