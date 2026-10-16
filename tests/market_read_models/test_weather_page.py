"""Story P2a (screen W3a): the `weather` page from M1's records. Criteria 1 (real source, every number re-read), 3 (in
test_contract_log_line.py) and 4 (never sent: no level, no `reaches`, no US cue). Criterion 2 does not apply: the
weather has no Drive-only input (its US cue is private and never read here)."""

import json
import math
from datetime import date, timedelta

import pytest

from fno.forecast_v4_rules.records import BACKFILL, LIVE
from fno.forecast_v4_rules.series import DayValue
from fno.market_read_models.blocks import SessionRows
from fno.market_read_models.publication import PublicationBuilder
from fno.market_read_models.weather_block import FnoWeatherBlock
from fno.market_read_models.weather_inputs import WeatherInputsReader
from fno.market_read_models.wiring import build_pinned_contract, build_weather_inputs
from fno.weather.checklist_v0 import AMBER_LIMITS, RED_LIMITS
from fno.weather.constants import WEATHER_AMBER_FLOORS, WEATHER_RED_FLOORS
from fno.weather.records import WeatherRecords

REAL_DAY = date(2026, 10, 14)
Q1, Q5 = "v6_abs_move_2pct_next_session", "v6_abs_move_2pct_within_5_sessions"
CONTRACT = build_pinned_contract()


def published(inputs) -> dict:
    """The stored payload, after the publication checked it against the pinned contract as stored and as served."""
    rows = SessionRows(inputs.day, [], [], [], [], weather=inputs)
    return PublicationBuilder([FnoWeatherBlock()], CONTRACT, "c" * 40).build(rows).records["weather"]["payload"]


def test_the_real_session_is_not_published_from_a_back_fill_record_and_every_number_is_the_records():
    inputs = build_weather_inputs().on(REAL_DAY)
    page, record = published(inputs), inputs.record
    assert record["label"] == BACKFILL and page["status"] == "not_published" and page["colour"] is None
    assert page["blocks_new_entries"] is True and page["missing_inputs"][0]["story"] == "M1"
    assert page["base_rate_1d"] == record["probabilities"]["base_rate"][Q1]["value"]
    assert page["base_rate_5d"] == record["probabilities"]["base_rate"][Q5]["value"]
    assert page["p_big_1d"] is None and page["drivers"] == [] and page["red_share"]["sessions"] == 0
    assert all(s["n_scored"] == 0 and s["status"] == "not_enough_data" for s in page["scores"])


def test_the_real_recent_strip_shows_no_back_fill_colour_and_the_closes_own_2pct_moves():
    from fno.forecast_v4_rules.series import closes_rows, regular_closes
    from fno.forecast_v4_rules.wiring import CLOSES_FILE

    closes = regular_closes(closes_rows(CLOSES_FILE.read_text()))
    by_day = {c.day: c.value for c in closes}
    days = [c.day for c in closes]
    page = published(build_weather_inputs().on(REAL_DAY))
    for item in page["recent"]:
        day = date.fromisoformat(item["session"])
        later = days[days.index(day) + 1] if day < REAL_DAY else None
        expected = abs(math.log(by_day[later] / by_day[day])) >= 0.02 if later else None
        assert item["colour"] is None and item["big_move"] == expected
    assert len(page["recent"]) == 10 and page["recent"][-1]["session"] == REAL_DAY.isoformat()


def record(day: date, label: str, colour: str, p1: float, p5: float, inputs: dict, events=()) -> dict:
    figures = {"weather_vix_v1": (p1, p5), "base_rate": (0.04, 0.12), "weather_checklist_v0": (0.05, 0.15)}
    return {
        "day": day.isoformat(), "label": label, "colour": colour, "operative": "weather_vix_v1", "status": "scored",
        "probabilities": {k: {Q1: {"status": "ok", "value": a}, Q5: {"status": "ok", "value": b}}
                          for k, (a, b) in figures.items()},
        "drivers": {"v0_inputs": {k: {"value": v, "reaches": "AMBER"} for k, v in inputs.items()},
                    "events_next_5_sessions": list(events), "us_move": "private"},
    }  # fmt: skip


def calm(i: int) -> dict:
    """Inputs that wobble a little each session: a typical change of 0.01 in each."""
    step = 0.01 * (i % 2)
    return {"vix_ratio": 1.0 + step, "vix_change5": 0.02 + step, "move5": 0.008 + step, "rv10": 0.12 + step}


