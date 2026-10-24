"""The composition root of the practice archive, built for real over a fake env, Drive, cache and git (MS-SIM-e2,
judge 531): the receipt commit takes only the run's own receipts folder, and the read-back is the verified Drive
reader over the data area."""

import subprocess
from pathlib import Path

from fno.school.dashcam.reader import VerifiedDriveReader
from fno.school.simulator.archive import names, wiring
from fno.school.simulator.archive.archive import PracticeArchive
from fno.storage.data_wiring import DATA_AREA
from tests.school.simulator.archive.test_archive import RUN

PENDING = f" M receipts/data/{names.PRACTICE_AREA}/{RUN}/median/2024/03/04/1500.decisions.jsonl.gz.sha256"


class RecordingGit:
    """Every git command the archive runs, answered as a checkout with one pending receipt would answer."""

    def __init__(self):
        self.calls: list[tuple[str, ...]] = []

    def __call__(self, args, cwd=None, **kwargs):
        self.calls.append(tuple(args[1:]))
        out = {("config", "core.hooksPath"): ".githooks\n", ("status",): PENDING + "\n"}
        stdout = next((text for key, text in out.items() if tuple(args[1 : 1 + len(key)]) == key), "")
        return subprocess.CompletedProcess(args, 0, stdout=stdout, stderr="")


def build(tmp_path, monkeypatch):
    seen = {}
    monkeypatch.setattr(wiring, "build_data_store", lambda writer, run, env: seen.update(env=env, run=run) or "store")
    monkeypatch.setattr(wiring, "build_drive_cache", lambda env: seen.update(cache_env=env) or "cache")
    git = RecordingGit()
    archive = wiring.build_practice_archive(RUN, {"FAKE": "env"}, repository=tmp_path, git=git)
    return archive, git, seen


def test_the_archive_is_built_over_the_given_env_with_the_run_as_the_writer_run(tmp_path, monkeypatch):
    archive, _, seen = build(tmp_path, monkeypatch)
    assert isinstance(archive, PracticeArchive) and archive.data == "store"
    assert seen == {"env": {"FAKE": "env"}, "run": RUN, "cache_env": {"FAKE": "env"}}


def test_the_recorder_commits_exactly_the_runs_receipts_folder(tmp_path, monkeypatch):
    archive, _, _ = build(tmp_path, monkeypatch)
    recorder = archive.publisher.recorder
    assert recorder.folder == f"receipts/data/{names.PRACTICE_AREA}/{RUN}" == names.receipts_folder(RUN)
    assert recorder.repository == Path(tmp_path)


def test_git_add_and_commit_get_only_that_pathspec(tmp_path, monkeypatch):
    archive, git, _ = build(tmp_path, monkeypatch)
    archive.publisher.recorder.commit("x")
    folder = names.receipts_folder(RUN)
    adds = [call for call in git.calls if call[0] == "add"]
    commits = [call for call in git.calls if call[0] == "commit"]
    assert adds == [("add", "--", folder)] and len(commits) == 1
    assert commits[0][-2:] == ("--", folder) and commits[0].count("--") == 1
    assert not any(call[:1] == ("add",) and "receipts" in call[-1].rstrip("/").split("/")[-1:] for call in git.calls)


def test_the_status_that_finds_the_pending_receipts_is_limited_to_that_folder_too(tmp_path, monkeypatch):
    archive, git, _ = build(tmp_path, monkeypatch)
    archive.publisher.recorder.commit("x")
    status = [call for call in git.calls if call[0] == "status"]
    assert status and all(call[-1] == names.receipts_folder(RUN) and call[-2] == "--" for call in status)


def test_the_read_back_is_the_verified_drive_reader_over_the_data_area_and_its_cache(tmp_path, monkeypatch):
    archive, _, _ = build(tmp_path, monkeypatch)
    assert type(archive.reader) is VerifiedDriveReader
    assert archive.reader.area == DATA_AREA == "data" and archive.reader.cache == "cache"
