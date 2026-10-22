"""Story O1-desk-freeze, acceptance 5: what reads the desk's steps on a later day reads a frozen session as frozen.
O8's health check shows no missed or late decisions, scoreboard B counts no missed run, and the card's last-session
line never says "no valid execution snapshot"."""

import json
from datetime import date, datetime, time

from fno.cards.rule_checks import DESK_FROZEN as CARD_FROZEN
from fno.cards.rule_checks import ExecutionOutcome, RunLogReader, run_log_path
from fno.constants import BOOK1_RULES, DAILY_RUN_STEPS, DESK_FROZEN_STEPS, HEALTH_MISSED, HEALTH_NOT_EXPECTED
from fno.desk.daily_run import FROZEN
from fno.desk.run_log import RunLog
from fno.health.desk_checks import DESK_FROZEN, RunLogCheck
from fno.health.model import Deadline
from fno.models import IST
from fno.scoreboard.committed_runs import CommittedRuns
from tests.cards.fakes import FakeRecords
from tests.cards.test_rule_checks import TODAY_TIMES

FROZEN_DAY, RESTART = date(2026, 10, 26), date(2026, 10, 27)
FROZEN_RESULT = {"status": "frozen", "reason": "desk:FROZEN"}


def frozen_log(root, day=FROZEN_DAY, **failed) -> RunLog:
    """A whole frozen session as the run commits it: every desk step frozen, the rest ok (or as given)."""
    log = RunLog.open(root, day)
    at = datetime.combine(day, time(15, 12), IST)
    for name in DAILY_RUN_STEPS:
        result = FROZEN_RESULT if name in DESK_FROZEN_STEPS else failed.get(name, {"status": "ok"})
        log.record(name, at, at, {}, result)
    return log


def evening(day=FROZEN_DAY) -> datetime:
    return datetime.combine(day, time(18, 0), IST)


def test_health_shows_a_frozen_session_as_not_expected_never_missed_or_late(tmp_path):
    frozen_log(tmp_path)
    result = RunLogCheck(tmp_path, Deadline(time(15, 12))).check(FROZEN_DAY, evening())
    assert (result.status, result.detail) == (HEALTH_NOT_EXPECTED, DESK_FROZEN)


def test_health_still_shows_a_failed_step_of_a_frozen_session(tmp_path):
    frozen_log(tmp_path, weather={"status": "failed", "reason": "raised:OSError"})
    result = RunLogCheck(tmp_path, Deadline(time(15, 12))).check(FROZEN_DAY, evening())
    assert result.status == HEALTH_MISSED and "weather failed" in result.detail


def test_health_still_shows_a_frozen_session_that_stopped_before_its_end(tmp_path):
    log = RunLog.open(tmp_path, FROZEN_DAY)
    at = datetime.combine(FROZEN_DAY, time(15, 12), IST)
    for name in DAILY_RUN_STEPS[: DAILY_RUN_STEPS.index("decisions") + 1]:
        log.record(name, at, at, {}, FROZEN_RESULT if name in DESK_FROZEN_STEPS else {"status": "ok"})
    result = RunLogCheck(tmp_path, Deadline(time(15, 12))).check(FROZEN_DAY, evening())
    assert result.status == HEALTH_MISSED and "steps not run" in result.detail


def test_scoreboard_b_counts_no_missed_decision_on_a_frozen_session(tmp_path):
    frozen_log(tmp_path)
    assert CommittedRuns(tmp_path).missed_runs(BOOK1_RULES, [FROZEN_DAY], lambda d: False) == []
    assert CommittedRuns(tmp_path).runs() == []  # nothing decided, nothing scored


def test_scoreboard_b_still_counts_a_missed_exit_review_when_a_trade_was_held(tmp_path):
    """Belt and braces: the freeze keeps the exits while a position is open, so a frozen exits step with a held trade
    is a real miss, and it still shows."""
    frozen_log(tmp_path, day=RESTART)
    found = CommittedRuns(tmp_path).missed_runs(BOOK1_RULES, [FROZEN_DAY, RESTART], lambda d: True)
    assert [(row["day"], row["missed_decision"], row["missed_exit_review"]) for row in found] == [
        ("2026-10-26", True, False), ("2026-10-27", False, True)]  # fmt: skip


def card_line(files: dict) -> list[str]:
    runs = RunLogReader(FakeRecords(files))
    return ExecutionOutcome(runs, TODAY_TIMES, lambda d: FROZEN_DAY).outcome(RESTART).line


def steps_file(day: date, **steps) -> bytes:
    return json.dumps({"day": day.isoformat(), "kind": "daily_run", "steps": {
        name: {"started_at": "", "finished_at": "", "inputs": {}, "result": result} for name, result in steps.items()
    }}).encode()  # fmt: skip


def test_the_restart_day_s_card_says_the_last_session_was_frozen():
    line = card_line({run_log_path(FROZEN_DAY): steps_file(FROZEN_DAY, snapshot=FROZEN_RESULT)})
    assert line == f"not yet decided: the desk has not run today; last session ({FROZEN_DAY}): {CARD_FROZEN}"
    assert "no valid execution snapshot" not in line


def test_the_committed_frozen_reason_is_the_desk_s_own_template():
    from fno.daily.public_log import PublicResult, ReasonRegistry
    from fno.daily.reason_codes import COMMON, STEP_TEMPLATES

    public = PublicResult(ReasonRegistry(COMMON, STEP_TEMPLATES))
    assert all(
        public.public(name, {"status": "frozen", "reason": FROZEN}) == FROZEN_RESULT for name in DESK_FROZEN_STEPS
    )
