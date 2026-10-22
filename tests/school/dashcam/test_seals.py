"""Criterion 2 (story MS-P1c): a seal not pushed, pushed after the fill time, or naming another file is refused."""

from dataclasses import replace
from datetime import timedelta

import pytest

from fno.school.constants import RecordKind
from fno.school.contracts.seal import StaleSeal
from fno.school.dashcam.seals import SealChecker
from tests.school.contracts import builders as b
from tests.school.contracts.test_records import trade_record
from tests.school.dashcam import harness


@pytest.fixture
def sealed(tmp_path):
    cam = harness.build(tmp_path)
    seal = cam.store.seal(b.SESSION, "15:00", RecordKind.DECISIONS, (trade_record(),))
    return SealChecker(cam.publisher, harness.AREA), seal


def test_a_pushed_seal_before_the_fill_is_accepted(sealed):
    checker, seal = sealed
    checker.check(seal, seal.sha256, seal.pushed_at + timedelta(seconds=1))
    checker.check(seal, seal.sha256, seal.pushed_at)  # boundary: pushed at the fill time itself


def test_a_seal_pushed_after_the_fill_time_is_refused(sealed):
    checker, seal = sealed
    with pytest.raises(StaleSeal, match="after the fill time"):
        checker.check(seal, seal.sha256, seal.pushed_at - timedelta(seconds=1))


def test_a_seal_naming_another_files_sha256_is_refused(sealed):
    checker, seal = sealed
    with pytest.raises(StaleSeal, match="another file"):
        checker.check(seal, "00" * 32, seal.pushed_at + timedelta(hours=1))


def test_a_seal_whose_commit_is_not_on_the_remote_is_refused(sealed):
    checker, seal = sealed
    unpushed = replace(seal, commit="1" * 40)
    with pytest.raises(StaleSeal, match="not on the remote"):
        checker.check(unpushed, seal.sha256, seal.pushed_at + timedelta(hours=1))


def test_a_commit_made_locally_but_not_pushed_is_refused(tmp_path):
    cam = harness.build(tmp_path)
    (cam.repository / "local.txt").write_text("x")
    harness.git(cam.repository, "add", "local.txt")
    harness.git(cam.repository, "commit", "-q", "-m", "local only")
    local = harness.git(cam.repository, "rev-parse", "HEAD").strip()
    seal = replace(b.seal(), commit=local)
    with pytest.raises(StaleSeal, match="not on the remote"):
        SealChecker(cam.publisher, harness.AREA).check(seal, seal.sha256, seal.pushed_at + timedelta(hours=1))


def test_a_forged_seal_naming_an_old_commit_or_an_earlier_time_is_refused(sealed):
    checker, seal = sealed
    late = seal.pushed_at + timedelta(hours=1)
    old_commit = harness.git(checker.publisher.repository, "rev-list", "--max-parents=0", "HEAD").strip()
    with pytest.raises(StaleSeal, match="does not hold"):
        checker.check(replace(seal, commit=old_commit), seal.sha256, late)
    with pytest.raises(StaleSeal, match="does not hold"):
        checker.check(replace(seal, pushed_at=seal.pushed_at - timedelta(days=1)), seal.sha256, late)
