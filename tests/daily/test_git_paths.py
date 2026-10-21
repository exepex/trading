"""Story O1, criteria 4 and 4a with real git (judge 169 addendum 1, note 2): each quote part's commit holds exactly its
own files (A4c's paths), never a Groww raw quote file, and never a file another writer staged; and a real child
command's exit code and lines."""

import os
import shutil
import subprocess
import sys
import time

from fno.config import ROOT
from fno.daily.processes import ChildProcesses
from fno.daily.quote_parts import QUOTE_PARTS
from fno.daily.steps import wait
from fno.desk.git_sync import Git

GROWW = "research/data/quotes/groww/derivatives/quote-snapshots/2026/10"
NSE = "research/data/quotes/nse/derivatives/quote-snapshots/2026/10"
OWN = {
    "nifty": [f"{GROWW}/nifty_20261016.canonical", f"{GROWW}/nifty_20261016_145500.meta.json"],
    "nse": [f"{NSE}/nifty_20261016{suffix}" for suffix in (".canonical", "_145501.csv", "_145501.meta.json")],
    "indices": [f"{GROWW}/{name}_20261016{suffix}" for name in ("banknifty", "finnifty", "midcpnifty")
                for suffix in (".canonical", "_150100.meta.json")],
}  # fmt: skip
RAW = [f"{GROWW}/{name}_20261016_145500.csv" for name in ("nifty", "banknifty")]
OTHER = "research/notes/another_writer.md"  # a tracked file another writer staged


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True).stdout


def test_each_part_commits_only_its_own_files_with_another_file_staged(tmp_path):
    git(tmp_path, "init", "-q")
    for key, value in (("user.email", "t@example.org"), ("user.name", "t"), ("core.hooksPath", "/dev/null")):
        git(tmp_path, "config", key, value)
    shutil.copy(ROOT / ".gitignore", tmp_path / ".gitignore")
    for path in [*sum(OWN.values(), []), *RAW, OTHER]:
        (tmp_path / path).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / path).write_text("x")
    git(tmp_path, "add", ".gitignore", OTHER)  # another writer's staged file
    repo = Git(tmp_path)
    for part in QUOTE_PARTS:
        files = repo.changed(part.pathspecs)
        assert sorted(repo.relative(f) for f in files) == sorted(OWN[part.name])  # no raw file, no other part's
        assert repo.commit_paths(files, f"3 pm quotes {part.name}")
        assert sorted(git(tmp_path, "show", "--name-only", "--format=", "HEAD").split()) == sorted(OWN[part.name])
    assert git(tmp_path, "diff", "--cached", "--name-only").split() == [".gitignore", OTHER]  # still staged, untouched
    assert repo.changed(QUOTE_PARTS[0].pathspecs) == []  # committed: nothing left for NIFTY


def test_a_real_child_command_gives_its_exit_code_and_last_lines():
    process = ChildProcesses(ROOT).start(["daily", "--help"])
    assert wait(process, sleep=lambda seconds: time.sleep(0.05)) == 0
    assert any("daily" in line for line in process.lines())


GRANDCHILD = (
    "import subprocess, sys, time\n"
    "p = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])\n"
    "open(sys.argv[1], 'w').write(str(p.pid))\n"
    "time.sleep(60)\n"
)


def test_stopping_a_command_kills_what_it_started_too(tmp_path, monkeypatch):
    """Judge 178 addendum 3, note 8: a grandchild (a git or Groww call) dies with the command it ran under."""
    marker = tmp_path / "grandchild.pid"
    real_popen = subprocess.Popen

    def popen(command, **options):  # the same options ChildProcesses gives, on a script that starts a grandchild
        return real_popen([sys.executable, "-c", GRANDCHILD, str(marker)], **options)

    monkeypatch.setattr(subprocess, "Popen", popen)
    process = ChildProcesses(tmp_path).start(["anything"])
    while not marker.exists() or not marker.read_text():
        time.sleep(0.05)
    grandchild = int(marker.read_text())
    assert os.getpgid(process.popen.pid) == process.popen.pid  # it leads its own group, so the group kill reaches all
    process.stop()
    time.sleep(0.2)
    assert process.poll() is not None and not _alive(grandchild)


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    with open(f"/proc/{pid}/stat") as stat:  # killed but not yet reaped by init: a zombie is not alive
        return stat.read().split()[2] != "Z"


CHATTY = (
    "import sys, time\n"
    "print('recording 1')\n"
    "print('alert NOT sent: FNO_SLACK_BOT_TOKEN is not set')\n"
    "for i in range(12):\n"
    "    print(f'line {i}')\n"
    "sys.stdout.flush()\n"
    "time.sleep(float(sys.argv[1]))\n"
)


def _chatty(monkeypatch, seconds: str):
    real_popen = subprocess.Popen
    monkeypatch.setattr(
        subprocess, "Popen", lambda command, **o: real_popen([sys.executable, "-c", CHATTY, seconds], **o)
    )


