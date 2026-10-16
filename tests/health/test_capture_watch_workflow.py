"""Story O10: the capture watcher's workflow watches every scheduled job (CI aside), reads runs and commits only the
capture-error log, and pastes no event value or secret into a script."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

WORKFLOWS = Path(__file__).resolve().parents[2] / ".github" / "workflows"
WATCHER = WORKFLOWS / "capture-watch.yml"
NOT_WATCHED = {"checks", "capture-watch"}  # CI on pushes, and the watcher itself


def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def triggers(workflow: dict) -> dict:
    return workflow.get("on", workflow.get(True))  # YAML 1.1 reads a bare `on` key as True


def test_every_job_is_watched():
    names = {load(path)["name"] for path in WORKFLOWS.glob("*.yml")}
    watched = set(triggers(load(WATCHER))["workflow_run"]["workflows"])
    assert watched == names - NOT_WATCHED
    assert triggers(load(WATCHER))["workflow_run"]["types"] == ["completed"]


def test_permissions_and_condition():
    workflow = load(WATCHER)
    assert workflow["permissions"] == {"actions": "read", "contents": "write"}
    assert "concurrency" not in workflow  # a group would cancel pending runs and lose rows
    job = workflow["jobs"]["record"]
    assert "!= 'success'" in job["if"] and "!= 'skipped'" in job["if"]


def test_commits_only_the_capture_error_log():
    text = WATCHER.read_text(encoding="utf-8")
    assert re.findall(r"git add (\S+)", text) == ["research/ops/capture_errors.csv"]
    assert "--no-verify" not in text


def test_no_expression_inside_a_script():
    for step in load(WATCHER)["jobs"]["record"]["steps"]:
        assert "${{" not in step.get("run", ""), step.get("name")


def test_union_merge_for_the_log():
    attributes = (WORKFLOWS.parents[1] / ".gitattributes").read_text(encoding="utf-8")
    assert "research/ops/capture_errors.csv merge=union" in attributes
