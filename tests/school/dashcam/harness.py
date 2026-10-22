"""A real dashcam on a temporary Drive folder and a temporary git remote (story MS-P1c): the store, the receipts and
the pushes are the production classes; only the Drive is a local folder."""

import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from fno.school.dashcam.names import SCHOOL_AREA
from fno.school.dashcam.publisher import GitReceiptPublisher
from fno.school.dashcam.reader import VerifiedDriveReader
from fno.school.dashcam.store import DriveDashcamStore
from fno.storage.data_store import DataStore
from fno.storage.drive_cache import DriveCache
from fno.storage.manifest_commit import GitManifestRecorder
from fno.storage.raw_store import LocalFolderStore
from fno.storage.receipts import ReceiptFolder

AREA = "data"
NOW = datetime(2026, 11, 2, 9, 40, tzinfo=UTC)


def git(cwd: Path, *args: str) -> str:
    done = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)
    return done.stdout


@dataclass
class Dashcam:
    repository: Path
    remote: Path
    drive: LocalFolderStore
    store: DriveDashcamStore
    publisher: GitReceiptPublisher


def build(tmp_path: Path, push_to_remote: bool = True) -> Dashcam:
    remote, repository = tmp_path / "origin.git", tmp_path / "checkout"
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(remote))
    git(tmp_path, "clone", "-q", str(remote), str(repository))
    hooks = tmp_path / "no-hooks"
    hooks.mkdir()
    for setting in (("core.hooksPath", str(hooks)), ("user.name", "t"), ("user.email", "t@example.invalid")):
        git(repository, "config", *setting)
    git(repository, "checkout", "-q", "-b", "main")
    (repository / "README").write_text("x")
    git(repository, "add", "README")
    git(repository, "commit", "-q", "-m", "start")
    git(repository, "push", "-q", "origin", "HEAD:main")
    if not push_to_remote:
        git(repository, "remote", "set-url", "origin", str(tmp_path / "nowhere.git"))
    receipts = ReceiptFolder(repository / "receipts")
    drive = LocalFolderStore(tmp_path / "drive")
    data = DataStore(drive, AREA, receipts, "test", "run1", clock=lambda: NOW)
    recorder = GitManifestRecorder(repository, repository / "receipts" / AREA / SCHOOL_AREA)
    publisher = GitReceiptPublisher(recorder, receipts, repository)
    cache = DriveCache(drive, receipts, tmp_path / "cache")
    return Dashcam(repository, remote, drive, DriveDashcamStore(data, publisher, VerifiedDriveReader(cache, AREA)),
                   publisher)  # fmt: skip
