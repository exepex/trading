"""G13 criteria 6-7 and 13: the day record. Point in time (a close on or after the day is never read; the
recorder asks for the day's chain only, test_recorder); the record check refuses bad rows; the AI slots are accepted
ids; an index gets a valuation and no forecasts; a chain without a spot gives missing forecasts with their reason."""

import math
from datetime import date, timedelta

import pytest

from fno.constants import BOOK2_HYBRID, BOOK3_AI
from fno.forecast_v4_rules.series import DayValue
from fno.price_distribution.build import DayBuilder
from fno.price_distribution.constants import AI_SLOTS, FORECASTERS, HORIZONS, MISSING, OK, RULE_FORECASTERS
from fno.price_distribution.records import RecordRefused, check_row, encode
from fno.research_data.calendar import CsvSessionCalendar
from tests.price_distribution.builders import DAY, RATE, chain_day

CALENDAR = CsvSessionCalendar(
    "date,kind,description,source_url\n2026-12-25,holiday,Christmas,https://example.invalid\n"
)


def history(last: date, n: int = 800):
    return [DayValue(last - timedelta(days=n - i), 22_000 * math.exp(0.01 * math.sin(i))) for i in range(n)]


def builder(closes):
    return DayBuilder(CALENDAR, RATE, closes, "c0" * 32)


def test_a_nifty_record_has_every_rule_forecaster_at_every_horizon_and_no_ai_rows():
    record = builder(history(DAY)).build(chain_day(), "backfill_3pm", None)
    pairs = {(r["forecaster"], r["horizon"]) for r in record["forecasts"]}
    assert pairs == {(f, h) for f in RULE_FORECASTERS for h in HORIZONS}
    assert record["status"] == OK and not record["problems"]
    assert AI_SLOTS == (BOOK2_HYBRID, BOOK3_AI) and set(AI_SLOTS) <= set(FORECASTERS)


def test_no_close_on_or_after_the_day_is_read():
    closes = history(DAY)
    planted = [*closes, DayValue(DAY, 99_999.0), DayValue(DAY + timedelta(days=3), 1.0)]
    clean, dirty = (builder(c).build(chain_day(), "backfill_3pm", None) for c in (closes, planted))
    assert encode(clean) == encode(dirty)


def test_an_index_gets_a_valuation_and_no_forecasts():
    record = builder(history(DAY)).build(chain_day(underlying="BANKNIFTY"), "backfill_3pm", None)
    assert record["forecasts"] == [] and record["valuation"]["expiries"] and record["valuation"]["rv20_points"] is None


def test_a_chain_without_a_spot_gives_missing_forecasts_and_names_the_problem():
    record = builder(history(DAY)).build(chain_day(spot=None), "backfill_3pm", None)
    assert {r["status"] for r in record["forecasts"]} == {MISSING}
    assert record["status"] == "problems" and all("no spot" in p for p in record["problems"])


def row(**changes):
    base = {"forecaster": "implied", "horizon": "h1", "label": "live", "status": OK, "reason": None}
    base |= {f"lq{n:02d}": v for n, v in zip((5, 10, 25, 50, 75, 90, 95), range(7), strict=True)}
    return base | changes


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"lq50": 2}, "strictly increasing"),  # a tie with lq25
        ({"lq50": 1}, "strictly increasing"),  # a fall
        ({"lq95": None}, "strictly increasing"),
        ({"status": MISSING, "reason": None}, "needs its reason"),
        ({"forecaster": "someone"}, "unknown forecaster"),
        ({"label": "made_up"}, "unknown forecaster"),
        ({"status": "maybe"}, "unknown status"),
    ],
)
def test_the_record_check_refuses_bad_rows(changes, message):
    with pytest.raises(RecordRefused, match=message):
        check_row(row(**changes))


def test_the_record_check_accepts_good_rows_and_the_ai_slot_ids():
    check_row(row())
    check_row(row(forecaster=BOOK2_HYBRID, status=MISSING, reason="not answered"))


def test_stale_closes_make_the_close_based_forecasters_missing_with_their_reason():
    closes = [c for c in history(DAY) if c.day < DAY - timedelta(days=3)]  # the last three days' closes never landed
    record = builder(closes).build(chain_day(), "backfill_3pm", None)
    by = {(r["forecaster"], r["horizon"]): r for r in record["forecasts"]}
    assert {by[("rv20", h)]["status"] for h in HORIZONS} == {MISSING}
    assert by[("hist750", "h1")]["reason"].startswith("closes stale: the last close before the day is 2026-10-12")
    assert {by[("implied", h)]["status"] for h in HORIZONS} == {OK}  # the chain alone needs no closes
    assert record["status"] == "problems"


def test_closes_up_to_the_previous_session_are_fresh_across_a_weekend():
    monday = date(2026, 10, 19)
    record = builder(history(date(2026, 10, 17))).build(chain_day(day=monday), "backfill_3pm", None)  # last: Fri 16th
    assert {r["status"] for r in record["forecasts"] if r["forecaster"] == "rv20"} <= {OK, "not_eligible"}


def test_not_started_is_accepted_for_the_ai_slots_only():
    check_row(row(forecaster=BOOK3_AI, status="not_started", reason="the AI books do not answer yet"))
    with pytest.raises(RecordRefused, match="AI books' slots only"):
        check_row(row(status="not_started", reason="x"))
