"""A20a criteria 13 and 14: the workflow's slots, rights and alert line, read from the YAML; the job commits manifest
rows only (no data file in the repository)."""

from pathlib import Path

import yaml

from fno.storage.wiring import MANIFEST_FOLDER, build_manifest_recorder

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "fo-masters.yml"


def load() -> dict:
    return yaml.safe_load(WORKFLOW.read_text())


def test_three_daily_slots_morning_retry_and_evening():
    crons = [slot["cron"] for slot in load()[True]["schedule"]]  # YAML 1.1 reads the key `on` as True
    assert crons == ["15 2 * * *", "45 5 * * *", "15 13 * * *"]  # 07:45, 11:15 and 18:45 IST


def test_rights_job_step_and_the_crash_only_alert_line():
    flow = load()
    assert flow["permissions"] == {"contents": "write"}
    steps = flow["jobs"]["masters"]["steps"]
    job = next(s for s in steps if s.get("id") == "masters")
    assert job["run"] == "python -m fno fo-masters"
    alert = steps[-1]
    assert alert["if"] == "${{ failure() && steps.masters.outputs.posted != 'true' }}"
    assert "build_alert_sender" in alert["run"]


def test_no_secret_value_is_written_in_the_workflow():
    for name, value in load()["jobs"]["masters"]["env"].items():
        assert value == f"${{{{ secrets.{name} }}}}", name


def test_the_job_commits_only_the_manifest_folder():
    assert build_manifest_recorder().folder == "research/data/manifests" == MANIFEST_FOLDER.relative_to(ROOT).as_posix()
