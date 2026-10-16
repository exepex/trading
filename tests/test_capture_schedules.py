"""global-cues.yml (A17) and vix-history.yml (A15) on a schedule (audit Part A2): the run times against the sources'
publication times, every `python -m fno` command as the parser reads it, the alert's cue names from a planted fill
output and the previous IST month the VIX job asks for."""

import re
import subprocess
from datetime import UTC, datetime, time, timedelta

import pytest
import yaml

from fno import cli
from fno.config import ROOT
from fno.global_cues import cli as cues_cli
from fno.models import IST, now_ist
from fno.vix_history import cli as vix_cli

WORKFLOWS = ROOT / ".github" / "workflows"
COMMAND = re.compile(r"python -m fno ([^\n|]+)")


def _workflow(name: str) -> dict:
    return yaml.safe_load((WORKFLOWS / name).read_text(encoding="utf-8"))


def _runs(name: str) -> list[str]:
    return [step.get("run", "") for job in _workflow(name)["jobs"].values() for step in job["steps"]]


def _ist_times(name: str) -> list[time]:
    times = []
    for entry in _workflow(name)[True]["schedule"]:  # YAML reads the key `on` as True
        minute, hour = (int(f) for f in entry["cron"].split()[:2])
        times.append(datetime(2026, 10, 16, hour, minute, tzinfo=UTC).astimezone(IST).time())
    return times


def test_the_cue_runs_come_after_the_overnight_files_and_rbi_s_rate():
    morning, afternoon = _ist_times("global-cues.yml")
    assert time(4, 30) <= morning < time(9, 15)  # after the US closes (by 02:30) and the Treasury (by about 04:30)
    assert time(13, 30) <= afternoon < time(19, 0)  # after RBI's reference rate, before the US session opens


@pytest.mark.parametrize("name", ["global-cues.yml", "vix-history.yml"])
def test_every_fno_command_parses_as_the_runner_calls_it(name, monkeypatch):
    called = []
    monkeypatch.setattr(cues_cli, "cmd_global_cues", lambda args: called.append(args.action) or 0)
    monkeypatch.setattr(vix_cli, "cmd_vix_history", lambda args: called.append(args.action) or 0)
    commands = [m.group(1).replace('"$MONTH"', "2026-09").split() for run in _runs(name) for m in COMMAND.finditer(run)]
    assert commands and all(cli.main(argv) == 0 for argv in commands)
    assert called == {"global-cues.yml": ["fill"], "vix-history.yml": ["fill", "sweep"]}[name]


def _alert_cues(tmp_path, fill_output: str) -> str:
    """The alert step's `cues=` line, run by bash over a planted fill output."""
    (tmp_path / "fill.txt").write_text(fill_output)
    line = next(r for r in _runs("global-cues.yml") if "cues=" in r).splitlines()[0]
    script = f'{line}\nprintf "%s" "$cues"'
    return subprocess.run(["bash", "-c", script], env={"RUNNER_TEMP": str(tmp_path)}, capture_output=True, text=True,
                          check=True).stdout  # fmt: skip


def test_the_alert_names_each_failed_or_stale_cue_and_only_those(tmp_path):
    output = (
        "sp500: FAILED, Cboe download failed (ConnectionError)\n"
        "us10y: 2 dates added, 0 revisions logged, last 2026-10-15\n"
        "brent: 0 dates added, 0 revisions logged, last 2026-09-22; STALE: older than 16 days on 2026-10-16\n"
        "checks: gaps 3, overlap rows 120\n"
    )
    assert _alert_cues(tmp_path, output) == "sp500,brent"
    assert _alert_cues(tmp_path, "STOPPED (RuntimeError): set FNO_GDRIVE_FOLDER_ID. Run again.\n") == ""


def test_the_vix_job_asks_for_the_previous_ist_month(tmp_path):
    line = next(r for r in _runs("vix-history.yml") if "MONTH=" in r)
    env_file = tmp_path / "env"
    subprocess.run(["bash", "-c", line], env={"GITHUB_ENV": str(env_file), "PATH": "/usr/bin:/bin"}, check=True)
    previous = now_ist().date().replace(day=1) - timedelta(days=1)
    assert env_file.read_text().strip() == f"MONTH={previous:%Y-%m}"
