"""The forecast capture's start (response 67 addendum 5): the push that lands the 3 pm canonical snapshot on main starts
it, the cron stays as a fallback, and the gate lets at most one run capture a day; a push run after 15:13 IST stops."""

import subprocess
import sys
from datetime import datetime
from pathlib import Path

import yaml

from fno.ai.paths import pack_path
from fno.models import IST
from fno.pipeline.capture_gate import skip_reason

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/forecast-capture.yml"
THIRD_PARTY = ("requests", "yaml", "numpy", "google", "psycopg", "jsonschema")


def at(hour, minute):
    return datetime(2026, 10, 15, hour, minute, tzinfo=IST)


def test_the_snapshot_push_and_the_cron_both_start_the_capture():
    on = yaml.safe_load(WORKFLOW.read_text())[True]  # YAML reads the key `on` as true
    assert on["push"] == {"branches": ["main"], "paths": ["research/data/quotes/**/*.canonical"]}
    assert on["schedule"] == [{"cron": "30 8 * * *"}] and "workflow_dispatch" in on


def test_the_capture_runs_only_when_the_gate_says_so_and_runs_never_overlap():
    workflow = yaml.safe_load(WORKFLOW.read_text())
    assert workflow["concurrency"] == {"group": "forecast-capture", "cancel-in-progress": False}
    gate, capture = workflow["jobs"]["gate"], workflow["jobs"]["capture"]
    assert gate["steps"][0]["with"]["ref"] == "main"  # sees a pack an earlier run committed
    assert "fno.pipeline.capture_gate" in gate["steps"][-1]["run"]
    assert capture["needs"] == "gate" and capture["if"] == "${{ needs.gate.outputs.run == 'true' }}"


def test_a_day_already_captured_is_never_captured_again(tmp_path):
    assert skip_reason(tmp_path, at(15, 1), "push") == ""
    (tmp_path / pack_path(at(15, 1).date())).parent.mkdir(parents=True)
    (tmp_path / pack_path(at(15, 1).date())).write_text("{}")
    for event in ("push", "schedule", "workflow_dispatch"):
        assert "already on main" in skip_reason(tmp_path, at(15, 1), event)


def test_a_push_run_after_1513_stops_but_the_late_cron_still_records_the_day(tmp_path):
    assert skip_reason(tmp_path, at(15, 13), "push") == ""
    assert "push after 15:13 IST" in skip_reason(tmp_path, at(15, 14), "push")
    assert skip_reason(tmp_path, at(18, 0), "schedule") == ""  # the fallback still records the day (late, unscored)


def run_without_site_packages(code: str) -> subprocess.CompletedProcess:
    """Python with site-packages disabled (-S) and isolated (-I: no PYTHONPATH, no current folder), only the repository
    on its path: what a runner has before any `pip install`."""
    setup = f"import sys; sys.path.insert(0, {str(ROOT)!r}); "
    return subprocess.run([sys.executable, "-S", "-I", "-c", setup + code], capture_output=True, text=True)


def test_the_gate_runs_with_the_standard_library_alone():
    """The gate runs before any install, so a third-party import anywhere in its import graph would stop every capture,
    the cron fallback included (judge 88's should-fix)."""
    done = run_without_site_packages("from fno.pipeline.capture_gate import main; main(['--event', 'schedule'])")
    assert done.returncode == 0, done.stderr
    assert done.stdout.startswith("run=")


def test_the_check_really_has_no_installed_library():
    """Without this, a Python whose packages sit outside site-packages would let a third-party import pass unseen."""
    missing = [name for name in THIRD_PARTY if run_without_site_packages(f"import {name}").returncode == 0]
    assert missing == []
