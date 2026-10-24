"""Story G10 part 2, criterion 5: the fire workflow starts on the push of the release record's receipt only, with no
cron, and fires today's day only."""

from datetime import date
from pathlib import Path

import yaml

from fno.forecast_v4.terms import V4_LATEST_FIRE
from fno.storage.data_wiring import DATA_AREA, RECEIPTS_FOLDER
from fno.storage.receipts import ReceiptFolder
from fno.v4_pack.paths import release_path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "v4-fire.yml"


def _workflow() -> dict:
    return yaml.safe_load(WORKFLOW.read_text())


def test_the_trigger_path_is_the_release_records_receipt_path():
    receipt = ReceiptFolder(ROOT / RECEIPTS_FOLDER).file_for(f"{DATA_AREA}/{release_path(date(2026, 10, 22))}")
    relative = receipt.relative_to(ROOT).as_posix()
    (pattern,) = _workflow()[True]["push"]["paths"]  # YAML reads the key "on" as True
    assert pattern.endswith("/**") and relative.startswith(pattern[: -len("**")])
    assert relative == "receipts/data/v4/days/2026/2026-10-22.json.sha256"
    assert "receipts/data/v4/days/${day:0:4}/${day}.json.sha256" in WORKFLOW.read_text()


def test_no_schedule_starts_the_fire():
    triggers = _workflow()[True]
    assert set(triggers) == {"push"} and triggers["push"]["branches"] == ["main"]
    assert "schedule:" not in WORKFLOW.read_text()


def test_the_fire_names_its_day_and_the_latest_start_is_in_the_terms():
    assert 'python -m fno ai fire --protocol v4 --day "${{ steps.day.outputs.day }}"' in WORKFLOW.read_text()
    assert V4_LATEST_FIRE.isoformat() == "14:55:00"


FIRE_LOG_FOLDER = "research/forecasts/ai_v4"  # G11's fired_v4_path(day) lives under it; G11's test pins the two


def test_the_fire_log_is_committed_and_pushed_after_the_fire():
    steps = _workflow()["jobs"]["fire"]["steps"]
    names = [step.get("name", "") for step in steps]
    fire = next(i for i, name in enumerate(names) if name.startswith("Fire the AI books"))
    commit = steps[next(i for i, name in enumerate(names) if name.startswith("Commit the fire log"))]
    assert names.index(commit["name"]) > fire and "!cancelled()" in commit["if"]
    script = commit["run"]
    assert f"git add {FIRE_LOG_FOLDER} ;" in script and "git pull --no-rebase" in script
    assert "git push origin HEAD:main" in script and "--no-verify" not in script
    assert any("git config core.hooksPath .githooks" in step.get("run", "") for step in steps[:fire])


def _today_step() -> str:
    steps = _workflow()["jobs"]["fire"]["steps"]
    return next(step["run"] for step in steps if step.get("name", "").startswith("Today's release record only"))


def _run_today_step(tmp_path, receipt_days):
    """G11 C16: the workflow's own day step, run as GitHub runs it, in a checkout holding `receipt_days`' receipts."""
    import os
    import subprocess

    for day in receipt_days:
        path = tmp_path / f"receipts/data/v4/days/{day[:4]}/{day}.json.sha256"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x\n")
    output, summary = tmp_path / "out", tmp_path / "summary"
    env = os.environ | {"GITHUB_OUTPUT": str(output), "GITHUB_STEP_SUMMARY": str(summary)}
    subprocess.run(["bash", "-c", _today_step()], cwd=tmp_path, env=env, check=True)
    return output.read_text() if output.exists() else "", summary.read_text() if summary.exists() else ""


def test_a_catch_up_push_of_an_earlier_day_fires_nothing(tmp_path):
    import subprocess

    yesterday = subprocess.run(["bash", "-c", "TZ=Asia/Kolkata date -d yesterday +%F"], capture_output=True, text=True)
    output, summary = _run_today_step(tmp_path, [yesterday.stdout.strip()])
    assert output == "" and "nothing fired" in summary


