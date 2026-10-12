"""Story O5, criteria 2 and 3: a routine's commit is refused when a staged record holds a planted value (the report
names the file, never the value), clean records commit, and the current repository's records pass the scan."""

import gzip
import subprocess
import sys
from pathlib import Path

import pytest

from fno.record_scan.record_files import NamedFiles, StagedRecords, TrackedRecords

ROOT = Path(__file__).resolve().parent.parent.parent
TOOL = ROOT / "tools" / "check_records.py"
HOOKS = ROOT / ".githooks"
FAKE_TOKEN = "xox" + "b-1234567890-plantedvalue"


def git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True)


@pytest.fixture
def repo(tmp_path):
    """A routine's checkout: a git repository with the record-scan hook enabled, as CLAUDE.md's routine sets it up."""
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.name", "routine")
    git(tmp_path, "config", "user.email", "routine@example.invalid")
    git(tmp_path, "config", "core.hooksPath", str(HOOKS))
    return tmp_path


def stage(repo: Path, path: str, text: str) -> None:
    (repo / path).parent.mkdir(parents=True, exist_ok=True)
    (repo / path).write_text(text)
    git(repo, "add", path)


def scan(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(TOOL), *args], capture_output=True, text=True)


def test_routine_commit_with_a_planted_token_is_refused_and_names_only_the_file(repo):
    stage(repo, "research/data/quotes/2026/10/13/attempt.csv", "snapshot_id,bid\n1,112.5\n")
    stage(repo, "journal/2026-10-13.md", f"note\nslack {FAKE_TOKEN}\n")
    commit = git(repo, "commit", "-q", "-m", "routine records")
    output = commit.stdout + commit.stderr  # git shows a hook's output on stderr
    assert commit.returncode != 0
    assert "journal/2026-10-13.md:2: Slack token" in output
    assert "REFUSED" in output and "plantedvalue" not in output
    assert git(repo, "rev-parse", "HEAD").returncode != 0  # nothing was committed


def test_routine_commit_of_clean_records_goes_through(repo):
    stage(repo, "research/data/quotes/2026/10/13/attempt.csv", "snapshot_id,bid\n1,112.5\n")
    assert git(repo, "commit", "-q", "-m", "routine records").returncode == 0


def test_staged_scan_reads_the_staged_bytes_not_the_working_tree(repo):
    stage(repo, "reports/r.md", f"{FAKE_TOKEN}\n")
    (repo / "reports/r.md").write_text("cleaned in the working tree but not re-staged\n")
    assert [r.path for r in StagedRecords(repo).records()] == ["reports/r.md"]
    assert scan("--staged", "--root", str(repo)).returncode == 1


def test_code_folders_are_not_records(repo):
    stage(repo, "tests/test_x.py", f"PLANTED = '{FAKE_TOKEN}'\n")
    assert list(StagedRecords(repo).records()) == []


def test_gzip_records_are_unpacked_and_scanned(repo):
    (repo / "research").mkdir()
    (repo / "research/data.csv.gz").write_bytes(gzip.compress(f"a,b\n1,{FAKE_TOKEN}\n".encode()))
    git(repo, "add", ".")
    assert [r.text.splitlines()[1] for r in TrackedRecords(repo).records()] == [f"1,{FAKE_TOKEN}"]


def test_named_files_scan_a_session_export_before_it_is_sent(tmp_path):
    export = tmp_path / "session-export"
    export.mkdir()
    (export / "transcript.md").write_text(f"token {FAKE_TOKEN}\n")
    assert len(list(NamedFiles([export]).records())) == 1
    result = scan(str(export))
    assert result.returncode == 1 and "transcript.md:1: Slack token" in result.stdout


def test_current_repository_records_pass_the_scan():
    result = scan()
    assert result.returncode == 0, result.stdout
