"""Composition root of the daily health check (story O8): the repository's files and history, F1's GitHub push
receipts, the NSE calendar, the desk timetable from config.yaml, the run record and the #fno-desk alert sender. Another
evidence source or receipt source is one new class plus one line here."""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path

from ..ai.receipts import GitHubActivityReceipts
from ..config import ROOT
from ..constants import ENV_GITHUB_TOKEN, GITHUB_REPOSITORY_VARIABLE, HEALTH_RUNS_FILE
from ..desk.timetable import timetable_from_config
from ..storage.wiring import build_session_calendar
from .checker import HealthCheck
from .evidence import Evidence, HealthHistory
from .expectations import build_expectations
from .run_record import RunRecord


def build_run_record(root: Path = ROOT) -> RunRecord:
    return RunRecord(Path(root) / HEALTH_RUNS_FILE)


def build_health_check(cfg: dict, root: Path = ROOT, env: Mapping[str, str] = os.environ) -> HealthCheck:
    history = HealthHistory(Path(root))
    receipts = GitHubActivityReceipts(env.get(GITHUB_REPOSITORY_VARIABLE, ""), env.get(ENV_GITHUB_TOKEN, ""), history)
    evidence = Evidence(Path(root), history, receipts)
    expectations = build_expectations(evidence, Path(root), timetable_from_config(cfg))
    return HealthCheck(expectations, build_session_calendar(), build_run_record(root), cfg["health"]["window_days"])