def test_todays_release_record_names_today(tmp_path):
    import subprocess

    today = subprocess.run(["bash", "-c", "TZ=Asia/Kolkata date +%F"], capture_output=True, text=True).stdout.strip()
    output, _ = _run_today_step(tmp_path, [today])
    assert output == f"day={today}\n"


def test_forecast_capture_waits_for_v4s_reveals_before_its_v4_collect():
    """G11 C16: collect writes each audit once, so it runs only after both protocols' reveals are in (or 15:30)."""
    text = (ROOT / ".github" / "workflows" / "forecast-capture.yml").read_text()
    wait, collect = text.index("python -m fno ai reveals-ready --protocol v4"), text.index("ai collect --protocol v4")
    assert wait < collect and "date -d 'today 15:30'" in text[text.rindex("limit=", 0, wait) : wait]


def _step(name: str) -> dict:
    return next(s for s in _workflow()["jobs"]["fire"]["steps"] if s.get("name", "").startswith(name))


def _git(cwd, *args):
    import subprocess

    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout


def _checkout(tmp_path):
    """A clone of a bare `origin` with one commit on main: the job's checkout, offline."""
    origin, work = tmp_path / "origin.git", tmp_path / "work"
    _git(tmp_path, "init", "-q", "--bare", "-b", "main", str(origin))
    _git(tmp_path, "clone", "-q", str(origin), str(work))
    for args in (["config", "user.email", "fire@example.invalid"], ["config", "user.name", "fire"],
                 ["commit", "-q", "--allow-empty", "-m", "main"], ["push", "-q", "origin", "HEAD:main"]):  # fmt: skip
        _git(work, *args)
    return origin, work


def _run_commit_step(work):
    import os
    import subprocess

    script = _step("Commit the fire log")["run"].replace("${{ steps.day.outputs.day }}", "2026-10-26")
    return subprocess.run(["bash", "-e", "-c", script], cwd=work, env=os.environ, capture_output=True, text=True)


def test_before_go_live_no_folder_means_nothing_to_commit_and_no_failure(tmp_path):
    """G11 C16 E (review of dfb26381): `git add` of a missing folder exits 128; the step must not fail the job."""
    origin, work = _checkout(tmp_path)
    done = _run_commit_step(work)
    assert done.returncode == 0, done.stderr
    assert _git(origin, "log", "--oneline", "main").count("\n") == 1  # nothing pushed


def test_a_fire_log_is_committed_and_pushed(tmp_path):
    origin, work = _checkout(tmp_path)
    log = work / FIRE_LOG_FOLDER / "2026" / "2026-10-26_fired.json"
    log.parent.mkdir(parents=True)
    log.write_text("{}\n")
    done = _run_commit_step(work)
    assert done.returncode == 0, done.stderr
    assert "v4 AI fire log 2026-10-26" in _git(origin, "log", "-1", "--format=%s", "main")


def test_a_failed_fire_fails_the_job_and_the_job_alerts():
    fire = _step("Fire the AI books")["run"]
    assert fire.index("set -o pipefail") < fire.index("| tee fire.log")
    alert = _step("Alert #fno-desk when the fire itself failed")
    assert alert["if"] == "${{ failure() }}" and "build_alert_sender().send" in alert["run"]


def test_a_refused_push_is_pulled_and_pushed_once_more():
    script = _step("Commit the fire log")["run"]
    assert "for attempt in 1 2" in script and "--no-verify" not in script


def test_forecast_captures_v4_collect_fails_loudly():
    """A failed v4 collect is never hidden behind tee (the step sets pipefail first)."""
    capture = yaml.safe_load((ROOT / ".github" / "workflows" / "forecast-capture.yml").read_text())
    steps = [s for job in capture["jobs"].values() for s in job["steps"]]
    collect = next(s["run"] for s in steps if "ai collect --protocol v4" in s.get("run", ""))
    assert collect.index("set -o pipefail") < collect.index("python -m fno ai collect --protocol v4 | tee -a ai.log")
