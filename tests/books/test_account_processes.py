"""Story E1 criteria 2-5 with real, separate operating-system processes (no mocks of the lock)."""

import json
import subprocess
import sys
import time
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest

from fno.books.lock import AccountBusy, AccountLock
from fno.composition import build_paper_account, open_account_writer
from fno.constants import BOOK1_RULES, BOOK2_HYBRID

WORKER = Path(__file__).with_name("account_worker.py")


@pytest.fixture
def root(tmp_path):
    for book in (BOOK1_RULES, BOOK2_HYBRID):
        with open_account_writer(book, tmp_path) as writer:
            writer.start(date(2026, 10, 13))
    return tmp_path


def launch(**spec) -> subprocess.Popen:
    return subprocess.Popen([sys.executable, str(WORKER), json.dumps(spec)], stdout=subprocess.PIPE, text=True)


def finish(process: subprocess.Popen) -> tuple[int, dict | None]:
    out, _ = process.communicate(timeout=60)
    return process.returncode, json.loads(out) if out.strip() else None


def fill_ids(root: Path, book: str) -> list[str]:
    return [f.fill_id for f in build_paper_account(book, root).fills()]


def test_two_writers_on_one_book_exactly_one_writes(root):
    start = time.time() + 1.5
    workers = [
        launch(root=str(root), book=BOOK1_RULES, fills=[[f"f-{n}", f"t-{n}", "buy", 100.0, 65]], start_at=start, hold=2)
        for n in (1, 2)
    ]
    results = [finish(w) for w in workers]
    assert sorted(code for code, _ in results) == [0, 3]  # one wrote, the other found the account busy
    winner = next(info for code, info in results if code == 0)
    loser = next(info for code, info in results if code == 3)
    assert "another writer holds the account" in loser["busy"]
    assert winner["applied"] == [True]
    assert len(fill_ids(root, BOOK1_RULES)) == 1  # the loser wrote nothing


def test_two_books_written_at_the_same_moment_both_succeed(root):
    start = time.time() + 1.5
    workers = [
        launch(root=str(root), book=book, fills=[[f"f-{book}", "t-1", "buy", 100.0, 65]], start_at=start, hold=2)
        for book in (BOOK1_RULES, BOOK2_HYBRID)
    ]
    assert [finish(w)[0] for w in workers] == [0, 0]
    assert fill_ids(root, BOOK1_RULES) == [f"f-{BOOK1_RULES}"] and fill_ids(root, BOOK2_HYBRID) == [f"f-{BOOK2_HYBRID}"]


def test_a_crashed_holders_lock_is_freed_only_after_its_lease_expires(root):
    code, _ = finish(launch(root=str(root), book=BOOK1_RULES, fills=[], lease=3.0, die="holding"))
    assert code == -9  # killed while holding the lock: its lease is still in the lock file
    with pytest.raises(AccountBusy, match="lease runs until"):
        AccountLock(root, BOOK1_RULES).acquire()  # holder gone, lease not expired: not taken over
    time.sleep(3.2)
    lock = AccountLock(root, BOOK1_RULES)
    with lock:
        assert lock.recovered_from is not None and lock.recovered_from.holder.pid != 0


def test_a_live_holder_keeps_its_lock_after_its_lease_expires(root):
    holder = launch(root=str(root), book=BOOK1_RULES, fills=[], lease=0.5, hold=4)
    time.sleep(2.0)  # lease long expired, holder still running and holding the lock
    with pytest.raises(AccountBusy):
        AccountLock(root, BOOK1_RULES).acquire()
    assert finish(holder)[0] == 0


def test_a_lease_naming_a_live_process_is_never_taken_over_even_when_expired(root):
    """The lease rule on its own (no flock held): an expired lease whose holder runs is still respected."""
    other = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
    try:
        lock = AccountLock(root, BOOK1_RULES)
        hour_ago = datetime.now(UTC) - timedelta(hours=1)
        lease = {"book": BOOK1_RULES, "start": hour_ago.isoformat(), "expiry": (hour_ago + timedelta(1e-5)).isoformat()}
        lease["holder"] = {"host": _host(), "pid": other.pid, "started": _start(other.pid)}
        lock.path.write_text(json.dumps(lease))
        with pytest.raises(AccountBusy, match="still alive"):
            lock.acquire()
        other.kill()
        other.wait()
        with lock:  # holder gone and lease expired: taken over
            assert lock.recovered_from.holder.pid == other.pid
    finally:
        other.kill()


@pytest.mark.parametrize("crash", ["before_view", "half_line"])
def test_a_restart_after_a_crash_mid_write_neither_loses_nor_repeats_a_fill(root, crash):
    fills = [["f-1", "t-1", "sell", 150.0, 65], ["f-2", "t-1", "buy", 50.0, 65], ["f-3", "t-1", "buy", 100.0, 65]]
    code, _ = finish(launch(root=str(root), book=BOOK1_RULES, fills=fills, lease=1.0, die=crash))
    assert code == -9
    expected_after_crash = ["f-1", "f-2"] if crash == "before_view" else ["f-1"]
    assert fill_ids(root, BOOK1_RULES) == expected_after_crash  # readers ignore a half-written line
    time.sleep(1.2)  # the crashed writer's lease expires
    code, info = finish(launch(root=str(root), book=BOOK1_RULES, fills=fills, lease=1.0))  # the same run, retried
    assert code == 0
    assert info["applied"] == ([False, False, True] if crash == "before_view" else [False, True, True])
    assert fill_ids(root, BOOK1_RULES) == ["f-1", "f-2", "f-3"]  # each fill exactly once
    ledger = build_paper_account(BOOK1_RULES, root).file("cash_ledger.csv").read_text()
    assert ledger.endswith("\n") and ledger.count("\n") == 5  # header, opening, three fills: no half line left
    account = build_paper_account(BOOK1_RULES, root)
    view = json.loads(account.file("positions.json").read_text())
    assert view == json.loads(json.dumps(account.summary()))  # the view was rebuilt from the ledger
    assert view["open_trades"][0]["legs"] == {"NIFTY-t-1-buy": 130, "NIFTY-t-1-sell": -65}


def _host() -> str:
    import socket

    return socket.gethostname()


def _start(pid: int) -> str:
    from fno.books.lock import process_start

    return process_start(pid)