def test_a_child_s_own_unsent_alert_reaches_the_run_s_output_beyond_the_kept_lines(tmp_path, monkeypatch):
    """Judge 178 addendum 6, should-fix 9: the line is printed as written, though the run log keeps only 10 lines."""
    _chatty(monkeypatch, "0")
    reported = []
    process = ChildProcesses(tmp_path, reported.append).start(["quotes", "record"])
    assert wait(process, sleep=lambda seconds: time.sleep(0.05)) == 0
    kept = process.lines()
    assert reported == ["alert NOT sent: FNO_SLACK_BOT_TOKEN is not set"] and len(kept) == 10
    assert "alert NOT sent: FNO_SLACK_BOT_TOKEN is not set" not in kept  # only the report carries it
    process.lines()
    assert len(reported) == 1  # read once, reported once


def test_a_stopped_child_s_unsent_alert_is_reported_too(tmp_path, monkeypatch):
    _chatty(monkeypatch, "60")
    reported = []
    process = ChildProcesses(tmp_path, reported.append).start(["margins", "stress-broker-check"])
    time.sleep(1.0)  # it has printed and is sleeping
    process.stop()
    assert reported == ["alert NOT sent: FNO_SLACK_BOT_TOKEN is not set"]


LAST_UNSENT = (
    "print('recorded: nifty_20261019_145500 (0 contracts, complete=False)')\n"
    "print('alert NOT sent: Slack answered HTTP 503 | 3 pm quote recorder: raw quote file NOT saved to Drive "
    "(DriveDown: https://example.invalid/drive/v3/files?q=FAKEFOLDERID123)')\n"
)


def test_an_unsent_alert_printed_last_is_reported_but_never_kept_for_the_committed_run_record(tmp_path, monkeypatch):
    """A4/O2 (21 Oct): an unsent alert's text can hold what is meant for Slack alone (a Drive error's text with the
    private folder ID); the routine gets it, the run record (journal/runs, public) never does."""
    real_popen = subprocess.Popen
    monkeypatch.setattr(subprocess, "Popen", lambda command, **o: real_popen([sys.executable, "-c", LAST_UNSENT], **o))
    reported = []
    process = ChildProcesses(tmp_path, reported.append).start(["quotes", "record"])
    assert wait(process, sleep=lambda seconds: time.sleep(0.05)) == 0
    kept = process.lines()
    assert len(reported) == 1 and "FAKEFOLDERID123" in reported[0]
    assert kept == ["recorded: nifty_20261019_145500 (0 contracts, complete=False)"]


UNSENT_ONLY = (
    "import sys\n"
    "print('recorded: nifty_20261019_145500 (0 contracts, complete=False) - raw quote file not saved: DriveDown')\n"
    "print('alert NOT sent: Slack answered HTTP 503 | 3 pm quote recorder: raw quote file NOT saved to Drive')\n"
    "sys.exit(1)\n"
)


class SentAlerts:
    def __init__(self):
        self.sent = []

    def send(self, text):
        self.sent.append(text)
        return "alert NOT sent: Slack answered HTTP 503"


def test_a_part_whose_only_alert_went_unsent_is_not_alerted_twice_and_its_text_stays_out_of_the_record(
    tmp_path, monkeypatch
):
    """Judge 412 add. 1 and the O1/O2 owner (21 Oct): with the real ChildProcess, a failed part that printed its own
    unsent alert counts as alerted (no second PART_NOT_OK), the line reaches the routine once, never the run record."""
    from datetime import date, datetime

    from fno.daily.quote_parts import QuotePart, QuoteParts
    from fno.models import IST
    from tests.daily.fakes import RecordingCommitter

    real_popen = subprocess.Popen
    monkeypatch.setattr(subprocess, "Popen", lambda command, **o: real_popen([sys.executable, "-c", UNSENT_ONLY], **o))
    reported, alerts = [], SentAlerts()
    part = QuotePart("nifty", ("quotes", "record"), ("research/data/quotes/groww/",))
    clock = lambda: datetime(2026, 10, 19, 15, 0, tzinfo=IST)  # noqa: E731
    parts = QuoteParts(
        (part,), ChildProcesses(tmp_path, reported.append), RecordingCommitter(clock, []), lambda s: [], alerts, clock
    )
    parts.start(date(2026, 10, 19))
    wait(parts.running["nifty"], sleep=lambda seconds: time.sleep(0.05))
    parts.service()
    result = parts.results["nifty"]
    assert result["status"] == "failed" and alerts.sent == []  # its own alert counts: no PART_NOT_OK
    assert len(reported) == 1 and reported[0].startswith("alert NOT sent: Slack answered HTTP 503 | ")
    assert not any("alert NOT sent" in line for line in result["lines"])  # never in the committed run record
