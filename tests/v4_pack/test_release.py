"""Story G10 part 2, criterion 2: the pack and its release record go through O9's DataStore; readers get them only
through the verified Drive cache; a missing, late or damaged release is refused."""

import json
from datetime import UTC, datetime

import pytest

from fno.constants import V4_DAY_SYSTEM_LATE
from fno.forecast_scoring.v4.days import DayFileError, parse_day
from fno.storage.data_store import DataStore
from fno.storage.drive_cache import DriveCache
from fno.storage.raw_store import RawFileConflict, RawFileStore
from fno.storage.receipts import ReceiptFolder
from fno.v4_pack.codec import pack_sha256
from fno.v4_pack.release import NotReleased, ReleasedPacks, parse_release, publish
from tests.v4_pack.test_pack_format import DAY, a_pack

AREA = "data"


class FakeDrive(RawFileStore):
    def __init__(self):
        self.files = {}

    def put(self, path, data):
        """Write-once, as every real store: the same bytes again change nothing, different bytes are refused."""
        if self.files.get(path, data) != data:
            raise RawFileConflict(path)
        self.files[path] = data

    def get(self, path):
        return self.files.get(path)

    def exists(self, path):
        return path in self.files

    def list(self, prefix):
        return sorted(p for p in self.files if p.startswith(prefix))


def stores(tmp_path):
    drive, receipts = FakeDrive(), ReceiptFolder(tmp_path / "receipts")
    store = DataStore(drive, AREA, receipts, "v4-pack", "run-1", clock=lambda: datetime(2026, 10, 22, 9, 2, tzinfo=UTC))
    return drive, store, ReleasedPacks(DriveCache(drive, receipts, tmp_path / "cache"), AREA)


def test_a_published_pack_is_read_back_verified_with_its_release_record(tmp_path):
    drive, store, packs = stores(tmp_path)
    record = publish(store, DAY, a_pack())
    assert sorted(drive.files) == ["data/v4/days/2026/2026-10-22.json", "data/v4/packs/2026/2026-10-22.json"]
    assert (tmp_path / "receipts/data/v4/days/2026/2026-10-22.json.sha256").is_file()
    assert packs.release(DAY) == record and packs.pack(record) == a_pack()
    assert record.pack_sha256 == pack_sha256(drive.files["data/v4/packs/2026/2026-10-22.json"])
    assert record.observed_by == a_pack().observed_by()


def test_g8_reads_the_release_record_in_part_1s_format(tmp_path):
    drive, store, _ = stores(tmp_path)
    record = publish(store, DAY, a_pack())
    body = json.loads(drive.files["data/v4/days/2026/2026-10-22.json"])
    found = parse_day(DAY.isoformat(), body)
    assert (found.label, found.pack_sha256, found.observed_by) == ("A", record.pack_sha256, record.observed_by)


def test_a_day_without_a_complete_pack_releases_a_system_late_record_and_no_pack(tmp_path):
    drive, store, packs = stores(tmp_path)
    record = publish(store, DAY, None)
    assert list(drive.files) == ["data/v4/days/2026/2026-10-22.json"]
    assert packs.release(DAY) == record and record.label == V4_DAY_SYSTEM_LATE
    with pytest.raises(NotReleased, match="system_late"):
        packs.pack(record)


def test_no_receipt_means_not_released(tmp_path):
    _, _, packs = stores(tmp_path)
    with pytest.raises(NotReleased, match="no release record"):
        packs.release(DAY)


def test_bytes_drive_returns_that_differ_from_the_receipt_are_never_used(tmp_path):
    drive, store, packs = stores(tmp_path)
    record = publish(store, DAY, a_pack())
    drive.files["data/v4/packs/2026/2026-10-22.json"] = b"{}"
    with pytest.raises(NotReleased, match="could not be verified"):
        packs.pack(record)


@pytest.mark.parametrize(("label", "path"), [("A", ""), (V4_DAY_SYSTEM_LATE, "v4/packs/2026/2026-10-22.json"),
                                             ("A", "v4/packs/2026/2026-10-23.json")])  # fmt: skip
def test_a_pack_path_that_does_not_fit_the_label_is_refused(label, path):
    body = {"day": "2026-10-22", "label": label, "pack_path": path, "pack_sha256": "" if path == "" and label != "A"
            else "a" * 64, "observed_by": "2026-10-22T14:31:09+05:30" if label == "A" else ""}  # fmt: skip
    with pytest.raises(DayFileError):
        parse_release("2026-10-22", json.dumps(body).encode())
