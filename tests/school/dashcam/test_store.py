"""Criteria 1, 4 and 5 (story MS-P1c): write-once, replay reads back exactly what was sealed, the conformance check."""

from dataclasses import replace

import pytest

from fno.school.constants import RecordKind
from fno.school.contracts.dashcam import ReplayConflict
from fno.school.contracts.seal import StaleSeal
from fno.school.dashcam.names import slot_file_path
from fno.school.dashcam.publisher import SealNotPushed
from fno.school.dashcam.replay import ReplayReader
from tests.school.contracts import builders as b
from tests.school.contracts import conformance as c
from tests.school.contracts.test_records import closed_record, outcome_record, trade_record
from tests.school.dashcam import harness

SLOT = "15:00"
RECORDS = (trade_record(), closed_record())
OTHER = (outcome_record(),)


@pytest.fixture
def cam(tmp_path):
    return harness.build(tmp_path)


def test_the_conformance_check(cam):
    c.check_dashcam(cam.store, b.SESSION, SLOT, RECORDS, OTHER)


def test_the_same_records_again_are_a_no_op_with_the_same_seal(cam):
    first = cam.store.seal(b.SESSION, SLOT, RecordKind.DECISIONS, RECORDS)
    receipts_before = sorted(p.name for p in (cam.repository / "receipts").rglob("*.sha256"))
    commits_before = harness.git(cam.repository, "rev-list", "--count", "HEAD")
    again = cam.store.seal(b.SESSION, SLOT, RecordKind.DECISIONS, RECORDS)
    assert again == first
    assert sorted(p.name for p in (cam.repository / "receipts").rglob("*.sha256")) == receipts_before
    assert harness.git(cam.repository, "rev-list", "--count", "HEAD") == commits_before


def test_other_records_for_a_sealed_key_are_a_replay_conflict_reported_as_rule_broken(cam):
    first = cam.store.seal(b.SESSION, SLOT, RecordKind.DECISIONS, RECORDS)
    with pytest.raises(ReplayConflict, match="rule broken"):
        cam.store.seal(b.SESSION, SLOT, RecordKind.DECISIONS, OTHER)
    assert cam.store.read(first) == RECORDS, "the sealed file is untouched"


def test_a_conflict_in_the_receipt_alone_is_also_a_replay_conflict(cam):
    cam.store.seal(b.SESSION, SLOT, RecordKind.DECISIONS, RECORDS)
    (cam.drive.folder / "data" / slot_file_path(b.SESSION, SLOT, RecordKind.DECISIONS)).unlink()  # Drive lost it
    with pytest.raises(ReplayConflict, match="rule broken"):
        cam.store.seal(b.SESSION, SLOT, RecordKind.DECISIONS, OTHER)
    assert not (cam.drive.folder / "data" / slot_file_path(b.SESSION, SLOT, RecordKind.DECISIONS)).exists(), (
        "the conflict is judged before Drive is touched"
    )


def test_the_seal_names_the_pushed_receipt_commit(cam):
    seal = cam.store.seal(b.SESSION, SLOT, RecordKind.DECISIONS, RECORDS)
    assert seal.commit in harness.git(cam.remote, "rev-list", "main")
    assert seal.path == slot_file_path(b.SESSION, SLOT, RecordKind.DECISIONS)
    assert seal.sha256 in (cam.repository / "receipts" / "data" / f"{seal.path}.sha256").read_text()


def test_a_receipt_that_cannot_be_pushed_gives_no_seal(tmp_path):
    cam = harness.build(tmp_path, push_to_remote=False)
    with pytest.raises(SealNotPushed):
        cam.store.seal(b.SESSION, SLOT, RecordKind.DECISIONS, RECORDS)


def test_replay_reads_back_exactly_the_records_sealed(cam):
    cam.store.seal(b.SESSION, SLOT, RecordKind.DECISIONS, RECORDS)
    cam.store.seal(b.SESSION, SLOT, RecordKind.OUTCOMES, OTHER)
    replay = ReplayReader(cam.store)
    assert replay.records(b.SESSION, SLOT, RecordKind.DECISIONS) == RECORDS
    assert replay.records(b.SESSION, SLOT, RecordKind.OUTCOMES) == OTHER
    assert [r.to_bytes() for r in replay.records(b.SESSION, SLOT, RecordKind.DECISIONS)] == [
        r.to_bytes() for r in RECORDS
    ]


def test_replay_of_an_empty_slot_says_nothing_is_sealed(cam):
    with pytest.raises(StaleSeal, match="nothing is sealed"):
        ReplayReader(cam.store).records(b.SESSION, SLOT, RecordKind.DECISIONS)


def test_a_sealed_file_with_one_changed_byte_is_refused_on_read(cam):
    seal = cam.store.seal(b.SESSION, SLOT, RecordKind.DECISIONS, RECORDS)
    cam.store.seal(b.SESSION, "15:01", RecordKind.DECISIONS, OTHER)
    damaged = replace(seal, sha256="00" * 32)
    with pytest.raises(StaleSeal):
        cam.store.read(damaged)


