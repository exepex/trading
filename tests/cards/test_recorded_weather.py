"""Story T1c: the card's weather from M1's committed record (criteria 1-7). The base record is the repository's real
committed live record of 23 Oct 2026, varied per case; the back-fill of 14 Oct is the not-live case."""

import copy
import hashlib
import json
import re
from datetime import date

import pytest

from fno.cards.committed import GitHeadRecords
from fno.cards.recorded_weather import BLOCKS
from fno.cards.wiring import _weather
from fno.config import ROOT
from tests.cards.fakes import WEATHER, FakeRecords, weather_of

DAY, BACKFILL_DAY = date(2026, 10, 23), date(2026, 10, 14)
PATH = WEATHER.format(day=DAY)
REAL = json.loads((ROOT / PATH).read_text(encoding="utf-8"))
COLOURS = re.compile(r"\b(GREEN|AMBER|RED)\b")
PROOF = "not yet proven: G8 has not scored it against v0 and the base rate"
CHANCES = "Chance of a 2% NIFTY move: next session 2.9% (base rate 2.7%); within 5 sessions 12.9% (base rate 10.4%)"


def section(record=None, raw: bytes | None = None, day=DAY):
    data = raw if raw is not None else (json.dumps(record).encode() if record is not None else None)
    return weather_of(FakeRecords({} if data is None else {PATH: data})).weather(day)


def varied(**changes):
    record = copy.deepcopy(REAL)
    record.update(changes)
    return record


def test_a_live_green_record_shows_its_colour_chances_proof_and_v0_and_is_listed_by_sha256():
    shown = section(REAL)
    assert shown.lines == (f"Weather: GREEN (weather_vix_v1, {PROOF})", CHANCES, "Checklist v0: AMBER")
    data = json.dumps(REAL).encode()
    assert [(u.path, u.sha256) for u in shown.used] == [(PATH, hashlib.sha256(data).hexdigest())]
    assert shown.missing == ()


def test_only_red_adds_no_new_entries():
    assert section(varied(colour="AMBER")).lines[0].startswith("Weather: AMBER (")
    assert section(varied(colour="AMBER")).lines[-1] == "Checklist v0: AMBER"
    red = section(varied(colour="RED")).lines
    assert red[0].startswith("Weather: RED (") and red[-1] == "RED: no new entries (owner rule)."


def test_a_back_fill_record_is_never_today_s_weather_and_blocks_new_trades():
    """M1's builder, 23 Oct: only a `live` label counts for the day's card; the real back-fill of 14 Oct."""
    path = WEATHER.format(day=BACKFILL_DAY)
    shown = weather_of(FakeRecords({path: (ROOT / path).read_bytes()})).weather(BACKFILL_DAY)
    assert shown.lines == (f"Weather: no live reading for {BACKFILL_DAY} (the record is backfill_exploratory, not "
                           "today's weather)", BLOCKS)  # fmt: skip
    assert shown.missing == (f"live weather record for {BACKFILL_DAY}",)
    assert not COLOURS.search("\n".join(shown.lines))


@pytest.mark.parametrize("record, raw, day", [
    (None, None, DAY),  # no record committed
    (None, b"{not json", DAY),  # unreadable
    (None, b"[1, 2]", DAY),  # JSON, but not a record
    (REAL, None, date(2026, 10, 15)),  # the record found under the card's path names another day
])  # fmt: skip
def test_no_readable_record_for_the_day_says_no_reading_blocks_new_trades_and_shows_no_colour(record, raw, day):
    if day != DAY:  # plant the 14 Oct record at the 15 Oct path
        shown = weather_of(FakeRecords({WEATHER.format(day=day): json.dumps(record).encode()})).weather(day)
    else:
        shown = section(record, raw)
    assert shown.lines == (f"Weather: no reading for {day}", BLOCKS)
    assert shown.missing == (f"weather record for {day}",) and shown.used == ()


def test_a_not_scored_record_says_why_blocks_new_trades_and_shows_no_colour():
    record = varied(colour="not scored", status="not scored: weather_vix_v1 v6_abs_move_2pct_next_session not_started")
    shown = section(record)
    assert shown.lines == (f"Weather: not scored for {DAY} (weather_vix_v1 v6_abs_move_2pct_next_session "
                           "not_started)", BLOCKS)  # fmt: skip
    assert shown.missing == (f"weather not scored for {DAY}",) and len(shown.used) == 1


def test_a_missing_operative_chance_is_not_scored_never_zero_percent():
    """A guard: M1's `_status` never writes a scored record with a missing value."""
    record = copy.deepcopy(REAL)
    record["probabilities"]["weather_vix_v1"]["v6_abs_move_2pct_next_session"] = {
        "status": "not_started",
        "value": None,
    }
    shown = section(record)
    assert shown.lines == (f"Weather: not scored for {DAY} (a chance or base rate is missing)", BLOCKS)
    assert section(varied(probabilities={})).lines[1] == BLOCKS  # empty probabilities: the same


