"""Shared test material for the playbook (story D1): a valid document, files in a temporary git repository, and
stand-in live reports."""

from __future__ import annotations

import copy
import subprocess
from collections.abc import Mapping
from datetime import date
from pathlib import Path

import yaml

from fno.playbook.lifecycle import StatusChanger
from fno.playbook.live_reports import LiveReports
from fno.playbook.loader import PlaybookLoader
from fno.playbook.wiring import build_playbook_loader, build_status_changer

EVIDENCE_FILES = ("research/x/results.json", "reviews/red_team.md", "reviews/judge.md", "research/x/FREEZE.md")
DOCUMENT = {
    "name": "sc-test", "version": 1, "status": "research", "payer": "option buyers", "edge_family": "short premium",
    "structure": {
        "code": "SC", "strikes_rule": "spot x 1.02 / 0.98", "width_rule": "widest under the cap",
        "widths": [300, 200, 100], "lots": 1,
        "expiry": {"kind": "monthly", "min_days": 30, "max_days": 45, "exit_days_before_expiry": 21},
    },
    "entry_conditions": [
        {"feature": "F1_atm_iv_minus_rv20", "operator": ">", "threshold": 0},
        {"feature": "F3_scheduled_event_in_window", "operator": "is", "threshold": False},
    ],
    "live_use_rule": {"min_days": 20, "min_agreement": 0.9, "min_available": 0.9},
    "size_rule": "1 lot",
    "funding": {"margin_per_lot": 20000, "source": "broker calculator", "date": date(2026, 10, 14)},
    "exits": {"time": "21 days to expiry", "profit": "none", "loss": "none (the bought wings cap it)", "event": "none"},
    "evaluation_plan": {
        "expected_range": {"low": -500, "high": 800}, "expected_net_per_opportunity": 150,
        "expected_net_source": "discovery results",
        "unit": "Rs per opportunity",
        "review_dates": [date(2027, 1, 14)], "pause_rules": ["one trade loses over Rs 10,000"],
        "catastrophic_loss_rs": 10000,
    },
    "evidence": dict.fromkeys(
        ("test_results_path", "test_results_commit", "red_team_note", "judge_verdict", "freeze_record",
         "owner_approval_date"),
    ),
}  # fmt: skip
LIVE_FEATURES = ("F1_live_atm_iv_minus_rv20", "F3_live_scheduled_event_in_window")


def document(**changes) -> dict:
    result = copy.deepcopy(DOCUMENT)
    result.update(changes)
    return result


def write(folder: Path, doc: dict, file_name: str | None = None) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / (file_name or f"{doc['name']}-v{doc['version']}.yaml")
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
    return path


def report(feature: str, agree_days: int, days: int = 20) -> dict:
    rows = [
        {"day": f"2026-11-{n + 1:02d}", "live": 1.0, "close": 1.0 if n < agree_days else -1.0, "agrees": n < agree_days,
         "captured_at": None}
        for n in range(days)
    ]  # fmt: skip
    return {"live_feature": feature, "validated": True, "comparisons": rows}


class FixedReports(LiveReports):
    def __init__(self, reports: Mapping[str, Mapping]):
        self.reports = dict(reports)

    def report(self, live_feature: str) -> Mapping | None:
        return self.reports.get(live_feature)


def validated_reports() -> FixedReports:
    return FixedReports({name: report(name, 20) for name in LIVE_FEATURES})


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True).stdout.strip()


def commit_all(root: Path, message: str = "change") -> str:
    git(root, "add", "-A")
    git(root, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", message)
    return git(root, "rev-parse", "HEAD")


def repository(root: Path) -> str:
    """A git repository with committed evidence files; returns the commit."""
    git(root, "init", "-q")
    for name in EVIDENCE_FILES:
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_text("evidence\n", encoding="utf-8")
    return commit_all(root, "evidence")


def filled_evidence(results_commit: str) -> dict:
    paths = dict(zip(("test_results_path", "red_team_note", "judge_verdict", "freeze_record"), EVIDENCE_FILES))
    return {**paths, "test_results_commit": results_commit, "owner_approval_date": date(2026, 10, 20)}


def loader(root: Path, reports: LiveReports | None = None) -> PlaybookLoader:
    """The app's own loader and checks (wiring), on a test repository and stand-in live reports."""
    return build_playbook_loader(root, reports or validated_reports())


def changer(root: Path, reports: LiveReports | None = None) -> StatusChanger:
    return build_status_changer(root, reports or validated_reports())
