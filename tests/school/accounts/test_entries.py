"""The read-only ledger read (orchestrator, 22 Oct 2026, for j's settlement before the session's first view):
`SchoolAccounts.entries` returns every recorded entry in order, writes nothing (no equity row, no account opened, no
push), pulls from Drive once per run under the lock, stops by name when the pull fails, and never returns half a
record."""

import pytest

from fno.books.account import AccountError, AccountWriter, PaperAccount
from fno.books.lock import AccountBusy, AccountLock
from fno.desk.private_files import PrivateFilesUnavailable
from fno.school.accounts.ledger_fills import ledger_fills
from fno.school.accounts.names import account_name
from tests.school.contracts import builders as b
from tests.school.contracts import conformance as c
from tests.school.execution.school_builders import CHARGES

from .account_builders import ACCOUNT_RS, NEXT, Sync, accounts, closing, marks, opening

FOLDER = ("journal", "shadow", "school-cs1-v1", "account")


def files(tmp_path) -> dict[str, bytes]:
    folder = tmp_path.joinpath(*FOLDER)
    return {p.name: p.read_bytes() for p in folder.iterdir() if p.name != ".lock"} if folder.exists() else {}


def test_entries_are_the_recorded_ledger_in_order(tmp_path):
    port, entry = accounts(tmp_path), opening(tmp_path)
    port.view("CS1@1", marks(), b.SESSION)
    port.record("CS1@1", entry)
    closed = closing(tmp_path, entry)
    port.record("CS1@1", closed)
    assert port.entries("CS1@1") == (entry, closed)
    rows = [r for r in PaperAccount(tmp_path, account_name("CS1@1")).ledger_rows() if r["trade_id"] == "p1"]
    assert len(rows) == len(entry.fill.legs) + len(closed.fill.legs)


def test_entries_write_nothing_no_equity_row_and_open_no_account(tmp_path):
    sync = Sync()
    port = accounts(tmp_path, sync=sync)
    assert port.entries("CS1@1") == () and files(tmp_path) == {}, "an account never opened stays unopened"
    port.view("CS1@1", marks(), b.SESSION)
    port.record("CS1@1", opening(tmp_path))
    before, pushes = files(tmp_path), len(sync.pushed)
    later = accounts(tmp_path, sync=sync)  # a new run: the session's first read is entries, before any view
    later.entries("CS1@1")
    later.entries("CS1@1")
    assert files(tmp_path) == before and len(sync.pushed) == pushes
    history = PaperAccount(tmp_path, account_name("CS1@1")).equity_history()
    assert [r["date"] for r in history] == [b.SESSION.isoformat()], "no row for the next session yet"
    assert later.view("CS1@1", marks(session=NEXT), NEXT).open_positions, "view still writes its row afterwards"


def test_entries_pull_once_per_run_under_the_lock(tmp_path):
    sync = Sync()
    port = accounts(tmp_path, sync=sync)
    port.entries("CS1@1")
    port.entries("CS1@1")
    port.view("CS1@1", marks(), b.SESSION)
    assert len(sync.pulled) == 1
    with AccountLock(tmp_path, account_name("CS1@1")), pytest.raises(AccountBusy, match="another writer"):
        accounts(tmp_path).entries("CS1@1")


def test_a_failed_pull_stops_by_name(tmp_path):
    class DriveDown(Sync):
        def pull(self, paths):
            raise PrivateFilesUnavailable("the private paper records in Drive could not be read (Drive down)")

    with pytest.raises(PrivateFilesUnavailable, match="could not be read"):
        accounts(tmp_path, sync=DriveDown()).entries("CS1@1")


def test_half_a_record_is_never_returned(tmp_path):
    port, entry = accounts(tmp_path), opening(tmp_path)
    port.view("CS1@1", marks(), b.SESSION)
    port.record("CS1@1", entry)
    half = ledger_fills(closing(tmp_path, entry), CHARGES)[0]
    with AccountLock(tmp_path, account_name("CS1@1")) as lock:
        AccountWriter(PaperAccount(tmp_path, account_name("CS1@1")), lock, ACCOUNT_RS).apply_fill(half)
    with pytest.raises(AccountError, match="disagree"):
        port.entries("CS1@1")


def test_school_accounts_pass_a3s_ledger_reader_check(tmp_path):
    port, entry = accounts(tmp_path), opening(tmp_path)
    c.check_ledger_reader(port, port, entry, closing(tmp_path, entry), marks(), b.SESSION)
