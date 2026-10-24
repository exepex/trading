"""global-cues.yml (A17) and vix-history.yml (A15) on a schedule (audit Part A2): the run times against the sources'
publication times, every `python -m fno` command as the parser reads it, the alert's cue names from a planted fill
output and the previous IST month the VIX job asks for."""

import re
import subprocess
from datetime import UTC, date, datetime, time, timedelta

import pytest
import yaml

from fno import cli
from fno.config import ROOT
from fno.global_cues import cli as cues_cli
from fno.models import IST, now_ist
from fno.vix_history import cli as vix_cli

WORKFLOWS = ROOT / ".github" / "workflows"
DAY = date(2026, 10, 16)
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


def test_the_cue_runs_come_after_the_us_close_and_land_before_the_open_even_5_hours_late():
    main, backup, afternoon = _ist_times("global-cues.yml")
    latest_us_close = time(2, 30)  # 16:00 New York in winter time; 01:30 IST in summer time
    five_hours_late = (datetime.combine(DAY, main) + timedelta(hours=5)).time()
    assert latest_us_close < main and five_hours_late < time(9, 15)  # judge 351: crons start 4 h 40 to 5 h 01 late
    assert time(4, 30) <= backup < time(9, 15)  # the Treasury's file, by about 04:30 IST
    assert time(13, 30) <= afternoon < time(19, 0)  # after RBI's reference rate, before the US session opens


@pytest.mark.parametrize("name", ["global-cues.yml", "vix-history.yml"])
def test_every_fno_command_parses_as_the_runner_calls_it(name, monkeypatch):
    called = []
    monkeypatch.setattr(cues_cli, "cmd_global_cues", lambda args: called.append(args.action) or 0)
    monkeypatch.setattr(vix_cli, "cmd_vix_history", lambda args: called.append(args.action) or 0)
    commands = [m.group(1).replace('"$MONTH"', "2026-09").split() for run in _runs(name) for m in COMMAND.finditer(run)]
    assert commands and all(cli.main(argv) == 0 for argv in commands)
    assert called == {"global-cues.yml": ["fill"], "vix-history.yml": ["fill", "sweep"]}[name]


def _alert_step(name: str) -> dict:
    steps = [s for job in _workflow(name)["jobs"].values() for s in job["steps"]]
    senders = [s for s in steps if "build_alert_sender" in s.get("run", "")]
    assert len(senders) == 1 and senders[0] is steps[-1]  # one alert step, the last, so it sees every step's outcome
    return senders[0]


def _fires(name: str, outcomes: dict, failed: bool = False, cancelled: bool = False) -> bool:
    """The alert step's `if:` as GitHub evaluates it: `failure()` is true after a step without continue-on-error
    failed (the commit), `!cancelled()` false once the run was cancelled or timed out."""
    expression = _alert_step(name)["if"].strip().removeprefix("${{").removesuffix("}}")
    expression = re.sub(r"steps\.(\w+)\.outcome", lambda m: repr(outcomes[m.group(1)]), expression)
    expression = expression.replace("!cancelled()", repr(not cancelled)).replace("failure()", repr(failed))
    return eval(expression.replace("&&", " and ").replace("||", " or "))  # noqa: S307 - our own workflow's condition


@pytest.mark.parametrize(
    ("name", "steps"), [("global-cues.yml", ("fill",)), ("vix-history.yml", ("fill", "sweep"))]
)  # fmt: skip
def test_the_alert_fires_on_any_failed_step_and_a_failed_commit_and_never_on_a_clean_or_cancelled_run(name, steps):
    clean = dict.fromkeys(steps, "success")
    assert not _fires(name, clean) and not _fires(name, clean, failed=True, cancelled=True)
    assert _fires(name, clean, failed=True)  # judge 351 SF1: the commit failed and every step before it succeeded
    for step in steps:
        assert _fires(name, clean | {step: "failure"}) and _fires(name, clean | {step: "failure"}, failed=True)
        assert _fires(name, clean | {step: "skipped"}, failed=True)  # an earlier setup step failed
    assert "exit 1" in _alert_step(name)["run"]  # the run is marked failed after its line


def _alert_text(tmp_path, fill_output: str, commit: str = "success") -> str:
    """The alert step's lines before its Python, run by bash over a planted fill output and commit outcome."""
    (tmp_path / "fill.txt").write_text(fill_output)
    lines = _alert_step("global-cues.yml")["run"].split("python -c")[0].replace("${{ steps.commit.outcome }}", commit)
    script = f'{lines}\nprintf "%s" "${{what:-the run failed}}"'
    return subprocess.run(["bash", "-c", script], env={"RUNNER_TEMP": str(tmp_path)}, capture_output=True, text=True,
                          check=True).stdout  # fmt: skip


def test_the_alert_names_each_failed_or_stale_cue_and_a_failed_commit(tmp_path):
    output = (
        "sp500: FAILED, Cboe download failed (ConnectionError)\n"
        "us10y: 2 dates added, 0 revisions logged, last 2026-10-15\n"
        "brent: 0 dates added, 0 revisions logged, last 2026-09-22; STALE: older than 16 days on 2026-10-16\n"
        "gaps: us10y missing 2\n"
        "nasdaq100: BEHIND, its newest value is older than the session expected by 09:15 IST\n"
        "still behind (alerted before): sp500\n"
    )
    assert _alert_text(tmp_path, output) == "sp500,brent,nasdaq100 failed, stale or behind (the log names why)"
    assert _alert_text(tmp_path, "us10y: 1 dates added\nchecks FAILED (OSError): disk full\n") == (
        "checks failed, stale or behind (the log names why)"
    )
    assert _alert_text(tmp_path, "STOPPED (RuntimeError): set FNO_GDRIVE_FOLDER_ID. Run again.\n") == "the run failed"
    assert _alert_text(tmp_path, "us10y: 1 dates added\n", commit="failure") == (
        "the commit step did not succeed (nothing of this run is in the repository)"
    )


def test_the_vix_job_asks_for_the_previous_ist_month(tmp_path):
    line = next(r for r in _runs("vix-history.yml") if "MONTH=" in r)
    env_file = tmp_path / "env"
    subprocess.run(["bash", "-c", line], env={"GITHUB_ENV": str(env_file), "PATH": "/usr/bin:/bin"}, check=True)
    previous = now_ist().date().replace(day=1) - timedelta(days=1)
    assert env_file.read_text().strip() == f"MONTH={previous:%Y-%m}"
