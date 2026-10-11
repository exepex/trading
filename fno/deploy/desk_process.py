"""Starts, checks and stops the long-running desk process, the same way on every operating system."""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import psutil

DESK_ARGUMENTS = ["-m", "fno", "live", "run"]
PID_FILE_NAME = "desk.pid"
LOG_FILE_PATTERN = "live-desk-{day:%Y-%m-%d}.log"


class DeskProcess:
    def __init__(
        self,
        repo_root: Path,
        state_dir: Path,
        log_dir: Path,
        python: str = sys.executable,
        arguments: list[str] = DESK_ARGUMENTS,
    ):
        self.repo_root = repo_root
        self.arguments = arguments
        self.pid_file = state_dir / PID_FILE_NAME
        self.log_dir = log_dir
        self.python = python

    def running_pid(self) -> int | None:
        """The desk's process id, if it is alive and really is the desk."""
        try:
            pid = int(self.pid_file.read_text(encoding="utf-8").strip())
            process = psutil.Process(pid)
            return pid if process.is_running() and self.arguments[-1] in process.cmdline() else None
        except (FileNotFoundError, ValueError, psutil.Error):
            return None

    def start(self, now: datetime) -> int:
        """Start the desk in the background with output going to today's log file. Returns its process id."""
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.pid_file.parent.mkdir(parents=True, exist_ok=True)
        log = (self.log_dir / LOG_FILE_PATTERN.format(day=now)).open("a", encoding="utf-8")
        process = subprocess.Popen(
            [self.python, *self.arguments],
            cwd=self.repo_root,
            stdout=log,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            env={**os.environ, "PYTHONUTF8": "1"},
            **background_options(),
        )
        self.pid_file.write_text(str(process.pid), encoding="utf-8")
        return process.pid

    def ensure_running(self, now: datetime) -> str:
        pid = self.running_pid()
        if pid:
            return f"desk already running (pid {pid})"
        return f"desk started (pid {self.start(now)})"

    def stop(self) -> str:
        pid = self.running_pid()
        if not pid:
            return "desk is not running"
        process = psutil.Process(pid)
        process.terminate()
        try:
            process.wait(timeout=20)
        except psutil.TimeoutExpired:
            process.kill()
        self.pid_file.unlink(missing_ok=True)
        return f"desk stopped (pid {pid})"


def background_options() -> dict:
    """Detach from the scheduler's console so the desk keeps running after the job that started it ends."""
    if sys.platform == "win32":
        return {"creationflags": subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP}
    return {"start_new_session": True}