def test_chances_have_one_decimal_at_the_boundary():
    record = copy.deepcopy(REAL)
    record["probabilities"]["weather_vix_v1"]["v6_abs_move_2pct_next_session"]["value"] = 0.10
    assert section(record).lines[1].startswith("Chance of a 2% NIFTY move: next session 10.0% (base rate 2.7%)")


def test_an_unscored_v0_shows_its_reason_and_an_older_record_without_one_never_raises():
    """Judge 401: the back-fills of 13-14 Oct predate `v0_status`."""
    with_reason = varied(v0_colour="not scored", v0_status="not scored: rv10 missing")
    assert section(with_reason).lines[2] == "Checklist v0: not scored (rv10 missing)"
    older = varied(v0_colour="not scored")
    older.pop("v0_status", None)
    assert section(older).lines[2] == "Checklist v0: not scored (no reason recorded)"


def test_no_driver_value_reaches_the_card():
    text = "\n".join(section(REAL).lines)
    for name, value in REAL["drivers"]["v0_inputs"].items():
        assert name not in text and str(value["value"]) not in text
    assert "us_move" not in text and "private" not in text


def test_the_app_reads_the_real_committed_record_and_an_uncommitted_file_reads_as_no_reading(tmp_path):
    shown = _weather(GitHeadRecords(ROOT)).weather(DAY)
    assert shown.lines[0] == f"Weather: GREEN (weather_vix_v1, {PROOF})" and shown.used[0].path == PATH
    on_disk_only = GitHeadRecords(tmp_path)  # not a git checkout: nothing is committed
    assert _weather(on_disk_only).weather(DAY).lines[0] == f"Weather: no reading for {DAY}"


@pytest.mark.parametrize("colour", ["BLUE", None, ""])
def test_a_colour_m1_never_writes_is_not_scored_and_never_shown(colour):
    """Self-review: only GREEN, AMBER and RED are shown; anything else fails closed."""
    shown = section(varied(colour=colour))
    assert shown.lines == (f"Weather: not scored for {DAY} (colour {colour!r} is not GREEN, AMBER or RED)", BLOCKS)


def _with(change):
    record = copy.deepcopy(REAL)
    change(record)
    return record


@pytest.mark.parametrize("change", [
    lambda r: r.update(probabilities="not a mapping"),
    lambda r: r["probabilities"].update(weather_vix_v1=["a", "list"]),
    lambda r: r["probabilities"]["base_rate"].update(v6_abs_move_2pct_next_session="ok"),
    lambda r: r["probabilities"]["weather_vix_v1"]["v6_abs_move_2pct_next_session"].update(value="0.03"),
    lambda r: r["probabilities"]["weather_vix_v1"]["v6_abs_move_2pct_next_session"].update(value=True),
    lambda r: r["probabilities"]["weather_vix_v1"]["v6_abs_move_2pct_next_session"].update(value=float("nan")),
    lambda r: r["probabilities"]["weather_vix_v1"]["v6_abs_move_2pct_next_session"].update(value=1.5),
    lambda r: r["probabilities"]["weather_vix_v1"]["v6_abs_move_2pct_next_session"].update(value=-0.01),
])  # fmt: skip
def test_a_malformed_chance_fails_closed_and_never_raises(change):
    shown = section(_with(change))
    assert shown.lines == (f"Weather: not scored for {DAY} (a chance or base rate is missing)", BLOCKS)


def test_a_weather_source_that_raises_still_says_no_new_trades():
    """Self-review: the card's guard keeps the owner's line when the weather source fails."""
    from fno.cards.card import CardBuilder
    from fno.cards.sections import WeatherSource
    from tests.cards.fakes import daily_card

    class Broken(WeatherSource):
        def weather(self, day):
            raise KeyError("colour")

    records = FakeRecords()
    answer = daily_card(records, ROOT).sessions.answer(DAY)
    from fno.cards.forecasts import LiveCaptureForecasts
    from fno.cards.status import RegistryStatus

    card = CardBuilder(RegistryStatus(records, records), Broken(), LiveCaptureForecasts(records)).build(DAY, answer)
    assert card.sections[1].lines == ("weather: not available on this card", BLOCKS)
    assert "weather source failed (KeyError)" in card.missing


def test_a_record_not_marked_scored_is_never_shown_even_with_a_colour_and_full_chances():
    """Judge 555 minor: the `status` check alone holds this inconsistent record back."""
    shown = section(varied(status="not scored: hand-made inconsistent record"))
    assert shown.lines == (f"Weather: not scored for {DAY} (hand-made inconsistent record)", BLOCKS)


def test_a_chance_whose_entry_status_is_not_ok_is_never_shown_even_with_a_value():
    """Judge 555 minor: the entry's own `status` check alone holds this inconsistent record back."""
    shown = section(_with(lambda r: r["probabilities"]["base_rate"]["v6_abs_move_2pct_within_5_sessions"].update(
        status="not_started")))  # fmt: skip
    assert shown.lines == (f"Weather: not scored for {DAY} (a chance or base rate is missing)", BLOCKS)
