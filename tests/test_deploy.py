import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

from fno.deploy.desk_process import DeskProcess
from fno.deploy.git_sync import end_of_day_sync
from fno.deploy.jobs import SYNC_JOB, WATCHDOG_JOB, desk_jobs
from fno.deploy.schedulers import CRON_MARKER, CronScheduler, WindowsTaskScheduler

JOBS = desk_jobs(Path("/home/me/trading/.venv/bin/python"), Path("/home/me/trading/deploy/desk.py"))


def test_cron_lines_replace_only_our_own():
    existing = "0 1 * * * backup.sh\n*/5 * * * * old desk # fno-desk FNO Desk Watchdog\n"
    merged = CronScheduler().merged_crontab(existing, JOBS)
    lines = merged.splitlines()
    assert lines[0] == "0 1 * * * backup.sh" and len(lines) == 3
    assert lines[1].startswith("*/5 * * * * /home/me/trading/.venv/bin/python /home/me/trading/deploy/desk.py deploy")
    assert lines[2].startswith("0 16 * * 1-5 ") and lines[2].endswith(f"{CRON_MARKER} {SYNC_JOB}")
    assert CronScheduler().merged_crontab(merged, []) == "0 1 * * * backup.sh\n"


def test_windows_task_commands():
    windows = WindowsTaskScheduler()
    watchdog = windows.create_command(JOBS[0])
    assert watchdog[:6] == ["schtasks", "/Create", "/F", "/TN", WATCHDOG_JOB, "/TR"]
    assert watchdog[-4:] == ["/SC", "MINUTE", "/MO", "5"]
    sync = windows.create_command(JOBS[1])
    assert sync[-6:] == ["/SC", "WEEKLY", "/D", "MON,TUE,WED,THU,FRI", "/ST", "16:00"]


def test_desk_process_start_check_stop(tmp_path):
    desk = DeskProcess(
        tmp_path,
        tmp_path / "state",
        tmp_path / "logs",
        sys.executable,
        ["-c", "import time; time.sleep(60)", "sleeper"],
    )
    assert desk.running_pid() is None
    first = desk.ensure_running(datetime(2026, 10, 12, 9, 0))
    assert first.startswith("desk started")
    assert desk.ensure_running(datetime(2026, 10, 12, 9, 5)).startswith("desk already running")
    assert desk.stop().startswith("desk stopped") and desk.running_pid() is None
    assert (tmp_path / "logs" / "live-desk-2026-10-12.log").exists()


def test_end_of_day_sync_commits_and_pushes(tmp_path):
    def git(*args, cwd):
        subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)

    remote, work = tmp_path / "remote.git", tmp_path / "work"
    git("init", "--bare", "-b", "main", str(remote), cwd=tmp_path)
    git("clone", str(remote), str(work), cwd=tmp_path)
    git("config", "user.email", "desk@example.com", cwd=work)
    git("config", "user.name", "desk", cwd=work)
    git("checkout", "-b", "main", cwd=work)
    (work / "README").write_text("x")
    git("add", "README", cwd=work)
    git("commit", "-m", "init", cwd=work)
    git("push", "-u", "origin", "main", cwd=work)
    assert end_of_day_sync(work, date(2026, 10, 12)) == "nothing new to save"
    (work / "journal").mkdir()
    (work / "journal" / "live_trades.json").write_text("[]")
    assert end_of_day_sync(work, date(2026, 10, 12)) == "saved and pushed to main"
