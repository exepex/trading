"""LR1's boundaries: it never reaches a decision, never scores a second way, reads the AI's files in one place, and
runs on the owner's Saturday schedule with G4's Monday post retired."""

import yaml

from fno.config import ROOT
from fno.storage.wiring import OWNER_UPLOAD_SETTINGS
from tests.import_graph import full_imports

PACKAGES = ("fno/learning", "fno/advocate")
NEVER = ("fno.desk", "fno.books", "fno.risk", "fno.checks")  # nothing here can decide a trade
NO_SECOND_SCORING = ("fno.forecast_scoring.scores", "fno.forecast_scoring.scoring", "fno.forecast_scoring.v4.scores",
                     "fno.forecast_scoring.v4.scoring", "fno.forecast_scoring.v4.comparison",
                     "fno.forecast_scoring.block_bootstrap")  # fmt: skip
AI_FILES = ("_prose.md", "_objections.md")


def _files():
    return [p for folder in PACKAGES for p in (ROOT / folder).glob("*.py")]


def test_nothing_imports_the_desk_books_risk_or_checks():
    bad = [(p.name, m) for p in _files() for m in full_imports(p) if m.startswith(NEVER)]
    assert bad == []


def test_no_score_is_computed_a_second_way():
    bad = [(p.name, m) for p in _files() for m in full_imports(p) if m in NO_SECOND_SCORING]
    assert bad == []


def test_only_publish_and_the_routine_adapter_name_the_ai_files():
    named = sorted(
        p.relative_to(ROOT).as_posix() for p in (ROOT / "fno").rglob("*.py")
        if any(f in p.read_text(encoding="utf-8") for f in AI_FILES)
    )  # fmt: skip
    assert named == ["fno/advocate/routine_file.py", "fno/learning/publish.py"]


def _workflow(name: str) -> dict:
    return yaml.safe_load((ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8"))


def test_saturday_10_41_and_11_41_ist_and_g4_s_monday_post_retired():
    crons = [c["cron"] for c in _workflow("postmortem-weekly.yml")[True]["schedule"]]  # YAML reads `on` as True
    assert crons == ["11 5 * * 6", "11 6 * * 6"]  # 05:11 and 06:11 UTC are 10:41 and 11:41 IST
    g4 = (ROOT / ".github" / "workflows" / "forecast-scores.yml").read_text(encoding="utf-8")
    assert "41 3 * * 1" not in g4 and "summary --send" not in g4


def test_the_workflow_never_skips_the_record_scan_and_uses_only_the_fno_slack_token():
    job = _workflow("postmortem-weekly.yml")["jobs"]["postmortem"]
    runs = "\n".join(step.get("run", "") for step in job["steps"])
    assert "--no-verify" not in runs and "core.hooksPath .githooks" in runs
    drive = [*OWNER_UPLOAD_SETTINGS]  # G10 completion: G8's report reads the day labels from Drive
    assert sorted(job["env"]) == sorted([*drive, "FNO_ROUTINE_POSTMORTEM_TOKEN", "FNO_ROUTINE_POSTMORTEM_TRIGGER_ID",
                                         "FNO_SLACK_BOT_TOKEN", "STEP"])  # fmt: skip
