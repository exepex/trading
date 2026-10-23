"""The receipt publisher on real git (story MS-P1c, Judge J's findings): a shallow clone, a stale clone, a receipt
touched again, and a push that failed before a rerun with other records."""

import pytest

from fno.school.constants import RecordKind
from fno.school.contracts.dashcam import ReplayConflict
from fno.school.contracts.seal import StaleSeal
from fno.school.dashcam.names import slot_file_path
from fno.school.dashcam.seals import SealChecker
from fno.storage.receipt_publisher import SealNotPushed, ShallowClone
from tests.school.contracts import builders as b
from tests.school.contracts.test_records import closed_record, outcome_record, trade_record
from tests.school.dashcam import harness

SLOT = "15:00"
RECORDS = (trade_record(), closed_record())
OTHER = (outcome_record(),)


def drive_path(kind=RecordKind.DECISIONS) -> str:
    return f"{harness.AREA}/{slot_file_path(b.SESSION, SLOT, kind)}"


def push_unrelated_commits(cam, count: int) -> None:
    for number in range(count):
        (cam.repository / f"other{number}.txt").write_text(str(number))
        harness.git(cam.repository, "add", ".")
        harness.git(cam.repository, "commit", "-q", "-m", f"other {number}")
    harness.git(cam.repository, "push", "-q", "origin", "HEAD:main")


def test_a_shallow_clone_names_the_real_add_commit_not_its_boundary_commit(tmp_path):
    cam = harness.build(tmp_path)
    seal = cam.store.seal(b.SESSION, SLOT, RecordKind.DECISIONS, RECORDS)
    push_unrelated_commits(cam, 5)  # the receipt's commit is now older than a depth-1 clone reaches
    shallow = harness.another_checkout(cam, tmp_path, "shallow", depth=1)
    assert harness.git(shallow.repository, "rev-parse", "--is-shallow-repository").strip() == "true"
    assert shallow.publisher.published(drive_path()).commit == seal.commit
    assert harness.git(shallow.repository, "rev-parse", "--is-shallow-repository").strip() == "false", "deepened once"
    assert shallow.store.seal(b.SESSION, SLOT, RecordKind.DECISIONS, RECORDS) == seal, "a rerun names the same seal"
    SealChecker(shallow.publisher, harness.AREA).check(seal, seal.sha256, seal.pushed_at)


def test_a_shallow_clone_that_cannot_be_deepened_is_refused_by_name(tmp_path):
    cam = harness.build(tmp_path)
    seal = cam.store.seal(b.SESSION, SLOT, RecordKind.DECISIONS, RECORDS)
    push_unrelated_commits(cam, 3)
    shallow = harness.another_checkout(cam, tmp_path, "shallow", depth=1)
    harness.git(shallow.repository, "remote", "set-url", "origin", str(tmp_path / "gone.git"))
    with pytest.raises(ShallowClone, match="git fetch --unshallow"):
        shallow.publisher.published(drive_path())
    with pytest.raises(StaleSeal, match="shallow clone"):
        SealChecker(shallow.publisher, harness.AREA).check(seal, seal.sha256, seal.pushed_at)
    with pytest.raises(SealNotPushed):
        shallow.store.seal(b.SESSION, SLOT, RecordKind.DECISIONS, RECORDS)


def test_published_fetches_a_receipt_another_checkout_pushed_after_this_one_cloned(tmp_path):
    cam = harness.build(tmp_path)
    stale = harness.another_checkout(cam, tmp_path, "stale")  # cloned before the seal exists
    seal = cam.store.seal(b.SESSION, SLOT, RecordKind.DECISIONS, RECORDS)
    found = stale.publisher.published(drive_path())
    assert found is not None and found.commit == seal.commit


def test_a_receipt_file_touched_again_still_names_the_commit_that_added_it(tmp_path):
    cam = harness.build(tmp_path)
    seal = cam.store.seal(b.SESSION, SLOT, RecordKind.DECISIONS, RECORDS)
    receipt = cam.store.data.receipts.file_for(drive_path())
    receipt.write_text(receipt.read_text())  # same bytes: no change; then a real touch below
    receipt.write_text(receipt.read_text() + "\n")
    harness.git(cam.repository, "commit", "-q", "-am", "touch the receipt")
    harness.git(cam.repository, "push", "-q", "origin", "HEAD:main")
    assert cam.publisher.published(drive_path()).commit == seal.commit


def test_a_rerun_with_other_records_after_a_failed_push_is_a_replay_conflict(tmp_path):
    cam = harness.build(tmp_path, push_to_remote=False)
    with pytest.raises(SealNotPushed):
        cam.store.seal(b.SESSION, SLOT, RecordKind.DECISIONS, RECORDS)  # on Drive, receipt committed, push failed
    with pytest.raises(ReplayConflict, match="rule broken"):
        cam.store.seal(b.SESSION, SLOT, RecordKind.DECISIONS, OTHER)


def test_a_checkout_carrying_other_unpushed_commits_is_refused_by_name_and_never_pushed_to_main(tmp_path):
    cam = harness.build(tmp_path, push_to_remote=False)
    with pytest.raises(SealNotPushed):
        cam.store.seal(b.SESSION, SLOT, RecordKind.DECISIONS, RECORDS)  # receipt committed here, push failed
    (cam.repository / "unjudged.txt").write_text("work on a story branch")
    harness.git(cam.repository, "add", "unjudged.txt")
    harness.git(cam.repository, "commit", "-q", "-m", "unjudged work")
    foreign = harness.git(cam.repository, "rev-parse", "HEAD").strip()
    harness.git(cam.repository, "remote", "set-url", "origin", str(cam.remote))
    main_before = harness.git(cam.remote, "rev-parse", "main").strip()
    with pytest.raises(SealNotPushed, match="unjudged.txt"):
        cam.store.seal(b.SESSION, SLOT, RecordKind.DECISIONS, RECORDS)
    assert harness.git(cam.remote, "rev-parse", "main").strip() == main_before, "nothing was pushed to main"
    assert foreign not in harness.git(cam.remote, "rev-list", "main")


def test_the_move_to_storage_changed_no_byte_of_the_seal_or_its_receipt(tmp_path):
    """Golden values taken before the publisher moved out of the dashcam package (story MS-SIM, SIM-e)."""
    cam = harness.build(tmp_path)
    seal = cam.store.seal(b.SESSION, SLOT, RecordKind.DECISIONS, RECORDS)
    assert seal.sha256 == "5a6b1a8564a6a0c1f3902e3428a65251bba6130ecd4a531c503b218234acd77d"
    receipts = list((cam.repository / "receipts").rglob("*.sha256"))
    assert len(receipts) == 1
    assert receipts[0].read_text().endswith("\t532\t2026-11-02T09:40:00+00:00\ttest\trun1\n")
    assert seal.pushed_at == cam.publisher.published(drive_path()).pushed_at
