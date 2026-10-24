"""Story A17f criteria 1 and 2: TWSE's closures calendar. Rows are keyed by date and kind (a year's `covers` row
beside a 1 Jan holiday); a malformed row is refused at load; an uncovered year is a failure and a missing next year
from 1 Dec an `incomplete` warning that one `covers` row stops; the committed file equals the parser's reading of
TWSE's own holiday file for every year it covers (the fixture is that file, byte for byte: public dates only)."""

import csv
import hashlib
from datetime import date
from pathlib import Path

import pytest

from fno.global_cues.market_closures import HOLIDAY, MarketClosures, load_closures, twse_closures
from fno.global_cues.preopen_calendar import ClosureCalendar
from fno.global_cues.preopen_outcome import FAILURE, INCOMPLETE, Problem
from fno.global_cues.wiring import TWSE_CLOSURES_FILE

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "twse"
TWSE_2026 = FIXTURES / "holiday_schedule_2026.json"
CLOSED_2026 = [
    *("2026-01-01", "2026-02-12", "2026-02-13", "2026-02-16", "2026-02-17", "2026-02-18", "2026-02-19", "2026-02-20"),
    *("2026-02-27", "2026-04-03", "2026-04-06", "2026-05-01", "2026-06-19", "2026-09-25", "2026-09-28", "2026-10-09"),
    *("2026-10-26", "2026-12-25"),
]


def rows(*items):
    return [dict(zip(("date", "kind", "description"), item, strict=True)) for item in items]


COVERS_2026 = ("2026-01-01", "covers", "TWSE 2026")


def calendar(*items):
    return ClosureCalendar("TWSE", lambda: MarketClosures(rows(COVERS_2026, *items), "test.csv"))


def test_the_committed_calendar_lists_monday_26_oct_and_the_23_oct_typhoon():
    closures = load_closures(TWSE_CLOSURES_FILE, "twse_closures.csv")
    assert closures.closure(date(2026, 10, 26)).kind == HOLIDAY
    assert closures.closure(date(2026, 10, 23)).kind == "unscheduled"
    assert closures.closure(date(2026, 10, 27)) is None and closures.closure(date(2026, 10, 22)) is None


def test_a_covers_row_and_a_holiday_on_1_jan_live_side_by_side_but_a_day_twice_is_refused():
    closures = MarketClosures(rows(COVERS_2026, ("2026-01-01", "holiday", "New Year")), "t.csv")
    assert closures.covers(2026) and closures.closure(date(2026, 1, 1)).description == "New Year"
    twice = rows(COVERS_2026, ("2026-01-01", "holiday", "a"), ("2026-01-01", "unscheduled", "b"))
    with pytest.raises(ValueError, match="row 4 lists 2026-01-01 twice"):
        MarketClosures(twice, "t.csv")


@pytest.mark.parametrize(
    ("bad", "message"),
    [
        (("2026-10-26", "closed", "x"), "row 3 has an unknown kind 'closed'"),
        (("2026-13-01", "holiday", "x"), "row 3 has no valid date"),
        (("", "holiday", "x"), "row 3 has no valid date"),
        (("2027-01-01", "holiday", "x"), "row 3 is a closure in 2027, which has no covers row"),
        (("2026-01-01", "covers", "again"), "row 3 is not the only covers row of 2026 on 1 Jan"),
        (("2027-10-01", "covers", "late"), "row 3 is not the only covers row of 2027 on 1 Jan"),
    ],
)
def test_a_malformed_row_is_refused_at_load_naming_the_row(bad, message):
    with pytest.raises(ValueError, match=message):
        MarketClosures(rows(COVERS_2026, bad), "t.csv")


def test_a_weekend_row_is_ignored_and_a_weekday_without_a_row_is_open():
    closures = MarketClosures(rows(COVERS_2026, ("2026-10-24", "holiday", "a Saturday")), "t.csv")
    assert closures.closure(date(2026, 10, 24)) is None and closures.closure(date(2026, 10, 27)) is None


