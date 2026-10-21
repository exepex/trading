"""Story O1-status-only (judges 443 and 443 add. 2): the committed run log holds status, never data. Planted values
under named and unnamed keys never reach `journal/runs/<date>.json`; the full text stays in the private, git-ignored
log; the reason codes are a closed, unambiguous set of the producers' own templates."""

import json
import re
import subprocess
from datetime import datetime, time
from pathlib import Path

import pytest

from fno.daily.full_log import FULL_LOGS
from fno.daily.public_log import UNLISTED, PublicResult, ReasonRegistry, TemplateRefused
from fno.daily.reason_codes import COMMON, STEP_TEMPLATES
from fno.daily.wiring import public_recorder
from fno.desk.daily_steps import StepOutcome
from fno.desk.run_log import RunLog
from fno.health.desk_checks import RunLogCheck
from fno.health.model import Deadline
from fno.models import IST
from fno.scoreboard.committed_runs import CommittedRuns
from tests.timetable.test_daily_run import NORMAL

from .fakes import RecordedStep
from .test_day_run import day  # noqa: F401 - the fixture: one day of the run over E3's real DailyRun

REPOSITORY = Path(__file__).resolve().parents[2]
PLANTED = ("net Rs 12,345.60", "22,811.35", "Rs12345.60", "Rs12345", "NIFTY26OCT25000CE", "/home/owner/secret.txt")
PLANTED_RESULT = {
    "status": "failed",
    "reason": "every leg closed; net Rs 12,345.60",
    "error": "OSError: [Errno 2] No such file: '/home/owner/secret.txt'",
    "lines": ["spot 22,811.35"],
    "results": [{"trade_id": "t1", "reason": "Rs12345.60"}],
    "detail": {"note": "NIFTY26OCT25000CE", "amount": 12345, "level": 22811.35, "cash": "Rs12345"},
}
PLANTED_INPUTS = {"blocked": {"book1_rules": "spot 22,811.35 is far from the previous close"}}
KEPT = {"trade_id": "t1", "book": "book1_rules", "shadow": "shadow:b0-monthly-sc-v1", "how": "earlier run"}


def public() -> PublicResult:
    return PublicResult(ReasonRegistry(COMMON, STEP_TEMPLATES))


def filled(template: str) -> str:
    """A template with each placeholder filled by a sample value (times keep their format)."""
    return re.sub(r"\{[^{}:]*(:[^{}]*)?\}", lambda m: "14:38" if m.group(1) else "x1", template)


def test_planted_values_never_reach_the_committed_run_log_and_stay_whole_in_the_full_log(day):  # noqa: F811
    runner, run, *_ = day(steps={"card": RecordedStep("card", [], PLANTED_RESULT)})
    run.recorder = public_recorder(run.steps.root)
    run.day_steps["margin_check"].run = lambda d: StepOutcome(PLANTED_INPUTS, {"status": "ok", "reason": "fine"})
    runner.run(NORMAL)
    committed = RunLog.open(run.steps.root, NORMAL).path.read_text(encoding="utf-8")
    assert not [value for value in PLANTED if value in committed] and "12345" not in committed
    assert not re.search(r"\d+\.\d+", committed.replace(NORMAL.isoformat(), ""))  # no float, no decimal anywhere
    card = json.loads(committed)["steps"]["card"]["result"]
    assert card["error"] == "raised:OSError" and card["reason"] == UNLISTED and "lines" not in card
    assert card["detail"] == {"note": UNLISTED, "amount": None, "level": None, "cash": UNLISTED}
    assert json.loads(committed)["steps"]["margin_check"]["inputs"] == {"blocked": {"book1_rules": UNLISTED}}
    full = (run.steps.root / FULL_LOGS / f"{NORMAL}.json").read_text(encoding="utf-8")
    assert all(value in full for value in PLANTED)  # the full text: private, for the alert and for debugging


def test_ids_hashes_times_and_status_words_are_kept_and_codes_survive_a_second_projection():
    kept = KEPT | {"commit": "a776bf42511fa3b33629c6495ec2424d95aa12cf", "run_id": "2026-10-21-r1",
                   "snapshot_id": "nifty_20261021_151500", "at": "2026-10-21T14:58:39+05:30",
                   "outcome": "not filled"}  # fmt: skip
    assert public().public("fills", kept) == kept
    once = public().public("fills", {"reason": "no new entry: x (today's exits run; the next session opens as usual)"})
    assert once == {"reason": "fills:BLOCKED"} and public().public("fills", once) == once  # a rerun records it again