def test_drive_bytes_that_do_not_match_the_receipt_are_never_read(cam):
    seal = cam.store.seal(b.SESSION, SLOT, RecordKind.DECISIONS, RECORDS)
    (cam.drive.folder / "data" / seal.path).write_bytes(b"tampered")
    with pytest.raises(StaleSeal):
        cam.store.read(seal)


def test_an_empty_records_file_round_trips(cam):
    seal = cam.store.seal(b.SESSION, SLOT, RecordKind.DRIFT, ())
    assert cam.store.read(seal) == ()


def test_a_damaged_sibling_file_does_not_block_reading_a_good_one(cam):
    good = cam.store.seal(b.SESSION, SLOT, RecordKind.DECISIONS, RECORDS)
    sibling = cam.store.seal(b.SESSION, SLOT, RecordKind.OUTCOMES, OTHER)
    (cam.drive.folder / "data" / sibling.path).write_bytes(b"tampered")
    assert cam.store.read(good) == RECORDS
    with pytest.raises(StaleSeal):
        cam.store.read(sibling)


def test_a_stale_cached_copy_is_never_read_when_drive_no_longer_matches_the_receipt(cam):
    seal = cam.store.seal(b.SESSION, SLOT, RecordKind.DECISIONS, RECORDS)
    assert cam.store.read(seal) == RECORDS  # now cached
    (cam.drive.folder / "data" / seal.path).write_bytes(b"tampered")
    cached = next((cam.repository.parent / "cache").rglob("*.jsonl.gz"))
    cached.write_bytes(b"also tampered")
    with pytest.raises(StaleSeal):
        cam.store.read(seal)


def test_the_reader_alone_refuses_a_stale_cached_copy(cam):
    seal = cam.store.seal(b.SESSION, SLOT, RecordKind.DECISIONS, RECORDS)
    cam.store.read(seal)
    (cam.drive.folder / "data" / seal.path).write_bytes(b"tampered")
    next((cam.repository.parent / "cache").rglob("*.jsonl.gz")).write_bytes(b"also tampered")
    with pytest.raises(StaleSeal, match="SHA-256"):
        cam.store.reader.read(seal.path)


def test_a_push_that_failed_earlier_is_pushed_by_the_rerun(tmp_path):
    cam = harness.build(tmp_path, push_to_remote=False)
    with pytest.raises(SealNotPushed):
        cam.store.seal(b.SESSION, SLOT, RecordKind.DECISIONS, RECORDS)  # committed locally, push failed
    harness.git(cam.repository, "remote", "set-url", "origin", str(cam.remote))
    seal = cam.store.seal(b.SESSION, SLOT, RecordKind.DECISIONS, RECORDS)
    assert seal.commit in harness.git(cam.remote, "rev-list", "main")


def test_a_fresh_checkout_returns_the_existing_seal_and_makes_no_second_receipt(tmp_path):
    cam = harness.build(tmp_path)
    first = cam.store.seal(b.SESSION, SLOT, RecordKind.DECISIONS, RECORDS)
    other = tmp_path / "other"
    other.mkdir()
    fresh = harness.build(other)  # a second container: its own checkout, the same Drive and remote
    fresh_drive = cam.drive
    harness.git(fresh.repository, "remote", "set-url", "origin", str(cam.remote))
    harness.git(fresh.repository, "pull", "-q", "--no-rebase", "--allow-unrelated-histories", "origin", "main")
    (fresh.repository / "receipts" / "data" / f"{first.path}.sha256").unlink()  # its checkout lacks the receipt
    fresh.store.data.drive = fresh_drive
    assert fresh.store.seal(b.SESSION, SLOT, RecordKind.DECISIONS, RECORDS) == first
    with pytest.raises(ReplayConflict):
        fresh.store.seal(b.SESSION, SLOT, RecordKind.DECISIONS, OTHER)


def test_find_names_the_seal_of_a_sealed_key_and_nothing_for_another(cam):
    assert cam.store.find(b.SESSION, SLOT, RecordKind.DECISIONS) is None
    seal = cam.store.seal(b.SESSION, SLOT, RecordKind.DECISIONS, RECORDS)
    assert cam.store.find(b.SESSION, SLOT, RecordKind.DECISIONS) == seal
    assert cam.store.find(b.SESSION, SLOT, RecordKind.OUTCOMES) is None
    assert cam.store.find(b.SESSION, "15:01", RecordKind.DECISIONS) is None


def test_find_is_none_for_a_file_whose_receipt_never_reached_the_remote(tmp_path):
    cam = harness.build(tmp_path, push_to_remote=False)
    with pytest.raises(SealNotPushed):
        cam.store.seal(b.SESSION, SLOT, RecordKind.DECISIONS, RECORDS)
    assert cam.store.find(b.SESSION, SLOT, RecordKind.DECISIONS) is None, "unpushed means unsealed: a rerun must seal"
