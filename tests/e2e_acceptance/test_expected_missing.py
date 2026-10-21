"""Story O11, what is not implemented yet: one strict xfail per missing piece of the core engine or of the go-live
gate (DESK_DECISIONS row 247), named by the story or owner step that closes it (`docs/CORE_ENGINE_PLAN.md`). When it
lands, its test passes, the strict xfail fails the suite, and that builder deletes the marker in the same branch (and,
for `not_built`, writes the real check). The suite is complete when this file holds no xfail."""

import json

import pytest

from fno import constants
from fno.cards.weather import PendingWeather
from fno.cards.wiring import build_daily_card
from fno.config import ROOT, load_app_config
from fno.constants import BOOK2_HYBRID, BOOK3_AI
from fno.desk.pack_wiring import PACKED_BOOKS
from tests.desk.conftest import RecordingAlerts

from . import real_day as rd
from .replay import Replay


class NotBuilt(Exception):
    """No code and no interface exist yet: the story's builder replaces `not_built` with the real check."""


def not_built(story: str):
    raise NotBuilt(f"{story} is not built")


def missing(*stories: str):
    return pytest.mark.xfail(strict=True, reason=f"not built yet: {', '.join(stories)}")


def replayed_decisions(tmp_path, monkeypatch, book_name: str) -> list:
    Replay(tmp_path, monkeypatch, RecordingAlerts()).run()
    return sorted((tmp_path / "journal" / book_name / "decisions" / rd.DAY.isoformat()).glob("*/*.json"))


@missing("owner: daily.live_from dates (go-live gate)")
def test_every_o1_step_has_its_live_date():
    assert all(load_app_config()["daily"]["live_from"].values())


@missing("O1 follow-up: the 14:05 start")
def test_the_daily_routine_starts_before_the_1430_forecast_cutoff():
    section = (ROOT / "CLAUDE.md").read_text(encoding="utf-8").split("## Daily desk routine")[1].split("\n## ")[0]
    assert "14:33" not in section


@missing("T1c: the card reads M1's weather record")
def test_the_card_shows_m1s_weather_not_a_pending_line():
    assert not isinstance(build_daily_card(ROOT).builder.weather_source, PendingWeather)


@missing("O11 part 2: the card step on a git root")
def test_the_card_is_built_on_the_recorded_day():
    not_built("the replay's card step (T1 reads committed records from git HEAD; the replay root is no checkout)")


@missing("D4", "D5", "F1t")
def test_books_2_and_3_get_their_private_packs():
    assert {BOOK2_HYBRID, BOOK3_AI} <= set(PACKED_BOOKS)


@missing("F1t", "F5")
def test_book2_decides_on_the_recorded_day_from_a_fake_ai_answer(tmp_path, monkeypatch):
    assert replayed_decisions(tmp_path, monkeypatch, BOOK2_HYBRID)


@missing("F1t", "F6")
def test_book3_decides_on_the_recorded_day_from_a_fake_ai_answer(tmp_path, monkeypatch):
    assert replayed_decisions(tmp_path, monkeypatch, BOOK3_AI)


@missing("F5", "F6")
def test_books_2_and_3_fill_and_exit_in_the_daily_run():
    not_built("Book 2's and Book 3's OrderBuilder and ExitRules in E3's daily run (F5, F6)")


@missing("F1t")
def test_each_ai_decision_records_the_model_served_and_its_session():
    not_built("F1t's model reporting (model_served, session_id) in Books 2 and 3's decision records")


@missing("E8")
def test_paper_fills_follow_the_owners_reaction_time():
    assert constants.VERDICT_REACTION_MINUTES == 60 and "owner_timing" in load_app_config()["desk"]


@missing("G6")
def test_protocol_v4_is_frozen_so_the_days_v4_rows_are_scored():
    assert (ROOT / "research" / "forecasts" / "FREEZE_v4.md").is_file()


@missing("G11")
def test_the_ai_books_answer_the_v4_questions_on_the_recorded_day():
    not_built("G11")


@missing("O10")
def test_every_capture_failure_leaves_one_committed_error_row_and_an_alert():
    not_built("O10: one committed row per capture job and day, and an alert on a failure")


@missing("O10", "A14")
def test_a_scheduled_job_that_never_starts_is_alerted_as_stale():
    not_built("O10's staleness alert on a due job with no run (health-check, nse-margins' early cron, participant-OI)")


def test_the_day_has_a_price_distribution_and_valuation_record(tmp_path, monkeypatch):
    """G13 (closed): O1's `price_distribution` step writes the day's live NIFTY record from the recorded chain: two
    expiries valued with their implied distributions, every rule forecaster at every horizon, no problem."""
    out = Replay(tmp_path, monkeypatch, RecordingAlerts()).run()
    assert out.log.result("price_distribution")["status"] == constants.STEP_OK
    (path,) = [p for p in out.distribution_drive.files if p.endswith(f"nifty_{rd.DAY.isoformat()}.json")]
    record = json.loads(out.distribution_drive.files[path])
    assert (record["label"], record["status"], record["problems"]) == ("live", "ok", [])
    assert [e["distribution"]["status"] for e in record["valuation"]["expiries"]] == ["ok", "ok"]
    assert len(record["forecasts"]) == 12 and {r["status"] for r in record["forecasts"]} == {"ok"}


@missing("F2")
def test_an_analyst_finding_card_is_written_for_the_day():
    not_built("F2")


@missing("F8c")
def test_each_ai_book_routine_records_its_own_usage_minutes():
    not_built("F8c")


@missing("T3")
def test_a_trade_card_carries_the_devils_advocate_objections():
    not_built("T3")
