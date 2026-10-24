"""Story MS-P1j's daily step in a rehearsal (REH1): once `school.enabled` is on, a rehearsal runs `school run` as on
the day, so every Drive write of the school (the dashcam's sealed files, the paper accounts) must go to the
rehearsal's `dryrun/<run_id>/` folder, never the real record."""

import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest

from fno.constants import ENV_FNO_REHEARSAL
from fno.rehearsal.drive import DryrunDrive, RehearsalWriteRefused
from fno.rehearsal.mode import Rehearsal
from fno.school.accounts.wiring import build_account_sync
from fno.school.dashcam.wiring import build_dashcam
from fno.storage.wiring import OWNER_UPLOAD_SETTINGS
from tests.rehearsal.fakes import RecordingDrive

PACKAGE = Path(__file__).resolve().parents[2] / "fno"


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


def test_a_school_child_in_the_rehearsal_s_clone_commits_and_pushes_only_to_that_clone_s_origin(tmp_path):
    """REH1 starts each step's child as `python -m fno` in its clone, whose `origin` is a local bare repository. The
    school's three git writers (the dashcam's receipts, the session counts, the paper accounts' checkout) take their
    checkout from the package's own folder, so in the clone they are the clone's and push there, never to GitHub."""
    clone, origin = tmp_path / "clone", tmp_path / "origin.git"
    subprocess.run(["git", "init", "-q", "--bare", str(origin)], check=True)
    subprocess.run(["git", "init", "-q", str(clone)], check=True)
    subprocess.run(["git", "-C", str(clone), "remote", "add", "origin", str(origin)], check=True)
    shutil.copytree(PACKAGE, clone / "fno", ignore=shutil.ignore_patterns("__pycache__"))
    probe = (
        "import fno.config, fno.storage.wiring, fno.school.dashcam.wiring as d; "
        "print(fno.config.ROOT); print(fno.storage.wiring.REPOSITORY); print(d.build_receipt_publisher().repository)"
    )
    found = subprocess.run([sys.executable, "-c", probe], cwd=clone, capture_output=True, text=True, check=True)
    assert found.stdout.splitlines() == [str(clone)] * 3
    remote = subprocess.run(["git", "-C", str(clone), "remote", "get-url", "origin"], capture_output=True, text=True)
    assert remote.stdout.strip() == str(origin)
