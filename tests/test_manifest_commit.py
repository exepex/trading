"""Story A10 follow-up (judge 34 minor): manifest rows written at save time are committed and pushed after every
librarian run, a refusing hook is reported and never bypassed, and uncommitted rows are reported by data-coverage."""

import subprocess
from datetime import date

import pytest

from fno.cli import uncommitted_lines
from fno.storage.librarian_cli import run_librarian
from fno.storage.manifest_commit import COMMITTED, NOTHING, GitManifestRecorder
from fno.storage.manifest_folder import FingerprintingStore, ManifestFolder
from fno.storage.raw_source import ParticipantOiSource, RawSourceUnavailable
from fno.storage.raw_store import LocalFolderStore
from fno.storage.wiring import RAW_SOURCES

DAY = date(2026, 10, 9)


def git(folder, *args):
    return subprocess.run(["git", *args], cwd=folder, check=True, capture_output=True, text=True).stdout


@pytest.fixture
def repository(tmp_path):
    """A clone of a bare 'origin' on branch main, with one commit, and its manifest folder."""
    origin, clone = tmp_path / "origin.git", tmp_path / "clone"
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(origin))
    git(tmp_path, "clone", "-q", str(origin), str(clone))
    for key, value in (("user.name", "test"), ("user.email", "test@example.invalid"), ("core.hooksPath", "hooks")):
        git(clone, "config", key, value)
    (clone / "README.md").write_text("x\n")
    git(clone, "add", "README.md")
    git(clone, "commit", "-q", "-m", "start")
    git(clone, "push", "-q", "origin", "HEAD:main")
    return clone, origin, clone / "research" / "data" / "manifests"


def save_one_file(tmp_path, manifests_folder):
    store = FingerprintingStore(LocalFolderStore(tmp_path / "drive"), ManifestFolder(manifests_folder), RAW_SOURCES)
    store.put(ParticipantOiSource.path_for(DAY), b"oi")


def test_a_save_without_a_committed_row_is_reported_until_it_is_committed_and_pushed(tmp_path, repository):
    clone, origin, manifests = repository
    recorder = GitManifestRecorder(clone, manifests)
    save_one_file(tmp_path, manifests)
    assert recorder.pending() == ["research/data/manifests/participant-oi.csv"]
    assert uncommitted_lines(recorder) == [
        "NOT COMMITTED: research/data/manifests/participant-oi.csv (rows written at save time; commit and push it)"
    ]
    assert recorder.commit("test run") == COMMITTED.format(count=1)
    assert recorder.pending() == [] and uncommitted_lines(recorder) == []
    assert "fao_participant_oi_09102026.csv" in git(origin, "show", "main:research/data/manifests/participant-oi.csv")
    assert recorder.commit("test run") == NOTHING


def test_only_the_manifest_folder_is_committed(tmp_path, repository):
    clone, _, manifests = repository
    (clone / "other.txt").write_text("staged by someone else\n")
    git(clone, "add", "other.txt")
    save_one_file(tmp_path, manifests)
    GitManifestRecorder(clone, manifests).commit("test run")
    assert git(clone, "show", "--name-only", "--format=", "HEAD").split() == [
        "research/data/manifests/participant-oi.csv"
    ]
    assert "other.txt" in git(clone, "diff", "--cached", "--name-only")  # left staged, untouched


def test_a_refusing_hook_is_reported_and_never_bypassed(tmp_path, repository):
    clone, _, manifests = repository
    hook = clone / "hooks" / "pre-commit"
    hook.parent.mkdir()
    hook.write_text("#!/bin/sh\necho 'record scan: refused (test)' >&2\nexit 1\n")
    hook.chmod(0o755)
    save_one_file(tmp_path, manifests)
    recorder = GitManifestRecorder(clone, manifests)
    outcome = recorder.commit("test run")
    assert outcome.startswith("manifest rows NOT committed: commit failed: record scan: refused (test)")
    assert recorder.pending() == ["research/data/manifests/participant-oi.csv"]  # still reported, not lost


class Stops:
    def fill(self, start, end):
        raise RawSourceUnavailable("NSE archive: connection refused")


def test_the_librarian_commits_its_rows_even_when_the_run_stops(tmp_path, repository):
    clone, _, manifests = repository
    save_one_file(tmp_path, manifests)  # a row the stopped run had already written
    out = []
    recorder = GitManifestRecorder(clone, manifests)
    assert run_librarian(Stops, None, recorder, "test run", None, DAY, out=out.append) == 1
    assert out[-1] == COMMITTED.format(count=1) and recorder.pending() == []


def test_a_push_beaten_by_another_session_is_pulled_and_pushed_again(tmp_path, repository):
    clone, origin, manifests = repository
    other = tmp_path / "other"
    git(tmp_path, "clone", "-q", str(origin), str(other))
    for key, value in (("user.name", "other"), ("user.email", "other@example.invalid")):
        git(other, "config", key, value)
    save_one_file(tmp_path, manifests)

    class Racing(GitManifestRecorder):
        raced = False

        def _git(self, *args):
            if args[0] == "push" and not self.raced:  # another session pushes just before our first push
                self.raced = True
                (other / "theirs.txt").write_text("x\n")
                git(other, "add", "theirs.txt")
                git(other, "commit", "-q", "-m", "theirs")
                git(other, "push", "-q", "origin", "HEAD:main")
            return super()._git(*args)

    assert Racing(clone, manifests).commit("test run") == COMMITTED.format(count=1)
    assert "theirs.txt" in git(origin, "ls-tree", "--name-only", "main")


def test_a_committer_given_its_own_message_uses_it_and_the_default_is_unchanged(tmp_path, repository):
    """Story A16 reuses the committer for its intraday folder with its own message."""
    clone, origin, _ = repository
    folder = clone / "research" / "data" / "intraday"
    folder.mkdir(parents=True)
    (folder / "heartbeat.json").write_text("{}\n")
    recorder = GitManifestRecorder(clone, folder, message="Data: intraday slots ({what})")
    assert recorder.commit("2026-10-15 09:15") == COMMITTED.format(count=1)
    assert git(origin, "log", "-1", "--format=%s", "main").strip() == "Data: intraday slots (2026-10-15 09:15)"
    assert GitManifestRecorder(clone, folder).message.startswith("Manifests: SHA-256 rows")
