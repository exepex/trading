"""Story MS-P1c follow-up (orchestrator's go, 23 Oct 2026): a run stopped after its Drive write and before its receipt's
push left a file with no receipt on `main`; the writer's rerun adopts it when it is the key's file and the writer's
own, and stops by name when it is not, never sealing over it. On the production store, publisher and git, Drive a
local folder (`harness`)."""

import gzip
from dataclasses import replace
from datetime import timedelta

import pytest

from fno.school.constants import RecordKind
from fno.school.contracts.dashcam import DashcamStuck, ReplayConflict
from fno.school.contracts.slot_file import encode_slot_file
from fno.school.dashcam.adoption import adoptable
from fno.school.dashcam.names import slot_file_path
from fno.storage.receipt_publisher import SealNotPushed
from tests.school.contracts import builders as b
from tests.school.contracts.test_records import closed_record, outcome_record, trade_record
from tests.school.dashcam import harness

SLOT = "15:00"
RECORDS = (trade_record(), closed_record())
REDECIDED = (closed_record(),)  # what a rerun decides now: a driver past its limit, a capture landed since
ALL = lambda record: True  # noqa: E731 - every record the writer's own
STUCK = "dashcam stuck: stored file unverifiable"


def stopped_before_push(tmp_path, records=RECORDS, kind=RecordKind.DECISIONS):
    """A run that saved the file to Drive and stopped before its receipt reached `main`; the next container."""
    cam = harness.build(tmp_path, push_to_remote=False)
    with pytest.raises(SealNotPushed):
        cam.store.seal(b.SESSION, SLOT, kind, records)
    return cam, harness.another_checkout(cam, tmp_path, "next")


def put_on_drive(cam, kind, payload: bytes, session=b.SESSION):
    cam.drive.put(f"{harness.AREA}/{slot_file_path(session, SLOT, kind)}", payload)


def remote_log(cam) -> str:
    return harness.git(cam.remote, "log", "--format=%s", "main")


def test_the_stuck_session_is_adopted_and_its_stored_records_stand(tmp_path):
    _, rerun = stopped_before_push(tmp_path)
    assert rerun.store.find(b.SESSION, SLOT, RecordKind.DECISIONS) is None  # a reader never adopts
    seal = rerun.store.recover(b.SESSION, SLOT, RecordKind.DECISIONS, ALL)
    assert seal is not None and rerun.store.read(seal) == RECORDS
    assert "adopted" in remote_log(rerun).splitlines()[0] and seal.commit in harness.git(
        rerun.remote, "rev-list", "main"
    )
    assert rerun.store.find(b.SESSION, SLOT, RecordKind.DECISIONS) == seal
    assert rerun.store.seal(b.SESSION, SLOT, RecordKind.DECISIONS, RECORDS) == seal
    with pytest.raises(ReplayConflict):  # what the rerun decided now never replaces the record
        rerun.store.seal(b.SESSION, SLOT, RecordKind.DECISIONS, REDECIDED)


def test_nothing_stored_and_nothing_sealed_recovers_nothing(tmp_path):
    cam = harness.build(tmp_path)
    assert cam.store.recover(b.SESSION, SLOT, RecordKind.DECISIONS, ALL) is None


@pytest.mark.parametrize(
    "why, kind, payload, belongs",
    [
        ("unreadable", RecordKind.DECISIONS, b"not a gzip file", ALL),
        (
            "not canonical",
            RecordKind.DECISIONS,
            gzip.compress(gzip.decompress(encode_slot_file(RECORDS)), mtime=1),
            ALL,
        ),
        ("a record that is not decisions", RecordKind.DECISIONS, encode_slot_file((outcome_record(),)), ALL),
        ("a record that is not drift", RecordKind.DRIFT, encode_slot_file(RECORDS), ALL),
        (
            "another session or slot",
            RecordKind.DECISIONS,
            encode_slot_file((trade_record(slot="15:01"),)),
            ALL,
        ),
        ("not this fleet's", RecordKind.DECISIONS, encode_slot_file(RECORDS), lambda record: False),
    ],
    ids=lambda value: value if isinstance(value, str) else "",
)
def test_a_stored_file_that_is_not_the_key_s_or_the_writer_s_stops_by_name_and_publishes_nothing(
    tmp_path, why, kind, payload, belongs
):
    cam = harness.build(tmp_path)
    put_on_drive(cam, kind, payload)
    before = remote_log(cam)
    with pytest.raises(DashcamStuck, match=STUCK) as stuck:
        cam.store.recover(b.SESSION, SLOT, kind, belongs)
    assert why in str(stuck.value) and f"{b.SESSION} {SLOT} {kind}" in str(stuck.value)
    assert remote_log(cam) == before, "a refused file was published"
    assert not (cam.repository / "receipts" / harness.AREA / f"{slot_file_path(b.SESSION, SLOT, kind)}.sha256").exists()


def test_a_settlement_s_outcome_filled_on_its_expiry_day_is_adopted_in_a_later_session_s_file():
    """An expiry settles at a later session's start; its outcome's exit fills on the expiry day, so an outcomes file
    is never judged by its fills' dates."""
    settled = replace(outcome_record(), exit=replace(outcome_record().exit,
                                                     filled_at=b.SLOT_AT - timedelta(days=3)))  # fmt: skip
    assert adoptable(encode_slot_file((settled,)), b.SESSION, SLOT, RecordKind.OUTCOMES, ALL) == (settled,)


def test_another_session_s_records_under_this_key_stop_by_name(tmp_path):
    cam, later = harness.build(tmp_path), b.SESSION + timedelta(days=1)
    put_on_drive(cam, RecordKind.DECISIONS, encode_slot_file(RECORDS), session=later)
    with pytest.raises(DashcamStuck, match="another session or slot"):
        cam.store.recover(later, SLOT, RecordKind.DECISIONS, ALL)
