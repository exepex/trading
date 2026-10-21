"""Story G11 round 2b, step 3 (response 272): the v4 firer fires each book once with its whole input in the pointer,
only on today's date and from the v4 go-live date, nothing without a released pack, and logs every not_fired with
its reason (the stop rule as a flag); the questions are the book's own registered slot's."""

import json
from datetime import date, datetime, time

import pytest

from fno.ai.run_terms import V4_TERMS
from fno.ai.v4_book_inputs import V4BookInputs
from fno.ai.v4_fire import V4BookFirer
from fno.ai.v4_pointer import parse_v4_pointer
from fno.constants import (
    BOOK2_HYBRID,
    BOOK3_AI,
    V1_RV_1S,
    V4_BASELINE_BASE_RATE,
    V4_SLOT_AI,
    V4_SLOT_HYBRID,
    V4_SLOT_RULES,
    V6_BIG_MOVE_1S,
    V6_BIG_MOVE_5S,
)
from fno.forecast_scoring.v4.inputs import ForecastFiles
from fno.forecast_scoring.v4.records import Registration, SlotRegistry
from fno.forecast_v4_rules import records
from fno.models import IST
from fno.v4_pack.release import NotReleased, ReleaseRecord
from fno.weather.constants import WEATHER_MODEL_VIX
from tests.ai.test_v4_input import DAY, a_pack
from tests.pipeline.fakes import FakeTrigger, RecordingAlerts

PACK_SHA = "d" * 64
QUESTIONS = [V6_BIG_MOVE_1S, V6_BIG_MOVE_5S]


def at(hh, mm, ss=0, day=DAY):
    return datetime.combine(day, time(hh, mm, ss), IST)


class Released:
    def __init__(self, missing=""):
        self.missing = missing

    def release(self, day):
        if self.missing:
            raise NotReleased(self.missing)
        return ReleaseRecord(day, "A", f"v4/packs/{day.year}/{day}.json", PACK_SHA, at(14, 31))

    def pack(self, release):
        return a_pack()


class Ledger(SlotRegistry):
    def __init__(self, extra=()):
        self.extra = extra

    def registered(self):
        slots = {(q, s): Registration(f, DAY) for q in QUESTIONS
                 for s, f in ((V4_SLOT_RULES, WEATHER_MODEL_VIX), (V4_SLOT_HYBRID, "book2_hybrid_v2"),
                              (V4_SLOT_AI, "book3_ai_v2"))}  # fmt: skip
        return slots | {key: Registration("book3_ai_v2", DAY) for key in self.extra}


def write_rules(v4):
    """The day's live rules-slot (the weather) and base-rate rows for V6a, committed before 14:30; V6b has none."""
    audit = dict(label=records.LIVE, kind="rule", slot="rules", method_sha256="b" * 64, inputs_sha256="c" * 64,
                 made_at="2026-10-26T08:50:00+00:00")  # fmt: skip
    for name, value in ((WEATHER_MODEL_VIX, 0.06), (V4_BASELINE_BASE_RATE, 0.04)):
        records.write(v4, name, V6_BIG_MOVE_1S, [records.record(DAY, V6_BIG_MOVE_1S, "ok", value, **audit)])
    return v4


class Desk:
    def __init__(self, root, ledger=None, released=None, live_from=DAY, now=None):
        self.root, self.alerts = root, RecordingAlerts()
        self.triggers = {BOOK2_HYBRID: FakeTrigger(BOOK2_HYBRID), BOOK3_AI: FakeTrigger(BOOK3_AI)}
        v4 = write_rules(root / "research/forecasts/v4")
        inputs = V4BookInputs(root, ledger or Ledger(), ForecastFiles(v4))
        packs = released or Released()
        self.firer = V4BookFirer(root, self.triggers, lambda: packs, inputs, self.alerts,
                                 lambda: now or at(14, 33), live_from)  # fmt: skip

    def log(self):
        return json.loads((self.root / V4_TERMS.fired_path(DAY)).read_text())


def test_both_books_are_fired_once_with_their_whole_input_in_the_pointer(tmp_path):
    desk = Desk(tmp_path)
    assert desk.firer.fire(DAY)[-1].endswith("fired book2_hybrid, book3_ai of book2_hybrid, book3_ai")
    hybrid = parse_v4_pointer(desk.triggers[BOOK2_HYBRID].fired[0].to_text())
    assert hybrid.input["rules"]["by_question"][V6_BIG_MOVE_1S] == {
        WEATHER_MODEL_VIX: 0.06,
        V4_BASELINE_BASE_RATE: 0.04,
    }
    assert "rules" not in parse_v4_pointer(desk.triggers[BOOK3_AI].fired[0].to_text()).input
    entry = desk.log()["books"][BOOK3_AI]
    assert (entry["fired"], entry["questions"], entry["pack_sha256"], entry["stop_rule"]) == (
        True,
        QUESTIONS,
        PACK_SHA,
        False,
    )
    assert entry["input_sha256"] == parse_v4_pointer(desk.triggers[BOOK3_AI].fired[0].to_text()).input_sha256
    assert "already fired" in desk.firer.fire(DAY)[-1] and len(desk.triggers[BOOK3_AI].fired) == 1


