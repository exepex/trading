"""Story A17b, criterion 2: the US stock-market calendar's expected date on holidays, closures and both US clocks,
checked against the dates-only list of US trading days, and the US 10-year's missing weekdays never treated as
sessions. The list, the us10y table and its gaps are in Drive since O9b: those two tests are `data` tests on the
verified cache (`python -m fno data-cache sync data/global-cues`)."""

import csv
from datetime import date, time, timedelta

import pytest

from fno.global_cues import wiring
from fno.global_cues.as_of import DECISION, OPEN
from fno.global_cues.check_files import CHECK_FILES, GAPS_FILE, CueChecks
from fno.global_cues.cue_calendars import NyseCalendar, WeekdayCalendar
from fno.global_cues.drive_wiring import CHECK, TABLE, TRADING_DATES
from fno.global_cues.reading import BEHIND, STALE, expected_date, reading_for
from fno.global_cues.treasury_source import TreasuryTenYearSource
from fno.global_cues.us_index_sources import CboeSp500Source
from fno.storage.receipted_rows import ReceiptedRowLog, ReceiptedSnapshots
from fno.storage.report_files import CsvReportFile, csv_reports
from tests.data_cache import cached_series

NYSE = NyseCalendar(wiring.us_market_closures())
SP500 = CboeSp500Source()


def expected(day: date, cutoff=OPEN) -> date:
    return expected_date(day, cutoff, SP500, NYSE)


def test_a_us_monday_holiday_good_friday_and_thanksgiving_week():
    assert expected(date(2026, 1, 20)) == date(2026, 1, 16)  # Martin Luther King Jr. Day, 19 Jan
    assert expected(date(2026, 4, 6)) == date(2026, 4, 2)  # Good Friday, 3 Apr
    assert expected(date(2026, 11, 26)) == date(2026, 11, 25)
    assert expected(date(2026, 11, 27)) == date(2026, 11, 25)  # Thanksgiving, 26 Nov
    assert expected(date(2026, 11, 28)) == date(2026, 11, 27)  # the half day counts


def test_juneteenth_from_2022_and_weekend_observed_holidays():
    assert NYSE.is_session(date(2021, 6, 18))  # 19 Jun 2021 a Saturday, before NYSE closed for it
    assert not NYSE.is_session(date(2022, 6, 20)) and not NYSE.is_session(date(2023, 6, 19))
    assert not NYSE.is_session(date(2026, 7, 3))  # 4 Jul 2026 a Saturday
    assert not NYSE.is_session(date(2022, 12, 26))  # Christmas 2022 a Sunday
    assert NYSE.is_session(date(2021, 12, 31))  # New Year 2022 a Saturday: no Friday closure
    assert date(2021, 12, 31) not in NYSE.holidays(2022) and date(2023, 1, 2) in NYSE.holidays(2023)  # Sunday: Monday
    assert expected(date(2026, 7, 6)) == date(2026, 7, 2)


def test_each_listed_closure_is_closed_and_has_an_https_source():
    with open(wiring.CLOSURES_FILE, encoding="utf-8") as f:
        closures = list(csv.DictReader(f))
    assert [r["date"] for r in closures] == ["2007-01-02", "2012-10-29", "2012-10-30", "2018-12-05", "2025-01-09"]
    for row in closures:
        assert row["source_url"].startswith("https://") and row["reason"], row["date"]
        assert not NYSE.is_session(date.fromisoformat(row["date"]))
    assert expected(date(2025, 1, 10)) == date(2025, 1, 8)
    assert expected(date(2018, 12, 6)) == date(2018, 12, 4)


def test_us_summer_and_winter_time_at_both_cutoffs():
    for day in (date(2026, 7, 15), date(2026, 1, 15)):  # US summer time (EDT), US winter time (EST)
        assert expected(day, OPEN) == expected(day, DECISION) == day - timedelta(days=1)
    summer_close, winter_close = time(1, 45), time(2, 45)  # IST: 16:00 EDT is 01:30, 16:00 EST is 02:30
    assert expected(date(2026, 7, 15), summer_close) == date(2026, 7, 14)
    assert expected(date(2026, 1, 15), summer_close) == date(2026, 1, 13)  # 02:30 not yet reached
    assert expected(date(2026, 1, 15), winter_close) == date(2026, 1, 14)


