"""A19's episodes written into O10's committed capture-error log (`research/ops/capture_errors.csv`), one format for
every capture job (orchestrator, 16 Oct). The log and its row class are passed in, so this adapter carries no
second copy of O10's format."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

from .episodes import EpisodeLog, LogRow
from .names import JOB


class CaptureEpisodeLog(EpisodeLog):
    def __init__(self, log, make_error: Callable, run_url: str):
        """`log`: O10's `CaptureErrorLog`; `make_error`: its `CaptureError`; `run_url`: this run's page."""
        self.log, self.make_error, self.run_url = log, make_error, run_url

    def rows(self) -> list[LogRow]:
        return [LogRow(row.day, row.job, row.step, row.kind) for row in self.log.rows()]

    def append(self, day: date, step: str, kind: str, message: str) -> None:
        self.log.append(self.make_error(day, JOB, step, kind, message, self.run_url))