@pytest.fixture
def live_world(tmp_path):
    """260 sessions: back-fill records, then 12 live ones (the last RED); a 3% NIFTY drop after the 255th session."""
    start = date(2025, 1, 1)
    days = [start + timedelta(days=i) for i in range(260)]
    closes, price = [], 100.0
    for i, d in enumerate(days):
        price *= 0.97 if i == 255 else 1.001
        closes.append(DayValue(d, price))
    store = WeatherRecords(tmp_path)
    for i, d in enumerate(days[:-1]):
        live = i >= len(days) - 13
        colour = "AMBER" if live and i % 3 == 0 else "GREEN"
        store.write(d, record(d, LIVE if live else BACKFILL, colour, 0.05, 0.14, calm(i)))
    today = days[-1]
    moved = {**calm(258), "vix_change5": 0.30, "move5": 0.0085}  # a big VIX jump; a small move5 change
    store.write(today, record(today, LIVE, "RED", 0.12, 0.42, moved, [{"type": "rbi_policy", "date": "2025-09-20"}]))
    return WeatherInputsReader(store, closes).on(today), days


def test_a_live_scored_record_is_published_with_its_figures_and_new_entries_blocked_when_red(live_world):
    inputs, _ = live_world
    page = published(inputs)
    assert page["status"] == "published" and page["colour"] == "RED" and page["blocks_new_entries"] is True
    assert (page["p_big_1d"], page["p_big_5d"], page["base_rate_1d"]) == (0.12, 0.42, 0.04)
    assert page["times_usual_1d"] == 3.0 and page["times_usual_5d"] == 3.5 and page["missing_inputs"] == []


def test_drivers_say_values_push_by_the_sign_of_the_change_and_rank_by_change_over_typical_change(live_world):
    inputs, _ = live_world
    page = published(inputs)
    drivers = page["drivers"]
    assert [d["driver"] for d in drivers][:2] == ["vix_change", "recent_big_moves"]  # 0.29 vs 0.0005, typical 0.01
    assert drivers[0] == {"driver": "vix_change", "text": "India VIX up 30% over 5 sessions", "push": "riskier"}
    assert drivers[-1] == {"driver": "scheduled_event", "text": "RBI policy decision on 2025-09-20", "push": "riskier"}


def test_recent_and_red_share_count_live_records_only_and_the_page_scores_nothing(live_world):
    inputs, _ = live_world
    page = published(inputs)
    colours = [r["colour"] for r in page["recent"]]
    assert colours[-1] == "RED" and None not in colours[-10:]  # the last 10 sessions are all live
    assert page["red_share"] == {"sessions": 13, "red_sessions": 1, "share": 1 / 13, "max_share": 0.15,
                                 "over_alarming": False}  # fmt: skip
    # 12 live days are resolved, yet the page scores nothing: the scores are G8's alone (judge 218)
    assert {(s["question"], s["baseline"]) for s in page["scores"]} == {
        (q, b) for q in ("V6_1d", "V6_5d") for b in ("base_rate", "v0_checklist")
    }
    assert all(
        (s["status"], s["n_scored"], s["brier"], s["brier_baseline"], s["skill"], s["verdict"])
        == ("not_enough_data", 0, None, None, None, "not_tested")
        for s in page["scores"]
    )


def test_a_back_fill_red_record_is_never_published(tmp_path):
    day = date(2025, 3, 3)
    store = WeatherRecords(tmp_path)
    store.write(day, record(day, BACKFILL, "RED", 0.2, 0.5, calm(0)))
    page = published(WeatherInputsReader(store, [DayValue(day, 100.0)]).on(day))
    assert page["status"] == "not_published" and page["colour"] is None and page["blocks_new_entries"] is True


def test_a_live_record_with_a_figure_missing_names_it_and_is_not_published(tmp_path):
    day = date(2025, 3, 3)
    broken = record(day, LIVE, "not scored", 0.2, 0.5, calm(0))
    broken["probabilities"]["base_rate"][Q5] = {"status": "not_eligible", "value": None}
    store = WeatherRecords(tmp_path)
    store.write(day, broken)
    page = published(WeatherInputsReader(store, [DayValue(day, 100.0)]).on(day))
    assert page["status"] == "not_published"
    assert page["missing_inputs"] == [
        {
            "input": "the usual chance of a 2% move over 750 sessions (V6_5d)",
            "story": "G7",
            "detail": "M1 recorded it as not_eligible for this session",
        }
    ]


def test_the_page_never_carries_a_level_a_reaches_colour_or_the_us_cue(live_world):
    inputs, _ = live_world
    text = json.dumps(published(inputs))
    assert "reaches" not in text and "us_move" not in text and "private" not in text
    levels = [*RED_LIMITS, *AMBER_LIMITS, *WEATHER_RED_FLOORS, *WEATHER_AMBER_FLOORS]
    shown = {f"{v:.2f}" for v in levels} | {f"{v:.0%}" for v in levels} | {f"{v:.1%}" for v in levels}
    for driver in published(inputs)["drivers"]:
        assert not any(level in driver["text"] for level in shown), driver["text"]
        assert not any(word in driver["text"].lower() for word in ("floor", "turns", "level", "threshold"))
