"""Story MS-P1j's daily step in a rehearsal (REH1): once `school.enabled` is on, a rehearsal runs `school run` as on
the day, so every Drive write of the school (the dashcam's sealed files, the paper accounts) must go to the
rehearsal's `dryrun/<run_id>/` folder, never the real record."""

from datetime import date

import pytest

from fno.constants import ENV_FNO_REHEARSAL
from fno.rehearsal.drive import DryrunDrive, RehearsalWriteRefused
from fno.rehearsal.mode import Rehearsal
from fno.school.accounts.wiring import build_account_sync
from fno.school.dashcam.wiring import build_dashcam
from fno.storage.wiring import OWNER_UPLOAD_SETTINGS
from tests.rehearsal.fakes import RecordingDrive


@pytest.fixture
def real_drive(monkeypatch):
    """The owner's Drive settings present (planted) and the real Drive store replaced by a recording one."""
    drive = RecordingDrive()
    for name in OWNER_UPLOAD_SETTINGS:
        monkeypatch.setenv(name, "planted")
    monkeypatch.setattr("fno.storage.wiring.GoogleDriveUploadStore", lambda *a, **k: drive)
    return drive


def rehearsing(monkeypatch, tmp_path) -> Rehearsal:
    mode = Rehearsal.new(date(2026, 10, 23), tmp_path, tmp_path)
    monkeypatch.setenv(ENV_FNO_REHEARSAL, mode.to_env())
    return mode


def school_drives():
    """The dashcam's store and the accounts' (built at their first pull or push, so opened here as that would)."""
    return build_dashcam().data.drive, build_account_sync()._store().drive


def test_in_a_rehearsal_the_dashcam_and_the_accounts_write_only_under_dryrun(monkeypatch, tmp_path, real_drive):
    mode = rehearsing(monkeypatch, tmp_path)
    for n, drive in enumerate(school_drives()):
        assert isinstance(drive, DryrunDrive) and drive.root == mode.drive_root
        drive.put(f"school/planted_{n}", b"x")
    assert set(real_drive.files) == {f"{mode.drive_root}/school/planted_{n}" for n in (0, 1)}


def test_a_rehearsal_s_school_write_to_the_real_root_is_refused_before_drive(monkeypatch, tmp_path, real_drive):
    rehearsing(monkeypatch, tmp_path)
    dashcam_drive, _ = school_drives()
    with pytest.raises(RehearsalWriteRefused):
        dashcam_drive.replace_contents("an-id-of-the-real-record", b"x")
    assert real_drive.files == {}


def test_outside_a_rehearsal_the_school_writes_the_real_drive(monkeypatch, real_drive):
    monkeypatch.delenv(ENV_FNO_REHEARSAL, raising=False)
    assert all(drive is real_drive for drive in school_drives())
