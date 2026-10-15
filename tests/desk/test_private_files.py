"""Story E2c: the private paper records in Drive (`PrivateFiles`) and the one-time move at the merge."""

from fno.books.cli import move_to_drive
from fno.constants import BOOKS
from fno.desk import wiring as desk_wiring
from fno.desk.private_files import ALREADY, DIFFERENT, UPLOADED, PrivateFiles
from fno.storage.index_store import LocalIndexStore

LEDGER = "journal/book1_rules/account/cash_ledger.csv"


def test_the_move_uploads_each_account_file_once_and_never_overwrites_other_bytes(root, tmp_path):
    drive = LocalIndexStore(tmp_path / "drive")
    files = PrivateFiles(lambda: drive, root)
    moved = files.move_accounts()
    assert moved[LEDGER] == UPLOADED and len(moved) == 3 * len(BOOKS)  # ledger, equity history and positions
    assert drive.get(LEDGER) == (root / LEDGER).read_bytes()
    assert set(files.move_accounts().values()) == {ALREADY}  # a repeated move changes nothing
    drive.replace(LEDGER, b"another ledger\n")
    assert files.move_accounts()[LEDGER] == DIFFERENT and drive.get(LEDGER) == b"another ledger\n"


def test_the_move_command_refuses_on_different_bytes_and_writes_no_daily_totals(root, tmp_path, monkeypatch, capsys):
    drive = LocalIndexStore(tmp_path / "drive")
    drive.replace(LEDGER, b"another ledger\n")
    monkeypatch.setattr(desk_wiring, "build_private_files", lambda root: PrivateFiles(lambda: drive, root))
    assert move_to_drive(root) == 1
    assert f"{LEDGER}: {DIFFERENT}" in capsys.readouterr().out
    assert not list(root.glob("journal/*/daily_totals.csv"))


def test_the_move_command_writes_each_book_s_first_daily_totals(root, tmp_path, monkeypatch, capsys):
    drive = LocalIndexStore(tmp_path / "drive")
    monkeypatch.setattr(desk_wiring, "build_private_files", lambda root: PrivateFiles(lambda: drive, root))
    assert move_to_drive(root) == 0
    totals = (root / "journal/book1_rules/daily_totals.csv").read_text().splitlines()
    assert totals == ["date,closed_equity_rs,open_trades,closed_trades,fills", "2026-10-14,2000000.00,0,0,0"]


def test_a_file_drive_does_not_hold_is_left_as_it_is_locally(root, tmp_path):
    before = (root / LEDGER).read_bytes()
    PrivateFiles(lambda: LocalIndexStore(tmp_path / "drive"), root).download()
    assert (root / LEDGER).read_bytes() == before
