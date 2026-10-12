"""End-of-day save of the desk's records to GitHub (uses the machine's normal git sign-in)."""

from __future__ import annotations

import subprocess
from datetime import date
from pathlib import Path

SYNCED_PATHS = ("journal", "reports", "conversations", "data/live/events", "data/live/news")
COMMIT_MESSAGE = "Live desk: end-of-day paper trades {day}"


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo), *args], check=check, capture_output=True, text=True)


def end_of_day_sync(repo: Path, day: date) -> str:
    branch = git(repo, "branch", "--show-current").stdout.strip()
    git(repo, "pull", "--quiet", "--rebase", "--autostash", "origin", branch)
    existing = [p for p in SYNCED_PATHS if (repo / p).exists()]
    if existing:
        git(repo, "add", *existing)
    if git(repo, "diff", "--cached", "--quiet", check=False).returncode == 0:
        return "nothing new to save"
    git(repo, "commit", "--quiet", "-m", COMMIT_MESSAGE.format(day=day.isoformat()))
    git(repo, "push", "--quiet", "origin", branch)
    return f"saved and pushed to {branch}"
