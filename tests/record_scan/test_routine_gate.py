"""Story O5, criteria 2 and 3: a routine's commit is refused when a staged record holds a planted value (the report
names the file, never the value), clean records commit, and the current repository's records pass the scan."""

import gzip
import io
import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from fno.constants import ENV_FNO_SLACK_BOT_TOKEN
from fno.record_scan.record_files import NamedFiles, StagedRecords, TrackedRecords

ROOT = Path(__file__).resolve().parent.parent.parent
TOOL = ROOT / "tools" / "check_records.py"
sys.path.insert(0, str(TOOL.parent))
HOOKS = ROOT / ".githooks"
FAKE_TOKEN = "xox" + "b-1234567890-plantedvalue"
# Tests never post to Slack: the hook's alert sees no token
NO_SLACK = {k: v for k, v in os.environ.items() if k != ENV_FNO_SLACK_BOT_TOKEN}


def git(repo: Path, *args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, env=env or NO_SLACK)


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
    return subprocess.run([sys.executable, str(TOOL), *args], capture_output=True, text=True, env=NO_SLACK)


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


def test_code_folders_are_scanned_for_credentials_only(repo):
    stage(repo, "tests/test_x.py", "EXAMPLE_EMAIL = 'someone@example.com'\n")
    assert git(repo, "commit", "-q", "-m", "code with an example e-mail").returncode == 0
    stage(repo, "tools/x/notes.md", f"token {FAKE_TOKEN}\n")
    commit = git(repo, "commit", "-q", "-m", "code with a token")
    assert commit.returncode != 0 and "tools/x/notes.md:1: Slack token" in commit.stderr


def test_zip_members_are_scanned(repo):
    packed = io.BytesIO()
    with zipfile.ZipFile(packed, "w") as archive:
        archive.writestr("inner.csv", f"a\n{FAKE_TOKEN}\n")
    (repo / "research").mkdir()
    (repo / "research/data.zip").write_bytes(packed.getvalue())
    git(repo, "add", ".")
    assert scan("--staged", "--root", str(repo)).stdout.startswith("research/data.zip/inner.csv:2: Slack token")


@pytest.mark.parametrize("name", ["research/broken.csv.gz", "tests/fixtures/broken.zip"])
def test_damaged_archive_is_refused_with_an_alert(repo, name):
    """Judge 4, finding (a): a corrupt .gz or .zip is a finding with an alert, not a crash."""
    import check_records

    (repo / name).parent.mkdir(parents=True)
    (repo / name).write_bytes(b"not an archive")
    git(repo, "add", ".")
    alerts = FakeAlerts()
    assert check_records.main(["--staged", "--alert", "--root", str(repo)], alerts=alerts) == 1
    assert f"{name}:0: unreadable archive" in alerts.sent[0]


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


class FakeAlerts:
    def __init__(self):
        self.sent = []

    def send(self, text):
        self.sent.append(text)
        return "alert sent to #fno-desk"


def test_refusal_alert_names_file_line_and_kind_never_the_value(repo, capsys):
    """Judge 2, finding 1: the refusal is posted (file, line, kind) through the alert sender."""
    import check_records

    stage(repo, "journal/2026-10-13.md", f"note\nslack {FAKE_TOKEN}\n")
    alerts = FakeAlerts()
    assert check_records.main(["--staged", "--alert", "--root", str(repo)], alerts=alerts) == 1
    assert len(alerts.sent) == 1 and "journal/2026-10-13.md:2: Slack token" in alerts.sent[0]
    assert "plantedvalue" not in alerts.sent[0] and "alert sent to #fno-desk" in capsys.readouterr().out


def test_hook_without_slack_token_still_refuses_and_says_the_alert_was_not_sent(repo):
    stage(repo, "journal/x.md", f"{FAKE_TOKEN}\n")
    commit = git(repo, "commit", "-q", "-m", "x")
    assert commit.returncode != 0 and "alert NOT sent: FNO_SLACK_BOT_TOKEN is not set" in commit.stderr


def test_fresh_checkout_is_gated_by_the_session_start_hook(tmp_path):
    """Judge 2, finding 2: a fresh checkout whose session runs .claude/settings.json's SessionStart command refuses a
    planted token (before that command runs, the same commit goes through)."""
    for part in (".claude", ".githooks", "fno", "tools"):
        shutil.copytree(ROOT / part, tmp_path / part, ignore=shutil.ignore_patterns("__pycache__"))
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.name", "session")
    git(tmp_path, "config", "user.email", "session@example.invalid")
    settings = json.loads((tmp_path / ".claude/settings.json").read_text())
    for command in [h["command"] for entry in settings["hooks"]["SessionStart"] for h in entry["hooks"]]:
        subprocess.run(command, shell=True, check=True, env={**NO_SLACK, "CLAUDE_PROJECT_DIR": str(tmp_path)})
    assert git(tmp_path, "config", "--get", "core.hooksPath").stdout.strip() == ".githooks"
    git(tmp_path, "add", ".")
    assert git(tmp_path, "commit", "-q", "-m", "fresh checkout").returncode == 0  # the scan passes its own code
    stage(tmp_path, "conversations/2026-10-13.md", f"owner pasted {FAKE_TOKEN}\n")
    commit = git(tmp_path, "commit", "-q", "-m", "log")
    assert commit.returncode != 0 and "conversations/2026-10-13.md:1: Slack token" in commit.stderr


def test_current_repository_records_pass_the_scan():
    result = scan()
    assert result.returncode == 0, result.stdout
