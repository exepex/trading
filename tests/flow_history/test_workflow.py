"""Criterion 4: the daily workflow runs at 21:30 IST with a 07:15 retry, archives and enters both datasets, and always
leaves O10 an alert step that speaks only for a failed step that did not post its own line (judge 359's pattern)."""

from __future__ import annotations

from pathlib import Path

import yaml

WORKFLOW = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "flow-history.yml"


def _workflow() -> dict:
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


def _steps() -> list[dict]:
    return _workflow()["jobs"]["flows"]["steps"]


def test_runs_at_2130_ist_and_retries_at_0715_ist():
    crons = [entry["cron"] for entry in _workflow()[True]["schedule"]]  # YAML reads "on" as True
    assert crons == ["0 16 * * *", "45 1 * * *"]


def test_archives_revises_and_enters_both_datasets():
    runs = " ".join(step.get("run", "") for step in _steps())
    for name in ("participant-volume", "fii-stats"):
        assert f"data-librarian {name}" in runs and f"data-revisions sweep {name}" in runs
        assert f"flows table {name}" in runs


def test_the_alert_step_runs_on_failure_and_reads_the_tables_own_lines():
    alert = next(step for step in _steps() if step.get("name", "").startswith("Alert"))
    assert alert["if"] == "${{ failure() }}"
    assert "steps.volume_table.outputs.posted == 'true'" in alert["env"]["VOLUME_TABLE"]
    assert "steps.fii_table.outputs.posted == 'true'" in alert["env"]["FII_TABLE"]
    assert "exit 0" in alert["run"]  # quiet when every failed step already spoke


def test_every_work_step_continues_so_the_run_fails_once_at_the_end():
    work = [step for step in _steps() if step.get("id") in ("volume", "fii", "revisions", "volume_table", "fii_table")]
    assert len(work) == 5 and all(step["continue-on-error"] is True for step in work)
    fail = next(step for step in _steps() if step.get("name", "").startswith("Fail the run"))
    assert all(f"steps.{s['id']}.outcome" in fail["env"]["OUTCOMES"] for s in work)
