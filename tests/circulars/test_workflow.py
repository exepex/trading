"""A20b criteria 13 and 14: the workflow's hourly slots, rights and alert line, read from the YAML; the job commits
only receipts and the open-problem keys (no data file in the repository)."""

from pathlib import Path

import yaml

from fno.circulars.wiring import ALERT_STATE_FILE, ALERT_STATE_FOLDER
from fno.storage.data_wiring import build_receipt_committer

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "circulars.yml"


def load() -> dict:
    return yaml.safe_load(WORKFLOW.read_text())


def test_hourly_from_08_00_to_22_00_ist():
    assert [slot["cron"] for slot in load()[True]["schedule"]] == ["30 2-16 * * *"]  # YAML 1.1 reads `on` as True


def test_rights_job_step_and_the_crash_only_alert_line():
    flow = load()
    assert flow["permissions"] == {"contents": "write"}
    steps = flow["jobs"]["circulars"]["steps"]
    assert next(s for s in steps if s.get("id") == "circulars")["run"] == "python -m fno circulars"
    alert = steps[-1]
    assert alert["name"].startswith("Alert") and alert["if"].startswith("${{ failure() }}")  # O10's watcher sees it ran
    assert alert["env"] == {"POSTED": "${{ steps.circulars.outputs.posted }}"}
    assert all("#" not in step.get("name", "") for step in steps)  # a " #" would cut the name (YAML comment)
    assert alert["run"].startswith('if [ "$POSTED" = "true" ]; then') and "exit 0; fi" in alert["run"].splitlines()[0]


def test_no_secret_value_is_written_in_the_workflow():
    for name, value in load()["jobs"]["circulars"]["env"].items():
        assert value == f"${{{{ secrets.{name} }}}}", name


def test_the_job_commits_only_receipts_and_the_open_problem_keys():
    assert build_receipt_committer().folder == "receipts"
    assert ALERT_STATE_FOLDER.relative_to(ROOT).as_posix() == "research/ops/alerts"
    assert ALERT_STATE_FILE.parent == ALERT_STATE_FOLDER


def test_the_alert_step_posts_nothing_and_succeeds_when_the_job_already_spoke():
    import subprocess

    script = load()["jobs"]["circulars"]["steps"][-1]["run"]
    done = subprocess.run(["bash", "-e", "-c", script], env={"POSTED": "true", "PATH": "/usr/bin:/bin"},
                          capture_output=True, text=True)  # fmt: skip
    assert done.returncode == 0 and "already spoke" in done.stdout and "python" not in done.stderr
