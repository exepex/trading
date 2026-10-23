"""The practice archive core (MS-SIM-e1)."""

import gzip
import json
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from fno.school.constants import RecordKind
from fno.school.contracts.codec import canonical_bytes
from fno.school.dashcam.names import counts_path, slot_file_path
from fno.school.fleet.counts_file import marks_path, opportunity_path
from fno.school.instructor.outputs.store import instructor_path
from fno.school.instructor.ports import InstructorKind
from fno.school.simulator.archive import names
from fno.school.simulator.archive.archive import (
    ArchiveDamaged,
    PracticeArchive,
    PracticeArchiveError,
    PracticeConflict,
    UnlabelledFile,
    check_labelled,
)
from fno.school.simulator.constants import PRACTICE_LABEL
from fno.storage.data_store import DataStore
from fno.storage.raw_store import RawFileStore
from fno.storage.receipts import ReceiptFolder
from tests.school.contracts.test_records import closed_record, trade_record

FIRST, LAST = date(2024, 3, 4), date(2024, 3, 6)
RUN = names.run_id(FIRST, LAST, ["NIFTY-M", "NIFTY-W"], ["median", "p75", "p95"], "abc1234", "deadbeef")
PATH = names.file_path(RUN, "median", "2024/03/04/1500.decisions.jsonl.gz")


def labelled_file(lines=2, label=PRACTICE_LABEL) -> bytes:
    """Real dashcam records, each line labelled as the practice dashcam writes it."""
    records = [trade_record(), closed_record()]
    rows = [
        b'{"label":' + json.dumps(label).encode() + b',"record":' + canonical_bytes(records[n % 2])
        + b',"type":"' + type(records[n % 2]).__name__.encode() + b'"}'
        for n in range(lines)
    ]  # fmt: skip
    return gzip.compress(b"".join(row + b"\n" for row in rows), mtime=0)


class DictDrive(RawFileStore):
    name = "dict drive"

    def __init__(self):
        self.files: dict[str, bytes] = {}

    def get(self, path):
        return self.files.get(path)

    def put(self, path, data):
        from fno.storage.raw_store import RawFileConflict

        if path in self.files and self.files[path] != data:
            raise RawFileConflict(path)
        self.files[path] = data


class FakePublisher:
    """Remembers the receipts it was asked to push, as the remote would."""

    def __init__(self, folder: ReceiptFolder):
        self.folder, self.pushed, self.commits = folder, {}, 0

    def publish(self, drive_path, what):
        from fno.storage.receipt_publisher import PushedReceipt

        self.commits += 1
        found = PushedReceipt(
            f"c{self.commits}", datetime(2026, 10, 23, 5, 0, tzinfo=UTC), self.folder.read(drive_path).sha256
        )
        self.pushed[drive_path] = found
        return found

    def published(self, drive_path):
        return self.pushed.get(drive_path)


class Reader:
    def __init__(self, drive):
        self.drive = drive

    def read(self, path):
        return self.drive.files[f"data/{path}"]


@pytest.fixture
def parts(tmp_path):
    drive, folder = DictDrive(), ReceiptFolder(tmp_path / "receipts")
    data = DataStore(drive, "data", folder, "practice archive", "run-1")
    publisher = FakePublisher(folder)
    return PracticeArchive(data, publisher, Reader(drive)), drive, publisher, folder


# ---- names ----------------------------------------------------------------------------------------------------------


def test_a_practice_path_never_starts_with_a_pilot_path_and_the_reverse():
    pilot = [
        slot_file_path(date(2026, 10, d), slot, kind) for d in (22, 23) for slot in ("15:00",) for kind in RecordKind
    ]
    pilot += [str(counts_path(date(2026, 10, d), "15:00")) for d in (22, 23)]
    pilot += [str(opportunity_path(date(2026, 10, d), "15:00")) for d in (22, 23)]
    pilot += [str(marks_path(date(2026, 10, d), "15:00")) for d in (22, 23)]
    pilot += [instructor_path(date(2026, 10, d), kind) for d in (22, 23) for kind in InstructorKind]
    for mine in (PATH, names.report_path(RUN), names.run_folder(RUN)):
        for theirs in pilot:
            assert not mine.startswith(theirs.split("/")[0] + "/") and not theirs.startswith(mine.split("/")[0] + "/")
        assert mine.split("/")[0] == names.PRACTICE_AREA != "school"


