"""Where an A21 capture's failure is recorded (story A21, both parts): one row in O10's committed capture-error log
per failure, with the job, the step and a one-line message built from names, never from a log."""

from __future__ import annotations

import os
from datetime import date
from typing import Protocol

from ..health.capture_errors import CaptureError, CaptureErrorLog
from .constants import JOB


class FailureLog(Protocol):
    def record(self, day: date, step: str, kind: str, message: str) -> None: ...

    def has(self, day: date, kind: str) -> bool: ...


def run_url(env=os.environ) -> str:
    """The Actions run that hit the failure, or empty outside Actions."""
    parts = (env.get("GITHUB_SERVER_URL"), env.get("GITHUB_REPOSITORY"), env.get("GITHUB_RUN_ID"))
    return f"{parts[0]}/{parts[1]}/actions/runs/{parts[2]}" if all(parts) else ""


class CaptureErrorFailures:
    def __init__(self, log: CaptureErrorLog, url: str, job: str = JOB):
        self.log, self.url, self.job = log, url, job

    def record(self, day: date, step: str, kind: str, message: str) -> None:
        self.log.append(CaptureError(day, self.job, step, kind, message, self.url))

    def has(self, day: date, kind: str) -> bool:
        """Already recorded today (a once-a-day failure is alerted once, whichever A16 fire sees it)."""
        return self.log.has(day, self.job, kind)
