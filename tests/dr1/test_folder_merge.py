"""Story DR1-0: two Drive folders with one name (22 Oct's `data/daily_runs/full`) merged into the copy holding the
verified files, through the real adapters over a fake Drive; nothing deleted, every receipt read back."""

import hashlib
from datetime import date
from types import SimpleNamespace

import pytest

from fno.storage.drive_items import DriveItems, PathAmbiguous
from fno.storage.folder_merge import FolderMerge
from fno.storage.raw_store import RawFileConflict
from fno.storage.receipts import Receipt, ReceiptFolder
from fno.storage.repair_cli import cmd_merge_folders
from tests.dr1.fake_drive import FakeDrive, store_on

FULL = "data/daily_runs/full"
RECEIPTED, ORPHAN = b'{"run": "f224c7"}', b'{"run": "39767f"}'
RECEIPTED_PATH = f"{FULL}/2026-10-22/20261022T100329Z-f224c7.json"
ORPHAN_PATH = f"{FULL}/2026-10-22/20261022T100328Z-39767f.json"


def raced(tmp_path, receipted_copy_first=False):
    """22 Oct's state: the older `full` holds the unreceipted log, the newer one the receipted log."""
    drive = FakeDrive()
    runs = drive.add(drive.add("root", "data"), "daily_runs")
    older, newer = drive.add(runs, "full"), drive.add(runs, "full")
    if receipted_copy_first:
        older, newer = newer, older
    drive.add(drive.add(older, "2026-10-22"), "20261022T100328Z-39767f.json", ORPHAN)
    drive.add(drive.add(newer, "2026-10-22"), "20261022T100329Z-f224c7.json", RECEIPTED)
    receipts = ReceiptFolder(tmp_path / "receipts")
    sha = hashlib.sha256(RECEIPTED).hexdigest()
    receipts.write(Receipt(RECEIPTED_PATH, sha, len(RECEIPTED), "2026-10-22T10:03:32+00:00", "daily-run", "f224c7"))
    merge = FolderMerge(DriveItems(store_on(drive)), receipts, store_on(drive))
    return drive, runs, merge, newer


def test_the_raced_folder_cannot_be_read_by_path_before_the_merge(tmp_path):
    drive, _, _, _ = raced(tmp_path)
    with pytest.raises(RawFileConflict):
        store_on(drive).get(RECEIPTED_PATH)


@pytest.mark.parametrize("receipted_copy_first", [False, True])
def test_the_copy_holding_the_verified_file_is_kept_whatever_its_age(tmp_path, receipted_copy_first):
    drive, runs, merge, kept_id = raced(tmp_path, receipted_copy_first)
    plan = merge.plan(FULL)
    assert plan.kept.id == kept_id and not plan.refusals
    assert [move.path for move in plan.moves] == [ORPHAN_PATH]
    assert merge.apply(plan, date(2026, 10, 23)) == []
    assert drive.named(runs, "full") == [kept_id]
    assert len(drive.named(runs, "full.merged-2026-10-23")) == 1  # renamed, never deleted
    store = store_on(drive)
    assert store.get(RECEIPTED_PATH) == RECEIPTED and store.get(ORPHAN_PATH) == ORPHAN  # both logs kept


def test_a_plan_changes_nothing_until_it_is_applied(tmp_path):
    drive, runs, merge, _ = raced(tmp_path)
    before = {i: dict(item) for i, item in drive.items.items()}
    merge.plan(FULL)
    assert drive.items == before


def test_two_copies_with_no_verified_file_are_a_tie_for_a_person(tmp_path):
    drive = FakeDrive()
    runs = drive.add(drive.add("root", "data"), "daily_runs")
    for _ in range(2):
        drive.add(runs, "full")
    merge = FolderMerge(DriveItems(store_on(drive)), ReceiptFolder(tmp_path / "receipts"), store_on(drive))
    plan = merge.plan(FULL)
    assert plan.kept is None and "a person decides" in plan.refusals[0]
    assert merge.apply(plan, date(2026, 10, 23)) == plan.refusals and len(drive.named(runs, "full")) == 2