@pytest.mark.parametrize("bad", ["", "..", "a/b", "20240304_20240306_zz", "20240304_20240306_ABCDEF012345", "x" * 80])
def test_a_run_id_with_a_slash_dots_or_nothing_is_refused(bad):
    with pytest.raises(names.BadRunId):
        names.run_folder(bad)


@pytest.mark.parametrize(
    "scenario,relative", [("", "a"), ("me/dian", "a"), ("median", "/abs"), ("median", "../x"), ("median", "a/../b")]
)
def test_a_file_place_that_climbs_or_is_absolute_is_refused(scenario, relative):
    with pytest.raises(names.BadRunId):
        names.file_path(RUN, scenario, relative)


def test_the_run_id_is_short_and_follows_everything_the_run_depended_on():
    base = (FIRST, LAST, ["NIFTY-M"], ["median"], "abc1234", "dead")
    assert names.RUN_ID_PATTERN.fullmatch(names.run_id(*base)) and len(names.run_id(*base)) == 30
    assert names.run_id(*base) == names.run_id(*base)
    assert len({names.run_id(*base), names.run_id(FIRST, LAST, ["NIFTY-M", "NIFTY-W"], ["median"], "abc1234", "dead"),
                names.run_id(FIRST, LAST, ["NIFTY-M"], ["median", "p75"], "abc1234", "dead"),
                names.run_id(FIRST, LAST, ["NIFTY-M"], ["median"], "def5678", "dead"),
                names.run_id(FIRST, LAST, ["NIFTY-M"], ["median"], "abc1234", "beef")}) == 5  # fmt: skip


def test_the_receipts_folder_is_the_practice_one_and_exact():
    assert names.receipts_folder(RUN) == f"receipts/data/school-practice/{RUN}"


# ---- the label ------------------------------------------------------------------------------------------------------


def test_a_file_without_the_label_on_every_line_is_refused():
    check_labelled(PATH, labelled_file(3))
    mixed = gzip.compress(gzip.decompress(labelled_file(2)) + b'{"record":{},"type":"DriftRow"}\n', mtime=0)
    with pytest.raises(UnlabelledFile, match="line 3"):
        check_labelled(PATH, mixed)
    with pytest.raises(UnlabelledFile):
        check_labelled(PATH, labelled_file(1, label="paper"))


def test_a_file_that_is_not_canonical_record_lines_is_refused():
    for data in (b"plain text", gzip.compress(b"not json\n"), gzip.compress(b"")):
        with pytest.raises(PracticeArchiveError):
            check_labelled(PATH, data)
    with pytest.raises(PracticeArchiveError):
        check_labelled(PATH.replace(".jsonl.gz", ".bin"), labelled_file())


def test_a_text_file_needs_the_label_at_the_start_of_every_line():
    check_labelled(names.report_path(RUN), f"{PRACTICE_LABEL} | a\n\n{PRACTICE_LABEL} | b\n".encode())
    with pytest.raises(UnlabelledFile):
        check_labelled(names.report_path(RUN), f"{PRACTICE_LABEL} | a\nb\n".encode())


# ---- the archive ----------------------------------------------------------------------------------------------------


def test_a_file_is_saved_to_drive_and_its_receipt_is_pushed(parts):
    archive, drive, publisher, folder = parts
    done = archive.archive(RUN, PATH, labelled_file(), "practice")
    assert drive.files[f"data/{PATH}"] == labelled_file() and done.commit == "c1"
    assert folder.read(f"data/{PATH}").sha256 == done.sha256 and publisher.commits == 1
    archive.verify(done)


def test_archiving_twice_with_the_same_bytes_returns_the_same_file_and_makes_no_second_commit(parts):
    archive, _, publisher, _ = parts
    first = archive.archive(RUN, PATH, labelled_file(), "practice")
    again = archive.archive(RUN, PATH, labelled_file(), "practice")
    assert again == first and publisher.commits == 1