@pytest.mark.parametrize(
    ("live_from", "now", "why"),
    [(DAY, at(14, 33, day=date(2026, 10, 27)), "is not today"), (None, None, "no v4 go-live date"),
     (date(2026, 10, 27), None, "not live before 2026-10-27")],
)  # fmt: skip
def test_a_day_that_is_not_today_or_not_live_fires_nothing_and_logs_nothing(tmp_path, live_from, now, why):
    desk = Desk(tmp_path, live_from=live_from, now=now)
    assert why in desk.firer.fire(DAY)[-1]
    assert not (tmp_path / V4_TERMS.fired_path(DAY)).exists() and not desk.triggers[BOOK3_AI].fired


def test_no_released_pack_fires_nothing_and_says_why(tmp_path):
    desk = Desk(tmp_path, released=Released("2026-10-26: system_late, no pack was released"))
    assert "nothing fired: 2026-10-26: system_late" in desk.firer.fire(DAY)[-1]
    assert desk.log() == {"released": False, "reason": "2026-10-26: system_late, no pack was released"}


def test_a_start_after_1455_is_a_logged_not_fired_with_an_alert(tmp_path):
    desk = Desk(tmp_path, now=at(14, 56))
    desk.firer.fire(DAY)
    entry = desk.log()["books"][BOOK2_HYBRID]
    assert (entry["fired"], entry["late_start"]) == (False, True) and len(desk.alerts.lines) == 2


def test_the_stop_rule_is_logged_as_its_flag(tmp_path, monkeypatch):
    monkeypatch.setattr("fno.ai.v4_fire.stop_reason", lambda root, book, version, day: "stopped: 2 breaches")
    desk = Desk(tmp_path)
    desk.firer.fire(DAY)
    assert desk.log()["books"][BOOK3_AI]["stop_rule"] is True and not desk.triggers[BOOK3_AI].fired


def test_a_refused_trigger_is_not_fired_and_never_retried(tmp_path):
    desk = Desk(tmp_path)
    desk.triggers[BOOK3_AI] = FakeTrigger(BOOK3_AI, failure="HTTP 500 from the routine API")
    desk.firer.fire(DAY)
    entry = desk.log()["books"][BOOK3_AI]
    assert (entry["fired"], entry["reason"]) == (False, "HTTP 500 from the routine API")


def test_a_registered_question_the_prompt_does_not_define_is_refused_loudly(tmp_path):
    desk = Desk(tmp_path, ledger=Ledger(extra=[(V1_RV_1S, V4_SLOT_AI)]))
    desk.firer.fire(DAY)
    assert "does not define" in desk.log()["books"][BOOK3_AI]["reason"] and desk.triggers[BOOK2_HYBRID].fired


def test_a_slot_with_no_registered_question_is_not_fired(tmp_path):
    class Empty(SlotRegistry):
        def registered(self):
            return {}

    desk = Desk(tmp_path, ledger=Empty())
    desk.firer.fire(DAY)
    assert desk.log()["books"][BOOK3_AI]["reason"] == "no v4 question is registered for its slot yet"


def test_the_v2_ai_fire_stops_from_the_v4_go_live_date(tmp_path):
    """Owner's choice A: one run cannot serve both, so from v4's date the books fire for v4 only."""
    from fno.ai.fire import AiBookFirer

    firer = AiBookFirer(tmp_path, {}, RecordingAlerts(), lambda: at(15, 10), v4_live_from=DAY)
    assert "v2 AI fire stopped" in firer.fire(DAY)[-1]
    assert (
        "no v2 pack"
        in AiBookFirer(tmp_path, {}, RecordingAlerts(), lambda: at(15, 10), DAY).fire(date(2026, 10, 23))[-1]
    )


def test_the_wiring_refuses_a_day_without_needing_drive():
    from fno.ai.wiring import build_v4_firer

    assert "is not today" in build_v4_firer({}).fire(date(2026, 10, 1))[-1]  # no Drive settings in this env


def test_the_fire_log_is_in_the_folder_v4_fire_yml_commits():
    """v4-fire.yml commits `research/forecasts/ai_v4` after the fire (judge 282): the path is pinned here."""
    assert V4_TERMS.fired_path(DAY) == "research/forecasts/ai_v4/2026/2026-10-26_fired.json"
    assert V4_TERMS.audit_path(DAY, BOOK3_AI).startswith("research/forecasts/ai_v4/")  # collect's commit covers it


def test_the_ai_books_go_live_on_their_own_key_never_forecasts_v4s_date():
    """Orchestrator, 21 Oct: O1's rule forecasts going live must not fire the books (their v4 steps are not built), so
    an accidental merge does nothing; the repository's config keeps the books' key null until step 7 and round 2c."""
    from fno.ai.wiring import v4_live_from
    from fno.config import load_app_config

    assert v4_live_from({"daily": {"live_from": {"forecasts_v4": "2026-10-22"}}}) is None
    assert v4_live_from({"daily": {"live_from": {"ai_books_v4": "2026-11-02"}}}) == date(2026, 11, 2)
    assert v4_live_from(load_app_config()) is None