def trading_dates() -> list[dict[str, str]]:
    return cached_series(ReceiptedSnapshots, TRADING_DATES).latest()


@pytest.mark.data
def test_the_calendar_matches_every_committed_sp500_trading_date_since_2007():
    listed = trading_dates()
    sp500 = {date.fromisoformat(r["date"]) for r in listed if r["in_sp500"] == "1"}
    day, last, mismatches = date(2007, 1, 1), max(sp500), []
    while day <= last:
        if day.weekday() < 5 and NYSE.is_session(day) != (day in sp500):
            mismatches.append(f"{day}: calendar {'session' if NYSE.is_session(day) else 'closed'}")
        day += timedelta(days=1)
    assert mismatches == []
    assert len(sp500) > 4900  # the list covers the whole table, not a sample
    nasdaq_only = [r["date"] for r in listed if r["in_sp500"] == "0"]
    assert nasdaq_only and not any(NYSE.is_session(date.fromisoformat(d)) for d in nasdaq_only)


@pytest.mark.data
def test_every_missing_us10y_weekday_is_a_listed_gap_and_never_read_as_a_session():
    rows = cached_series(ReceiptedRowLog, TABLE.format(cue="us10y")).rows()
    listed = cached_series(ReceiptedSnapshots, CHECK.format(stem=GAPS_FILE.rsplit(".", 1)[0])).latest()
    gaps = {r["date"] for r in listed if r["cue"] == "us10y" and r["kind"] == "weekday_without_value"}
    held = {r["value_date"] for r in rows}
    first, last = date.fromisoformat(rows[0]["value_date"]), date.fromisoformat(rows[-1]["value_date"])
    missing = [d for d in (first + timedelta(n) for n in range((last - first).days)) if d.weekday() < 5]
    missing = [d for d in missing if d.isoformat() not in held]
    assert missing and {d.isoformat() for d in missing} == gaps
    source, weekdays = TreasuryTenYearSource(), WeekdayCalendar()
    for day in missing:
        reading = reading_for(rows, day + timedelta(days=1), OPEN, False, source, weekdays)
        assert reading.expected == day and reading.status in (BEHIND, STALE), day


class Table:
    def __init__(self, *days):
        self.held = [{"value_date": d, "value": "1.0"} for d in days]

    def rows(self):
        return self.held


def test_check_writes_the_dates_of_both_us_tables_and_nothing_without_them(tmp_path):
    out = tmp_path / "us_trading_dates.csv"
    tables = {"sp500": Table("2026-01-16", "2026-01-20"), "nasdaq100": Table("2026-01-16", "2026-01-19")}
    lines = CueChecks(tables, csv_reports(tmp_path / "checks", CHECK_FILES), trading_dates=CsvReportFile(out)).write()
    assert out.read_text() == (
        "date,in_sp500,in_nasdaq100\n2026-01-16,1,1\n2026-01-19,0,1\n2026-01-20,1,0\n"
    )  # dates and flags only, never a value
    assert lines[0] == "US trading dates: 2 S&P 500 dates, 1 Nasdaq-only dates listed"
    other = tmp_path / "other.csv"
    CueChecks({"sp500": tables["sp500"]}, csv_reports(tmp_path / "checks", CHECK_FILES),
              trading_dates=CsvReportFile(other)).write()  # fmt: skip
    assert not other.exists()  # without both US tables the list is left alone


def test_expected_date_turns_over_strictly_after_the_close_is_out():
    summer_out, winter_out = time(1, 30), time(2, 30)  # IST: 16:00 EDT and 16:00 EST on the US day before
    assert expected(date(2026, 7, 15), summer_out) == date(2026, 7, 13)  # at the moment itself: not yet out
    assert expected(date(2026, 7, 15), time(1, 30, 1)) == date(2026, 7, 14)
    assert expected(date(2026, 1, 15), winter_out) == date(2026, 1, 13)
    assert expected(date(2026, 1, 15), time(2, 30, 1)) == date(2026, 1, 14)
    assert expected(date(2026, 3, 9), time(1, 31)) == date(2026, 3, 6)  # US clocks change 8 Mar: Friday was EST
    assert expected(date(2026, 3, 10), time(1, 31)) == date(2026, 3, 9)  # Monday 9 Mar closes in EDT
