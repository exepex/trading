"""Story DR1-0: a receipt for a Drive file saved without one, built from its own bytes and Drive's creation time;
refused when the path has a receipt, no file or two files."""

import hashlib
from types import SimpleNamespace

from fno.storage.drive_items import DriveItems
from fno.storage.receipt_repair import ReceiptRepair
from fno.storage.receipts import ReceiptFolder
from fno.storage.repair_cli import cmd_receipt
from tests.dr1.fake_drive import FakeDrive, store_on

PATH = "data/daily_runs/full/2026-10-22/20261022T100328Z-39767f.json"
LOG = b'{"run": "39767f"}'


class Committer:
    def __init__(self, line="receipts committed and pushed (1 file(s))"):
        self.line, self.whats = line, []

    def commit(self, what):
        self.whats.append(what)
        return self.line


def saved(tmp_path, copies=1):
    drive = FakeDrive()
    day = drive.add(drive.add(drive.add(drive.add("root", "data"), "daily_runs"), "full"), "2026-10-22")
    for _ in range(copies):
        drive.add(day, "20261022T100328Z-39767f.json", LOG)
    receipts = ReceiptFolder(tmp_path / "receipts")
    return ReceiptRepair(DriveItems(store_on(drive)), receipts), receipts


def args(apply):
    return SimpleNamespace(path=PATH, writer="daily-run", run_id="20261022T100328Z-39767f", apply=apply)


def test_the_receipt_is_the_files_own_digest_and_drives_creation_time(tmp_path):
    repair, receipts = saved(tmp_path)
    receipt = repair.receipt_for(PATH, "daily-run", "20261022T100328Z-39767f")
    assert receipt.sha256 == hashlib.sha256(LOG).hexdigest() and receipt.size == len(LOG)
    assert receipt.written_at == "2026-10-22T10:03:05+00:00" and receipts.read(PATH) is None  # nothing written yet


def test_the_command_writes_and_commits_only_with_apply(tmp_path):
    repair, receipts = saved(tmp_path)
    committer, lines = Committer(), []
    assert cmd_receipt(args(False), lines.append, repair, committer) == 0
    assert receipts.read(PATH) is None and committer.whats == []
    assert cmd_receipt(args(True), lines.append, repair, committer) == 0
    assert receipts.read(PATH).sha256 == hashlib.sha256(LOG).hexdigest()
    assert committer.whats == [f"DR1-0 repair of {PATH}"]


def test_an_existing_receipt_is_never_replaced(tmp_path):
    repair, _ = saved(tmp_path)
    assert cmd_receipt(args(True), [].append, repair, Committer()) == 0
    lines = []
    assert cmd_receipt(args(True), lines.append, repair, Committer()) == 1
    assert lines == [f"{PATH}: already has a receipt; it is never replaced"]


def test_two_files_or_none_are_refused(tmp_path):
    for copies, words in ((2, "2 files with this name"), (0, "no file in Drive")):
        repair, receipts = saved(tmp_path / str(copies), copies)
        lines = []
        assert cmd_receipt(args(True), lines.append, repair, Committer()) == 1
        assert words in lines[-1] and receipts.read(PATH) is None


def test_a_commit_the_committer_refuses_fails_the_command(tmp_path):
    repair, _ = saved(tmp_path)
    committer = Committer("receipts NOT committed: commit failed: hook. Commit receipts/ by hand")
    assert cmd_receipt(args(True), [].append, repair, committer) == 1


def test_a_path_through_a_doubled_folder_is_refused_in_one_line(tmp_path):
    drive = FakeDrive()
    runs = drive.add(drive.add("root", "data"), "daily_runs")
    drive.add(runs, "full"), drive.add(runs, "full")
    repair = ReceiptRepair(DriveItems(store_on(drive)), ReceiptFolder(tmp_path / "receipts"))
    lines = []
    assert cmd_receipt(args(True), lines.append, repair, Committer()) == 1
    assert lines == [f"2 Drive folders named 'full' on the way to {PATH}"]
