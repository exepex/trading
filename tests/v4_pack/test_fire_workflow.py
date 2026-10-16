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
    assert f"git add {FIRE_LOG_FOLDER} " in script and "git pull --no-rebase" in script
    assert "git push origin HEAD:main" in script and "--no-verify" not in script
    assert any("git config core.hooksPath .githooks" in step.get("run", "") for step in steps[:fire])