def test_other_bytes_for_an_archived_key_are_refused_and_nothing_is_written(parts):
    archive, drive, publisher, _ = parts
    archive.archive(RUN, PATH, labelled_file(2), "practice")
    with pytest.raises(PracticeConflict, match="rule broken"):
        archive.archive(RUN, PATH, labelled_file(3), "practice")
    assert drive.files[f"data/{PATH}"] == labelled_file(2) and publisher.commits == 1


def test_a_drive_conflict_without_a_pushed_receipt_is_refused_too(parts):
    archive, drive, publisher, _ = parts
    drive.files[f"data/{PATH}"] = b"older bytes"  # on Drive, never pushed
    with pytest.raises(PracticeConflict, match="rule broken"):
        archive.archive(RUN, PATH, labelled_file(), "practice")
    assert publisher.commits == 0


def test_a_path_outside_the_run_is_refused_before_anything_is_written(parts):
    archive, drive, publisher, _ = parts
    other = names.file_path(names.run_id(FIRST, LAST, ["X"], ["median"], "c", "i"), "median", "a.jsonl.gz")
    with pytest.raises(PracticeArchiveError, match="not in the run"):
        archive.archive(RUN, other, labelled_file(), "practice")
    assert not drive.files and publisher.commits == 0


def test_an_unlabelled_file_is_refused_before_anything_is_written(parts):
    archive, drive, publisher, _ = parts
    with pytest.raises(UnlabelledFile):
        archive.archive(RUN, PATH, labelled_file(1, label=""), "practice")
    assert not drive.files and publisher.commits == 0


def test_a_damaged_read_back_is_named(parts):
    archive, drive, _, _ = parts
    done = archive.archive(RUN, PATH, labelled_file(), "practice")
    drive.files[f"data/{PATH}"] = b"damaged"
    with pytest.raises(ArchiveDamaged):
        archive.verify(done)


def test_the_report_text_is_archived_and_its_sha_is_in_a_receipt(parts):
    archive, _, _, folder = parts
    text = f"{PRACTICE_LABEL} | local only\n{PRACTICE_LABEL} | window\n".encode()
    done = archive.archive(RUN, names.report_path(RUN), text, "practice report")
    import hashlib

    assert folder.read(f"data/{names.report_path(RUN)}").sha256 == hashlib.sha256(text).hexdigest() == done.sha256


def test_the_default_paths_are_in_the_practice_receipt_folder(parts):
    archive, _, _, folder = parts
    archive.archive(RUN, PATH, labelled_file(), "practice")
    receipt = folder.file_for(f"data/{PATH}")
    assert Path(receipt).relative_to(folder.folder).parts[:2] == ("data", "school-practice")


# ---- Judge H's minors (526 a to c) ----------------------------------------------------------------------------------


@pytest.mark.parametrize("tail", ["../../school/x.jsonl.gz", "a/../b.jsonl.gz", "a//b.jsonl.gz", "./a.jsonl.gz"])
def test_a_path_that_climbs_or_has_an_empty_part_is_refused_by_the_archive_itself(parts, tail):
    archive, drive, publisher, _ = parts
    with pytest.raises(PracticeArchiveError, match="not in the run"):
        archive.archive(RUN, f"{names.run_folder(RUN)}/{tail}", labelled_file(), "x")
    assert not drive.files and not publisher.pushed


def test_a_labelled_line_that_is_not_a_record_is_refused():
    label = {"label": PRACTICE_LABEL}
    for row in (
        label,
        {**label, "type": "NoSuchRecord", "record": {}},
        {**label, "type": "DriftRow", "record": {"n": 1}},
    ):
        data = gzip.compress(json.dumps(row).encode() + b"\n", mtime=0)
        with pytest.raises(PracticeArchiveError, match="canonical record lines"):
            check_labelled(PATH, data)


def test_a_text_file_that_is_not_utf8_is_refused_by_name():
    with pytest.raises(PracticeArchiveError, match="UTF-8"):
        check_labelled(names.report_path(RUN), b"\xff\xfe" + PRACTICE_LABEL.encode())
