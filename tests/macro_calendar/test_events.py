"""A20c criterion 12: `announced_on` is the IST day of the first snapshot holding a date; a date first seen on or
after its day is not an announcement; a future date a later snapshot drops is withdrawn and A6's `known_on` knows it
only until then; a past date the calendar stops covering stands; a date that comes back is a new announcement; A6's
types and `events.csv` are untouched."""

from datetime import date

from fno.research_data.events import TYPES, in_window, known_on
from fno.research_data.macro_events import MACRO_TYPES, macro_events


def row(day, seen_at, kind="india_cpi", source="mospi", period=("2026-04-01", "2027-03-31")):
    return {"kind": kind, "date": day, "planned": day, "source": source, "source_url": "u", "seen_at": seen_at,
            "period_start": period[0], "period_end": period[1]}  # fmt: skip


def test_announced_on_is_the_ist_day_of_the_first_snapshot():
    rows = [row("2026-11-12", "2026-10-16T20:00:00+00:00"), row("2026-11-12", "2026-10-18T02:00:00+00:00")]
    [event] = macro_events(rows)  # 20:00 UTC on 16 Oct is 01:30 IST on 17 Oct
    assert (event.day, event.kind, event.scheduled, event.announced_on) == (
        date(2026, 11, 12), "india_cpi", True, date(2026, 10, 17),
    )  # fmt: skip
    assert known_on([event], date(2026, 10, 16)) == [] and known_on([event], date(2026, 10, 17)) == [event]


def test_a_date_first_seen_on_or_after_its_day_is_not_an_announcement():
    assert macro_events([row("2026-10-12", "2026-10-16T02:00:00+00:00")]) == []  # past date in the first calendar
    assert macro_events([row("2026-10-16", "2026-10-16T02:00:00+00:00")]) == []  # the day itself


def test_a_dropped_future_date_is_withdrawn_and_known_only_until_then():
    rows = [
        row("2026-12-12", "2026-10-16T02:00:00+00:00"), row("2027-01-12", "2026-10-16T02:00:00+00:00"),
        row("2027-01-12", "2026-11-02T02:00:00+00:00"),  # 12 Dec no longer listed on 2 Nov
    ]  # fmt: skip
    events = macro_events(rows)
    withdrawn = next(e for e in events if e.day == date(2026, 12, 12))
    assert not withdrawn.scheduled and withdrawn.first_withdrawn_on == date(2026, 11, 2)
    assert "WITHDRAWN 2026-11-02" in withdrawn.description
    assert [e.day for e in known_on(events, date(2026, 11, 1))] == [date(2026, 12, 12), date(2027, 1, 12)]
    assert [e.day for e in known_on(events, date(2026, 11, 2))] == [date(2027, 1, 12)]
    assert in_window(events, date(2026, 11, 1), date(2026, 12, 1), date(2026, 12, 31))[0].day == date(2026, 12, 12)


def test_a_past_date_the_calendar_stops_listing_stands():
    rows = [row("2026-10-20", "2026-10-16T02:00:00+00:00"), row("2027-01-12", "2026-11-02T02:00:00+00:00")]
    [past, new] = macro_events(rows)  # 20 Oct, already past, is no longer listed on 2 Nov
    assert past.scheduled and past.announced_on == date(2026, 10, 16) and new.announced_on == date(2026, 11, 2)


def test_the_next_financial_year_s_calendar_does_not_withdraw_the_old_year_s_last_dates():
    next_year = ("2027-04-01", "2028-03-31")
    rows = [row("2027-03-28", "2027-02-01T02:00:00+00:00", kind="india_iip"),
            row("2027-04-28", "2027-03-10T02:00:00+00:00", kind="india_iip", period=next_year)]  # fmt: skip
    events = macro_events(rows)
    assert [(e.day, e.scheduled) for e in events] == [(date(2027, 3, 28), True), (date(2027, 4, 28), True)]
    assert [e.day for e in known_on(events, date(2027, 3, 20))] == [date(2027, 3, 28), date(2027, 4, 28)]


def test_an_older_calendar_served_again_withdraws_nothing_outside_its_year():
    rows = [row("2026-11-12", "2026-10-16T02:00:00+00:00"),
            row("2025-11-12", "2026-10-17T02:00:00+00:00", period=("2025-04-01", "2026-03-31"))]  # fmt: skip
    assert all(e.scheduled for e in macro_events(rows))


def test_a_date_that_comes_back_is_a_new_announcement():
    rows = [
        row("2026-12-12", "2026-10-16T02:00:00+00:00"), row("2027-01-12", "2026-10-20T02:00:00+00:00"),
        row("2026-12-12", "2026-10-25T02:00:00+00:00"),
    ]  # fmt: skip
    dec = [e for e in macro_events(rows) if e.day == date(2026, 12, 12)]
    assert [(e.scheduled, e.announced_on, e.first_withdrawn_on) for e in dec] == [
        (False, None, date(2026, 10, 20)), (True, date(2026, 10, 25), None),
    ]  # fmt: skip


def test_sources_are_separate_snapshots():
    rows = [row("2026-12-12", "2026-10-16T02:00:00+00:00"),
            row("2026-12-09", "2026-10-17T02:00:00+00:00", kind="us_fomc", source="fed")]  # fmt: skip
    assert [(e.kind, e.scheduled) for e in macro_events(rows)] == [("us_fomc", True), ("india_cpi", True)]


def test_a6_types_and_events_csv_are_untouched():
    assert not set(MACRO_TYPES) & set(TYPES) and TYPES == ("rbi_policy", "budget", "election_result")