def test_a_listed_day_is_closed_with_no_problem():
    verdict = calendar(("2026-10-26", "holiday", "Retrocession Day")).verdict("taiex", date(2026, 10, 26))
    assert verdict.closure.day == date(2026, 10, 26) and verdict.problems == () and verdict.lines == ()
    assert verdict.closed_line("taiex", "TWSE") == "taiex: market closed (TWSE holiday: Retrocession Day)"


def test_an_uncovered_year_is_a_failure_and_lists_nothing():
    verdict = calendar(("2026-10-26", "holiday", "x")).verdict("taiex", date(2027, 1, 4))
    assert verdict.closure is None and verdict.problems == (Problem("taiex: TWSE calendar has no 2027", FAILURE),)
    assert verdict.lines == ("taiex: TWSE calendar has no 2027",)


def test_from_1_dec_a_missing_next_year_warns_and_one_covers_row_stops_it():
    assert calendar().verdict("taiex", date(2026, 11, 30)).problems == ()
    warned = calendar().verdict("taiex", date(2026, 12, 1))
    assert warned.problems == (Problem("taiex: TWSE calendar has no 2027 yet", INCOMPLETE),)
    assert calendar(("2027-01-01", "covers", "TWSE 2027")).verdict("taiex", date(2026, 12, 1)).problems == ()


def test_a_calendar_that_cannot_be_loaded_is_a_failure_of_that_index_only(tmp_path):
    missing = ClosureCalendar("TWSE", lambda: load_closures(tmp_path / "none.csv", "none.csv"))
    verdict = missing.verdict("taiex", date(2026, 10, 26))
    assert verdict.closure is None and verdict.problems == (Problem("taiex: calendar refused (FileNotFoundError)"),)
    broken = calendar(("2026-10-26", "shut", "x")).verdict("taiex", date(2026, 10, 26))
    assert broken.problems == (Problem("taiex: calendar refused (ValueError)"),) and "unknown kind" in broken.lines[0]


def test_twses_2026_file_gives_the_18_weekday_closures():
    found = twse_closures(TWSE_2026.read_bytes())
    assert [day.isoformat() for day, _ in found] == CLOSED_2026


def test_trading_day_rows_and_weekends_are_not_closures_but_settlement_only_days_are():
    found = {day for day, _ in twse_closures(TWSE_2026.read_bytes())}
    assert not found & {date(2026, 1, 2), date(2026, 2, 11), date(2026, 2, 23)}  # "交易日": trading days
    assert not found & {date(2026, 2, 28), date(2026, 4, 4), date(2026, 4, 5), date(2026, 10, 25)}  # weekends
    assert {date(2026, 2, 12), date(2026, 2, 13)} <= found  # no trading, settlement only


@pytest.mark.parametrize(
    "data",
    [b"[]", b'[{"Name": "x"}]', b'[{"Date": "1151026"}]', b'[{"Date": "2026-10-26", "Name": "x"}]', b"<html>", b"{}"],
)
def test_a_changed_or_empty_twse_file_is_refused(data):
    with pytest.raises(ValueError):
        twse_closures(data)


def test_the_committed_calendar_equals_twses_file_for_every_year_it_covers():
    with open(TWSE_CLOSURES_FILE, encoding="utf-8") as f:
        committed = list(csv.DictReader(f))
    covers = [row for row in committed if row["kind"] == "covers"]
    assert covers, "the calendar covers no year"
    for row in covers:
        year = date.fromisoformat(row["date"]).year
        data = (FIXTURES / f"holiday_schedule_{year}.json").read_bytes()
        assert hashlib.sha256(data).hexdigest() == row["sha256"], f"{year}: the fixture is not the file cited"
        listed = sorted(r["date"] for r in committed if r["kind"] == HOLIDAY and r["date"].startswith(str(year)))
        assert listed == [day.isoformat() for day, _ in twse_closures(data)]