def test_every_template_maps_to_its_own_code_and_no_two_templates_match_the_same_text():
    registry = ReasonRegistry(COMMON, STEP_TEMPLATES)
    for step, pairs in (("any", COMMON), *STEP_TEMPLATES.items()):
        for code, template in pairs:
            text = filled(template)
            assert registry.matching(step, text) == [code], (code, text)  # exactly one: no two templates overlap


def test_a_template_that_starts_with_a_placeholder_matches_only_its_own_texts():
    registry = ReasonRegistry(COMMON, STEP_TEMPLATES)
    assert registry.code("owner_timing_fills", "3 applied, 1 waiting for their due mark") == "owner_timing:APPLIED"
    assert registry.code("owner_timing_fills", "2 legs filled at the 15:15 mark of 2026-10-21") == "owner_timing:OPENED"
    assert registry.code("owner_timing_fills", "net Rs 12,345.60") == UNLISTED


def test_an_unknown_text_is_unlisted_a_raise_keeps_only_its_type_and_a_template_without_a_literal_is_refused():
    registry = ReasonRegistry(COMMON, STEP_TEMPLATES)
    assert registry.code("exits", "settled at NSE's final settlement price 22,811.35 (NSE)") == UNLISTED
    assert registry.code("weather", "ValueError: price 22811.35 is stale") == "raised:ValueError"
    with pytest.raises(TemplateRefused):
        ReasonRegistry([("bad", "{a} {b}: {c}")], {})


def test_a_command_step_s_line_becomes_its_status_code_and_its_output_is_dropped():
    result = {"status": "failed", "reason": "spot 22,811.35", "exit_code": 1, "lines": ["x"], "stderr": ["Trace"]}
    assert public().public("weather", result) == {"status": "failed", "reason": "command:exit_1", "exit_code": 1}


def test_readers_still_work_on_an_old_text_bearing_log(tmp_path):
    """The four logs committed before this story hold text; health and the scoreboard read them unchanged."""
    old = REPOSITORY / "journal/runs/2026-10-21.json"
    (tmp_path / "journal/runs").mkdir(parents=True)
    (tmp_path / "journal/runs/2026-10-21.json").write_bytes(old.read_bytes())
    session = RunLog.days(tmp_path)[0]
    check = RunLogCheck(tmp_path, Deadline(time(15, 12)))
    assert check.check(session, datetime(2026, 10, 21, 18, 0, tzinfo=IST)).status
    assert list(CommittedRuns(tmp_path).logs())


def test_the_full_log_is_git_ignored_so_it_is_never_committed():
    name = f"{FULL_LOGS}/2026-10-22.json"
    assert subprocess.run(["git", "-C", str(REPOSITORY), "check-ignore", "-q", name], check=False).returncode == 0


CHILD = """import sys
print("weather 2026-10-14: spot 22,811.35")
print("alert NOT sent: ConnectionError | F&O weather 2026-10-14: refused")
print("Traceback: ValueError: cash Rs12345.60 at /home/owner/secret.txt", file=sys.stderr)
raise SystemExit(1)
"""


def test_a_real_child_s_printed_price_and_its_stderr_never_reach_the_committed_log(tmp_path):
    from fno.daily.full_log import FullRunLog, PublicRecorder
    from fno.daily.processes import ChildProcesses
    from fno.daily.steps import CommandStep

    (tmp_path / "fno").mkdir()
    (tmp_path / "fno" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "fno" / "__main__.py").write_text(CHILD, encoding="utf-8")
    relayed = []
    step = CommandStep(ChildProcesses(tmp_path, relayed.append), lambda d: ("weather", "capture"), (), lambda s: [])
    done = step.run(NORMAL)
    log = RunLog(NORMAL, tmp_path / "journal/runs" / f"{NORMAL}.json")
    now = datetime(2026, 10, 14, 14, 40, tzinfo=IST)
    PublicRecorder(public(), FullRunLog(tmp_path / FULL_LOGS)).record(
        log, "weather", now, now, done.inputs, done.result
    )
    committed = log.path.read_text(encoding="utf-8")
    assert not [text for text in ("22,811.35", "Rs12345", "secret", "Traceback", "NOT sent") if text in committed]
    assert json.loads(committed)["steps"]["weather"]["result"] == {"status": "failed", "reason": "command:exit_1",
                                                                     "exit_code": 1}  # fmt: skip
    full = json.loads((tmp_path / FULL_LOGS / f"{NORMAL}.json").read_text(encoding="utf-8"))["steps"]["weather"]
    assert full["result"]["stderr"] == ["Traceback: ValueError: cash Rs12345.60 at /home/owner/secret.txt"]
    assert "Traceback" not in " ".join(full["result"]["lines"])  # stderr is no longer merged into the kept lines
    assert relayed == ["alert NOT sent: ConnectionError | F&O weather 2026-10-14: refused"]  # still relayed once
