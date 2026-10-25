"""REC1b's step in the daily run: right after `school`, its own live date (null: not live, nothing runs), no
pathspec (it pushes its own receipt), and no second status alert (the command alerts each failure itself)."""

from datetime import date

from fno.config import load_app_config
from fno.constants import DAILY_RUN_STEPS, STEP_NOT_LIVE
from fno.daily.steps import Alerted, CommandStep, LiveFrom
from fno.daily.wiring import live_dates
from tests.daily.live_dates import without_live_dates
from tests.price_ranges.test_score_steps import day_steps

DAY = date(2026, 11, 2)


def test_the_step_follows_the_school_and_is_off_until_the_owner_s_go(monkeypatch):
    step = day_steps(monkeypatch, without_live_dates())["recommend"]
    assert DAILY_RUN_STEPS.index("recommend") == DAILY_RUN_STEPS.index("school") + 1
    assert isinstance(step, Alerted) and isinstance(step.step, LiveFrom) and isinstance(step.step.step, CommandStep)
    command = step.step.step
    assert tuple(command.arguments(DAY)) == ("recommend", "decide", "--on", "2026-11-02")
    assert tuple(command.pathspecs) == ()  # never the whole tree: the command pushes its own receipt
    assert step.status_alerts is False
    assert step.step.live_from is None and step.run(DAY).result["status"] == STEP_NOT_LIVE


def test_the_repository_s_config_keeps_it_off():
    assert live_dates(load_app_config())["recommend"] is None


def test_its_live_date_is_its_own_key():
    assert live_dates({"daily": {"live_from": {"recommend": "2026-11-02", "school": "2026-10-01"}}})["recommend"] == DAY


def test_every_last_line_of_the_command_has_its_own_public_code():
    from fno.daily.public_log import ReasonRegistry
    from fno.daily.reason_codes import COMMON, STEP_TEMPLATES

    registry = ReasonRegistry(COMMON, STEP_TEMPLATES)
    last_lines = {
        "recommend:POSTED": "PAPER ONLY. Recommender (not the card) for 02 Nov 2026. Real money: DO NOT TRADE (no "
        "version has passed). This is the record made at 09:50 UTC, whose save stopped before its push, now receipted. "
        "Record recommend/2026/11/2026-11-02.json, SHA-256 abababababab.",
        "recommend:INPUT_PROBLEM": "recommendation for 2026-11-02, input problem: the day's conditions could not be "
        "read: log gone",
        "recommend:NOT_POSTED": "recommendation NOT posted for 2026-11-02: recommend/x.json: RuntimeError",
        "recommend:NOT_A_SESSION": "recommend 2026-11-01: not a trading day, nothing recorded",
    }
    assert {code: registry.matching("recommend", text) for code, text in last_lines.items()} == {
        code: [code] for code in last_lines
    }
