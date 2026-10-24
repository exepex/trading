"""Story MS-P1j's daily step: the market school's `school run --session D` in the whole day, through the real
composition root (`fno/daily/wiring.py`), with only the outside services replaced (story O2's harness)."""

from datetime import date

from fno.constants import DAILY_RUN_STEPS
from fno.daily.steps import COMMAND_LIMIT_SECONDS

from .children import Foreground
from .harness import fixture_day

SCHOOL = ("school", "run", "--session")
SATURDAY = date(2026, 10, 17)


def school_command(day) -> tuple[str, ...]:
    return (*SCHOOL, day.day.isoformat())


def scripted_school(day, minutes: float, code: int, lines: list[str]) -> None:
    """The school's child replaced by one that ends `minutes` after it starts with `code` and `lines`."""
    day.children.script[school_command(day)] = Foreground(minutes, lambda: (code, lines))


def started(day) -> list[tuple[str, ...]]:
    return [key for _, key in day.children.started]


def test_the_step_sits_after_every_quote_part_and_g13d_and_before_v4_s_check_and_a4h_s_two_reads():
    """Its roads are all recorded by `quotes_done`; G13d (seconds) refuses after 15:30 as law 6 does, so it goes
    first; A4h's two close reads stay last."""
    steps = list(DAILY_RUN_STEPS)
    school = steps.index("school")
    assert steps[school - 1] == "premium_ranges" and steps.index("quotes_done") < school
    assert school < steps.index("v4_deadline") and steps[-2:] == ["close_read", "close_recheck"]


def test_a_session_runs_the_school_once_for_its_day_and_with_the_switch_off_it_writes_nothing(tmp_path, monkeypatch):
    day = fixture_day(tmp_path, monkeypatch)
    assert day.run() == (0, "day done")
    assert started(day).count(school_command(day)) == 1 and day.slack.sent == []
    assert day.step("school") == {"status": "ok", "reason": "school:OFF", "exit_code": 0}
    assert day.full_step("school")["lines"] == ["school off"]
    assert not [path for path in day.origin_files() if path.startswith("research/school/")]


def test_a_school_stop_fails_its_step_alerts_once_and_a_rerun_does_not_run_it_again(tmp_path, monkeypatch):
    day = fixture_day(tmp_path, monkeypatch)
    scripted_school(day, 2, 1, ["stopped: dashcam stuck: planted"])
    code, line = day.run()
    assert (code, line) == (1, "day done with problems: school")
    assert day.step("school")["status"] == "failed" and day.step("school")["reason"] == "school:STOPPED"
    assert len(day.slack.sent) == 1 and "step school failed: stopped: dashcam stuck: planted" in day.slack.sent[0]
    assert "candles" in day.log()["steps"]  # the run went on
    day.slack.sent.clear()
    assert day.run() == (1, "day done with problems: school")  # no retry: a later run never chooses a paper trade
    assert started(day).count(school_command(day)) == 1 and day.slack.sent == []


def test_a_school_run_past_the_command_limit_is_stopped_failed_and_the_day_goes_on(tmp_path, monkeypatch):
    day = fixture_day(tmp_path, monkeypatch)
    scripted_school(day, COMMAND_LIMIT_SECONDS / 60 + 1, 0, ["never reached"])
    code, line = day.run()
    assert (code, line) == (1, "day done with problems: school")
    assert day.step("school")["reason"] == "o1:STOPPED_AT_LIMIT"
    assert list(day.log()["steps"]) == list(DAILY_RUN_STEPS)


def test_a_school_run_that_ends_just_inside_the_limit_is_its_own_result(tmp_path, monkeypatch):
    day = fixture_day(tmp_path, monkeypatch)
    scripted_school(day, COMMAND_LIMIT_SECONDS / 60 - 1, 0, ["school off"])
    assert day.run() == (0, "day done") and day.step("school")["reason"] == "school:OFF"


def test_a_closed_day_never_starts_the_school(tmp_path, monkeypatch):
    day = fixture_day(tmp_path, monkeypatch)
    day.move_to(SATURDAY)
    day.run()
    assert (*SCHOOL, SATURDAY.isoformat()) not in started(day) and "school" not in day.log().get("steps", {})


def test_a_school_step_that_raises_is_failed_once_and_never_retried_by_a_rerun(tmp_path, monkeypatch):
    """O1's per-step rule: `Alerted` catches the raise, fails the step alone and alerts it once; a rerun repeats no
    recorded step, so no later run decides the session's paper trades."""
    day = fixture_day(tmp_path, monkeypatch)
    entry = day.children.script.pop(school_command(day))  # the child cannot start: the parent raises
    assert day.run() == (1, "day done with problems: school")
    assert len(day.slack.sent) == 1 and "step school failed: KeyError" in day.slack.sent[0]
    assert day.step("school")["status"] == "failed" and "candles" in day.log()["steps"]
    day.children.script[school_command(day)] = entry
    day.slack.sent.clear()
    assert day.run() == (1, "day done with problems: school")
    assert school_command(day) not in started(day) and day.slack.sent == []
