"""Story A8 on GitHub Actions: the participant-OI watch workflow's schedule and safety rules, and the union merge that
lets two jobs append to the same release log without a conflict."""

import re
import shutil
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "participant-oi-watch.yml"
LOG = "research/data/participant_oi/release_checks.csv"
IST_OFFSET = timedelta(hours=5, minutes=30)


def workflow() -> dict:
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


def run_times_ist() -> list[str]:
    """Every start time (HH:MM IST) the cron lines give in a day."""
    times = []
    for entry in workflow()[True]["schedule"]:  # YAML reads the key `on` as True
        minutes, hours, *rest = entry["cron"].split()
        assert rest == ["*", "*", "*"]
        first, last = (int(h) for h in hours.split("-"))
        for hour in range(first, last + 1):
            for minute in (int(m) for m in minutes.split(",")):
                times.append(f"{datetime(2026, 1, 1, hour, minute) + IST_OFFSET:%H:%M}")
    return sorted(times)


def test_runs_every_15_minutes_through_the_evening_with_a_last_run_from_23_15():
    times = run_times_ist()
    assert times[0] <= "17:00" and "23:15" <= times[-1] <= "23:30"
    gaps = {(datetime.strptime(b, "%H:%M") - datetime.strptime(a, "%H:%M")).seconds for a, b in zip(times, times[1:])}
    assert gaps == {15 * 60}


def test_one_check_per_run_one_writer_at_a_time_and_the_record_scan_kept():
    job, text = workflow()["jobs"]["check"], WORKFLOW.read_text(encoding="utf-8")
    assert workflow()["concurrency"] == {"group": "participant-oi-watch", "cancel-in-progress": False}
    assert "workflow_dispatch" in workflow()[True]
    assert "python -m fno participant-oi check-once" in text and "participant-oi watch" not in text
    assert "git pull --no-rebase" in text and "--no-verify" not in text and "core.hooksPath .githooks" in text
    assert re.findall(r"secrets\.(\w+)", text) == ["FNO_SLACK_BOT_TOKEN"]
    assert job["env"]["LOG"] == LOG and job["timeout-minutes"] <= 15


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True).stdout


def test_two_jobs_appending_to_the_log_merge_without_a_conflict(tmp_path):
    repo = tmp_path / "repo"
    (repo / LOG).parent.mkdir(parents=True)
    shutil.copy(ROOT / ".gitattributes", repo / ".gitattributes")
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.email", "test@example.invalid")
    git(repo, "config", "user.name", "test")
    header = "day,checked_at,outcome,sha256,last_modified\n"
    (repo / LOG).write_text(header + "2026-10-12,2026-10-12T17:37:00+05:30,absent,,\n")
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", "base")
    git(repo, "checkout", "-q", "-b", "routine")
    routine_row = "2026-10-12,2026-10-12T17:41:00+05:30,absent,,\n"
    (repo / LOG).write_text((repo / LOG).read_text() + routine_row)
    git(repo, "commit", "-q", "-am", "routine")
    git(repo, "checkout", "-q", "main")
    actions_row = "2026-10-12,2026-10-12T17:52:00+05:30,present,ab,\n"
    (repo / LOG).write_text((repo / LOG).read_text() + actions_row)
    git(repo, "commit", "-q", "-am", "actions")
    git(repo, "merge", "-q", "--no-edit", "routine")  # check=True: a conflict fails here
    lines = (repo / LOG).read_text().splitlines(keepends=True)
    assert lines[0] == header and lines.count(header) == 1
    assert routine_row in lines and actions_row in lines and len(lines) == 4
