"""Story A17b, criterion 1: a reading gives the row, its age, the expected date and a status, decided in the order
none, current, ahead, behind, stale. All values are made up (fake), never real ones."""

from datetime import date, timedelta

from fno.global_cues.as_of import DECISION, OPEN
from fno.global_cues.cue_calendars import NseSessionCalendar, NyseCalendar, WeekdayCalendar
from fno.global_cues.other_sources import EiaBrentSource, RbiUsdInrSource
from fno.global_cues.reading import AHEAD, BEHIND, CURRENT, NONE, STALE, CueReader, reading_for
from fno.global_cues.treasury_source import TreasuryTenYearSource
from fno.global_cues.us_index_sources import CboeSp500Source, NasdaqNdxSource
from fno.global_cues.wiring import us_market_closures
from fno.research_data.calendar import CsvSessionCalendar

NYSE = NyseCalendar(us_market_closures())
SOURCE = "https://nsearchives.nseindia.com/content/circulars/example.pdf"
NSE = CsvSessionCalendar(f"date,kind,description,source_url\n2026-10-02,holiday,example holiday,{SOURCE}\n")
SEEN_LATE = "2026-12-31T00:00:00+05:30"


def rows(*days: str, seen: str = SEEN_LATE) -> list[dict[str, str]]:
    return [{"value_date": d, "value": "1.0", "first_seen_at": seen} for d in days]


def weekdays(start: date, end: date) -> list[str]:
    days = (start + timedelta(n) for n in range((end - start).days + 1))
    return [d.isoformat() for d in days if d.weekday() < 5]


def test_nasdaq_lacking_the_previous_close_reads_behind():
    reading = reading_for(rows("2026-10-12", "2026-10-13"), date(2026, 10, 15), OPEN, False, NasdaqNdxSource(), NYSE)
    assert (reading.status, reading.expected, reading.age_days) == (BEHIND, date(2026, 10, 14), 2)
    assert reading.row["value_date"] == "2026-10-13"


def test_six_weeks_old_reads_stale_and_the_expected_date_skips_thanksgiving():
    reading = reading_for(rows("2026-10-14"), date(2026, 11, 27), OPEN, False, CboeSp500Source(), NYSE)
    assert (reading.status, reading.expected, reading.age_days) == (STALE, date(2026, 11, 25), 44)


def test_after_hurricane_sandy_the_last_close_is_current_although_five_days_old():
    reading = reading_for(rows("2012-10-25", "2012-10-26"), date(2012, 10, 31), OPEN, False, CboeSp500Source(), NYSE)
    assert (reading.status, reading.expected, reading.age_days) == (CURRENT, date(2012, 10, 26), 5)


def test_rbi_on_an_nse_holiday_reads_ahead():
    calendar = NseSessionCalendar(NSE, NSE.first)
    reading = reading_for(rows("2026-10-01", "2026-10-02"), date(2026, 10, 3), OPEN, False, RbiUsdInrSource(), calendar)
    assert (reading.status, reading.expected) == (AHEAD, date(2026, 10, 1))
    same_day = reading_for(rows("2026-10-01"), date(2026, 10, 1), DECISION, False, RbiUsdInrSource(), calendar)
    assert (same_day.status, same_day.expected) == (CURRENT, date(2026, 10, 1))  # published 13:30, read at 15:00


def test_us10y_on_good_friday_is_current_on_monday_and_never_ahead():
    days = rows("2023-04-06", "2023-04-07")
    reading = reading_for(days, date(2023, 4, 10), OPEN, False, TreasuryTenYearSource(), WeekdayCalendar())
    assert (reading.status, reading.expected) == (CURRENT, date(2023, 4, 7))
    for day in weekdays(date(2023, 1, 2), date(2023, 12, 29)):
        later = date.fromisoformat(day) + timedelta(days=1)
        status = reading_for(rows(day), later, OPEN, False, TreasuryTenYearSource(), WeekdayCalendar()).status
        assert status != AHEAD, day