def test_two_files_with_one_name_are_refused_before_anything_moves(tmp_path):
    drive, runs, merge, newer = raced(tmp_path)
    older = next(i for i in drive.named(runs, "full") if i != newer)
    drive.add(drive.named(older, "2026-10-22")[0], "20261022T100329Z-f224c7.json", b"other bytes")
    plan = merge.plan(FULL)
    assert plan.refusals and "both copies hold" in plan.refusals[0]
    before = {i: dict(item) for i, item in drive.items.items()}
    merge.apply(plan, date(2026, 10, 23))
    assert drive.items == before


def test_one_folder_needs_no_merge_and_a_doubled_folder_above_is_named(tmp_path):
    drive = FakeDrive()
    data = drive.add("root", "data")
    drive.add(drive.add(data, "daily_runs"), "full")
    merge = FolderMerge(DriveItems(store_on(drive)), ReceiptFolder(tmp_path / "receipts"), store_on(drive))
    assert not merge.plan(FULL).needed
    drive.add(data, "daily_runs")
    with pytest.raises(PathAmbiguous):
        merge.plan(FULL)


def test_the_command_prints_the_plan_and_applies_only_when_asked(tmp_path):
    drive, runs, merge, _ = raced(tmp_path)
    lines = []
    assert cmd_merge_folders(SimpleNamespace(path=FULL, apply=False), lines.append, merge) == 0
    assert lines[0].startswith(f"{FULL}: keep the copy created") and lines[1] == f"  move {ORPHAN_PATH}"
    assert len(drive.named(runs, "full")) == 2
    lines.clear()
    assert cmd_merge_folders(SimpleNamespace(path=FULL, apply=True), lines.append, merge) == 0
    assert lines[-1] == f"{FULL}: merged; every receipt under it reads back"
    assert len(drive.named(runs, "full")) == 1


def test_the_command_names_a_missing_path_in_one_line(tmp_path):
    drive = FakeDrive()
    merge = FolderMerge(DriveItems(store_on(drive)), ReceiptFolder(tmp_path / "receipts"), store_on(drive))
    lines = []
    assert cmd_merge_folders(SimpleNamespace(path=FULL, apply=True), lines.append, merge) == 1
    assert lines == [f"no Drive folder 'data' on the way to {FULL}"]


@pytest.mark.parametrize("damage, why", [("missing", "missing"), ("other bytes", "other bytes")])
def test_a_receipted_file_that_does_not_read_back_after_the_merge_is_named_and_fails(tmp_path, damage, why):
    drive, runs, merge, kept = raced(tmp_path)
    receipted = next(i for i, item in drive.items.items() if item["name"].endswith("f224c7.json"))
    plan = merge.plan(FULL)
    if damage == "missing":
        drive.items[receipted]["parent"] = "elsewhere"  # the file left the kept folder: the path finds nothing
    else:
        drive.items[receipted]["data"] = b"other bytes"
    assert merge.apply(plan, date(2026, 10, 23)) == [f"{RECEIPTED_PATH}: receipt not matched after the merge ({why})"]
    lines = []
    drive_again, _, merge_again, _ = raced(tmp_path / "again")
    receipted_again = next(i for i, item in drive_again.items.items() if item["name"].endswith("f224c7.json"))
    move = merge_again.items.move

    def move_and_damage(item, source, target):  # the receipted file changes while the merge runs
        move(item, source, target)
        drive_again.items[receipted_again]["data"] = b"other bytes"

    merge_again.items.move = move_and_damage
    assert cmd_merge_folders(SimpleNamespace(path=FULL, apply=True), lines.append, merge_again) == 1
    assert lines[-1] == f"{RECEIPTED_PATH}: receipt not matched after the merge (other bytes)"


def test_a_clean_merge_reads_every_receipt_back_and_exits_0(tmp_path):
    _, _, merge, _ = raced(tmp_path)
    plan = merge.plan(FULL)
    assert merge.apply(plan, date(2026, 10, 23)) == [] and merge.check(FULL) == []
