"""Story GB1: the workflow is a dry run unless told otherwise and only deletes through the tool; the committed inventory
is well formed and never lists a branch the rules keep."""

import csv
import re
import sys

import yaml

from fno.config import ROOT

sys.path.insert(0, str(ROOT / "tools"))
from branch_rules import DEFAULT_BRANCH, parse_keep_list  # noqa: E402

WORKFLOW = ROOT / ".github" / "workflows" / "branch-cleanup.yml"
INVENTORY = ROOT / "docs" / "branch_inventory.csv"
KEEP_LIST = ROOT / ".github" / "branch-keep.txt"
DECISIONS = {"delete", "keep", "keep-unsure"}


def workflow() -> dict:
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


def test_manual_runs_default_to_a_dry_run_of_the_reviewed_list():
    inputs = workflow()[True]["workflow_dispatch"]["inputs"]  # YAML 1.1 reads a bare `on` key as True
    assert inputs["apply"]["default"] is False
    assert inputs["mode"]["default"] == "inventory" and inputs["mode"]["options"] == ["inventory", "merged"]


def test_the_schedule_runs_only_while_the_repository_variable_is_on():
    job = workflow()["jobs"]["cleanup"]
    assert workflow()[True]["schedule"]
    assert "vars.BRANCH_CLEANUP_SCHEDULE == 'on'" in job["if"] and "github.event_name != 'schedule'" in job["if"]


def test_permissions_are_the_two_it_needs_and_nothing_else_is_used():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert workflow()["permissions"] == {"contents": "write", "pull-requests": "read"}
    assert "secrets." not in text and "--no-verify" not in text and "git push" not in text


def test_no_expression_inside_a_script_and_the_checkout_is_main_with_history():
    steps = workflow()["jobs"]["cleanup"]["steps"]
    assert all("${{" not in step.get("run", "") for step in steps)
    assert steps[0]["with"] == {"ref": "main", "fetch-depth": 0}


def test_only_the_tool_deletes_and_the_open_pr_list_is_read_before_it():
    run = [step["run"] for step in workflow()["jobs"]["cleanup"]["steps"] if "run" in step]
    assert "gh pr list" in run[0] and "tools/branch_cleanup.py" in run[1]
    assert not re.search(r"--delete|-X DELETE", "".join(run))


def rows() -> list[dict]:
    with INVENTORY.open(newline="", encoding="utf-8") as source:
        return list(csv.DictReader(source))


def test_the_inventory_is_well_formed():
    found = rows()
    assert list(found[0]) == [
        "branch", "sha", "last_commit_utc", "merged", "commits_not_on_main", "decision", "reason",
    ]  # fmt: skip
    names = [row["branch"] for row in found]
    assert len(names) == len(set(names)) and DEFAULT_BRANCH in names
    for row in found:
        assert row["decision"] in DECISIONS and re.fullmatch(r"[0-9a-f]{40}", row["sha"]), row["branch"]
        assert row["merged"] in ("yes", "no") and row["reason"], row["branch"]


def test_the_inventory_never_deletes_main_or_a_kept_branch():
    kept = parse_keep_list(KEEP_LIST.read_text(encoding="utf-8"))
    for row in rows():
        if row["decision"] == "delete":
            assert row["branch"] != DEFAULT_BRANCH and row["branch"] not in kept, row["branch"]