def test_an_age_at_the_limit_is_behind_and_one_day_more_is_stale():
    sp500 = CboeSp500Source()
    assert sp500.max_age_days == 4
    at_limit = reading_for(rows("2026-10-09"), date(2026, 10, 13), OPEN, False, sp500, NYSE)
    assert (at_limit.status, at_limit.age_days, at_limit.expected) == (BEHIND, 4, date(2026, 10, 12))
    over = reading_for(rows("2026-10-09"), date(2026, 10, 14), OPEN, False, sp500, NYSE)
    assert (over.status, over.age_days) == (STALE, 5)


def test_brent_without_a_calendar_reads_only_behind_stale_or_none():
    brent = EiaBrentSource()
    statuses = {
        reading_for(rows("2026-09-28"), date(2026, 9, 28) + timedelta(days=age), OPEN, False, brent, None).status
        for age in range(11, 40)
    }
    assert statuses == {BEHIND, STALE}
    edge = reading_for(rows("2026-09-28"), date(2026, 10, 14), OPEN, False, brent, None)
    assert (edge.status, edge.age_days, edge.expected) == (BEHIND, 16, None)
    assert reading_for(rows("2026-09-28"), date(2026, 10, 15), OPEN, False, brent, None).status == STALE
    assert reading_for(rows("2026-10-14"), date(2026, 10, 15), OPEN, False, brent, None).status == NONE  # not final


def test_no_rows_reads_none_with_the_expected_date():
    reading = reading_for([], date(2026, 10, 15), OPEN, False, CboeSp500Source(), NYSE)
    assert (reading.row, reading.status, reading.age_days, reading.expected) == (None, NONE, None, date(2026, 10, 14))


def test_nasdaqs_holiday_row_is_skipped_so_the_next_day_never_reads_ahead():
    days = rows("2026-01-15", "2026-01-16", "2026-01-19")  # 19 Jan: Martin Luther King Jr. Day, a repeated close
    reading = reading_for(days, date(2026, 1, 20), OPEN, False, NasdaqNdxSource(), NYSE)
    assert (reading.status, reading.row["value_date"]) == (CURRENT, "2026-01-16")
    sp500 = reading_for(days, date(2026, 1, 20), OPEN, False, CboeSp500Source(), NYSE)
    assert sp500.status == AHEAD  # a source without holiday rows keeps such a row, flagged


def test_live_only_reads_what_was_seen_before_the_cutoff():
    early = rows("2026-10-14", seen="2026-10-15T06:00:00+05:30")
    late = rows("2026-10-14", seen="2026-10-15T10:00:00+05:30")
    assert reading_for(early, date(2026, 10, 15), OPEN, True, CboeSp500Source(), NYSE).status == CURRENT
    assert reading_for(late, date(2026, 10, 15), OPEN, True, CboeSp500Source(), NYSE).status == NONE


class Table:
    def __init__(self, held):
        self.held = held

    def rows(self):
        return self.held


def test_the_reader_reads_a_cue_through_its_own_source_and_calendar():
    reader = CueReader({"sp500": Table(rows("2026-10-14"))}, {"sp500": CboeSp500Source()}, {"sp500": NYSE})
    reading = reader.read("sp500", date(2026, 10, 15), OPEN, False)
    assert (reading.status, reading.expected) == (CURRENT, date(2026, 10, 14))


def test_a_muhurat_day_is_no_usdinr_session_so_its_rate_reads_ahead():
    calendar = CsvSessionCalendar(f"date,kind,description,source_url\n2024-11-01,muhurat,Diwali muhurat,{SOURCE}\n")
    nse = NseSessionCalendar(calendar, calendar.first)
    reading = reading_for(rows("2024-11-01"), date(2024, 11, 4), OPEN, False, RbiUsdInrSource(), nse)
    assert (reading.status, reading.expected) == (AHEAD, date(2024, 10, 31))
    assert nse.is_session(date(2016, 3, 7)) and not nse.is_session(date(2016, 3, 6))  # before 2024: weekdays


def test_a_row_dated_after_the_india_date_is_never_usable():
    future = rows("2026-10-14", "2026-10-20", seen="2026-10-14T08:00:00+05:30")
    reading = reading_for(future, date(2026, 10, 15), OPEN, True, CboeSp500Source(), NYSE)
    assert (reading.row["value_date"], reading.age_days) == ("2026-10-14", 1)
