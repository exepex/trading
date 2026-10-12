"""Registers the desk's jobs with the operating system's own scheduler: Task Scheduler on Windows, cron elsewhere."""

from __future__ import annotations

import platform
import shlex
import subprocess
from abc import ABC, abstractmethod

from .jobs import WEEKDAYS, ScheduledJob

CRON_MARKER = "# fno-desk"
WINDOWS = "Windows"


class Scheduler(ABC):
    name = "scheduler"

    @abstractmethod
    def install(self, jobs: list[ScheduledJob]) -> None: ...

    @abstractmethod
    def uninstall(self, jobs: list[ScheduledJob]) -> None: ...


class WindowsTaskScheduler(Scheduler):
    """schtasks.exe: tasks run while the user is logged on (a locked screen is fine)."""

    name = "Windows Task Scheduler"

    def create_command(self, job: ScheduledJob) -> list[str]:
        action = subprocess.list2cmdline(job.command)
        base = ["schtasks", "/Create", "/F", "/TN", job.name, "/TR", action]
        if job.every_minutes:
            return [*base, "/SC", "MINUTE", "/MO", str(job.every_minutes)]
        return [*base, "/SC", "WEEKLY", "/D", ",".join(WEEKDAYS), "/ST", job.weekdays_at]

    def install(self, jobs: list[ScheduledJob]) -> None:
        for job in jobs:
            subprocess.run(self.create_command(job), check=True, capture_output=True)

    def uninstall(self, jobs: list[ScheduledJob]) -> None:
        for job in jobs:
            subprocess.run(["schtasks", "/Delete", "/F", "/TN", job.name], capture_output=True)


class CronScheduler(Scheduler):
    """The user's crontab on Linux and macOS. Only lines marked '# fno-desk' are ever touched."""

    name = "cron"

    def line_for(self, job: ScheduledJob) -> str:
        command = " ".join(shlex.quote(part) for part in job.command)
        if job.every_minutes:
            timing = f"*/{job.every_minutes} * * * *"
        else:
            hour, minute = job.weekdays_at.split(":")
            timing = f"{int(minute)} {int(hour)} * * 1-5"
        return f"{timing} {command} {CRON_MARKER} {job.name}"

    def merged_crontab(self, current: str, jobs: list[ScheduledJob]) -> str:
        kept = [line for line in current.splitlines() if CRON_MARKER not in line]
        return "\n".join([*kept, *(self.line_for(job) for job in jobs)]) + "\n"

    def _current(self) -> str:
        result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        return result.stdout if result.returncode == 0 else ""

    def _write(self, content: str) -> None:
        subprocess.run(["crontab", "-"], input=content, text=True, check=True)

    def install(self, jobs: list[ScheduledJob]) -> None:
        self._write(self.merged_crontab(self._current(), jobs))

    def uninstall(self, jobs: list[ScheduledJob]) -> None:
        self._write(self.merged_crontab(self._current(), []))


def scheduler_for_this_machine() -> Scheduler:
    return WindowsTaskScheduler() if platform.system() == WINDOWS else CronScheduler()
