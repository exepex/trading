"""REH1, acceptance 1 and 5: every write of a rehearsal lands under `dryrun/<run_id>/`; the real record is read but
never written; a real file is seen only once the replay clock has reached its receipt's time."""

from datetime import UTC, datetime

import pytest

from fno.rehearsal.drive import DryrunDrive, RehearsalWriteRefused
from fno.rehearsal.visibility import Visibility
from fno.storage.receipts import Receipt, ReceiptFolder

from .fakes import RecordingDrive

ROOT = "dryrun/r1"
CLOSE = "data/closes/2026/10/2026-10-23.first.raw.json"


def drive(real, visible=lambda path: True):
    return DryrunDrive(real, ROOT, visible)


def test_every_write_lands_under_the_rehearsal_s_folder_and_the_real_record_is_untouched():
    real = RecordingDrive({"paper/journal/book1_rules/account/ledger.csv": b"real"})
    store = drive(real)
    store.put("data/x.json", b"new")
    assert real.writes == [f"{ROOT}/data/x.json"] and store.get("data/x.json") == b"new"
    assert store.get("paper/journal/book1_rules/account/ledger.csv") == b"real"  # the real state is read
    assert store.file_id("paper/journal/book1_rules/account/ledger.csv") is None  # its ID is never handed out
    store.put("paper/journal/book1_rules/account/ledger.csv", b"rehearsed")  # an index file's first write: a copy
    file_id = store.file_id("paper/journal/book1_rules/account/ledger.csv")
    store.replace_contents(file_id, b"again")
    assert real.files["paper/journal/book1_rules/account/ledger.csv"] == b"real"
    assert all(path.startswith(f"{ROOT}/") for path in real.writes)


def test_a_replace_of_any_id_the_rehearsal_did_not_find_under_its_folder_is_refused_before_any_write():
    real = RecordingDrive({"paper/a.csv": b"real"})
    with pytest.raises(RehearsalWriteRefused, match="no write to the real Drive record"):
        drive(real).replace_contents("id:paper/a.csv", b"x")
    assert real.writes == [] and real.files["paper/a.csv"] == b"real"


def test_listings_join_the_visible_real_files_and_the_rehearsal_s_own():
    real = RecordingDrive({"data/c/old.json": b"1", "data/c/late.json": b"2", "data/c/sub/x": b"3"})
    store = drive(real, visible=lambda path: not path.endswith("late.json"))
    store.put("data/c/mine.json", b"4")
    assert set(store.checksums("data/c")) == {"old.json", "mine.json"} and store.folders("data/c") == ["sub"]
    assert store.get("data/c/late.json") is None and store.metadata("data/c/late.json", "id") is None


def test_a_file_is_visible_only_once_the_replay_clock_reaches_its_receipt(tmp_path):
    receipts = ReceiptFolder(tmp_path)
    receipts.write(Receipt(CLOSE, "a" * 64, 10, "2026-10-23T10:10:09+00:00", "closes read", "r"))  # 15:40:09 IST
    now = {"at": datetime(2026, 10, 23, 8, 35, tzinfo=UTC)}  # 14:05 IST
    visible = Visibility(receipts, lambda: now["at"])
    assert not visible(CLOSE) and not visible("data/never/recorded.json")
    now["at"] = datetime(2026, 10, 23, 10, 11, tzinfo=UTC)  # 15:41 IST
    assert visible(CLOSE) and visible("paper/journal/book1_rules/account/ledger.csv")  # state: read as it is
