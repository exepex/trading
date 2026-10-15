"""R2 rules, timing and events (PROTOCOL.md sections 4 and 8, amendment 1 sections A, C, D1-D2, D5)."""

from collections import Counter
from datetime import date, datetime

import pytest
from r2_synthetic import weekdays
from r2study import events as ev
from r2study.events import Filings, Meeting, build_events, one_per_reschedule
from r2study.rules import clusters_a_year, clusters_a_year_needed, units_needed, window_years
from r2study.sessions import Sessions, choose_expiry, filed_before_entry_close, reaction_session

QUARTER = date(2024, 9, 30)
S = Sessions(weekdays(date(2024, 10, 1), date(2025, 1, 31)))


def test_registered_count_is_130_and_80_percent_power_needs_297():
    assert units_needed(1.645, 0, 0.60, 0.05) == 390
    assert clusters_a_year_needed(0) == 130
    assert units_needed(1.645, 0.842, 0.60, 0.05) == 891
    assert clusters_a_year_needed(0.842) == 297


def test_annualisation_divides_by_the_window_length_in_years_both_ends_included():
    assert window_years(date(2025, 1, 1), date(2025, 12, 31)) == pytest.approx(365 / 365.25)
    assert clusters_a_year(130, date(2024, 10, 1), date(2025, 9, 30)) == pytest.approx(130 * 365.25 / 365)
    assert clusters_a_year(0, date(2024, 10, 1), date(2026, 10, 14)) == 0


@pytest.mark.parametrize(
    ("moment", "expected"),
    [
        (datetime(2024, 10, 15, 9, 15), date(2024, 10, 15)),  # at the open: that session
        (datetime(2024, 10, 15, 15, 30), date(2024, 10, 15)),  # at the close: that session
        (datetime(2024, 10, 15, 15, 31), date(2024, 10, 16)),  # just after: the next session
        (datetime(2024, 10, 15, 9, 14), date(2024, 10, 15)),  # before the open: the first session from that day
        (datetime(2024, 10, 19, 11, 0), date(2024, 10, 21)),  # a Saturday: the next session
    ],
)
def test_reaction_session_follows_the_filing_time(moment, expected):
    assert reaction_session(S, moment.date(), moment) == expected


def test_no_filing_time_takes_the_first_session_after_the_results_day():
    assert reaction_session(S, date(2024, 10, 15), None) == date(2024, 10, 16)


def test_filing_at_or_before_the_entry_close_is_flagged_and_after_it_is_not():
    entry = date(2024, 10, 14)
    assert filed_before_entry_close(datetime(2024, 10, 14, 15, 30), entry)
    assert not filed_before_entry_close(datetime(2024, 10, 14, 15, 31), entry)
    assert not filed_before_entry_close(None, entry)


def test_expiry_needs_five_sessions_after_r_and_reports_a_push():
    listed = [date(2024, 10, 31), date(2024, 11, 28)]
    # R on 24 Oct: 25, 28, 29, 30, 31 Oct are 5 sessions after it -> October expiry, no push
    assert choose_expiry(S, listed, date(2024, 10, 24)) == (date(2024, 10, 31), False)
    # R on 25 Oct: only 4 -> November, pushed
    assert choose_expiry(S, listed, date(2024, 10, 25)) == (date(2024, 11, 28), True)
    assert choose_expiry(S, [], date(2024, 10, 25)) == (None, False)
    assert choose_expiry(S, [date(2024, 10, 31)], date(2024, 10, 30)) == (None, True)


def meeting(symbol, day, text="Financial Results"):
    return Meeting(symbol, day, text)


def test_reschedules_fewer_than_30_days_apart_are_one_event_keeping_the_filed_one():
    first, moved, next_quarter = date(2024, 10, 10), date(2024, 11, 8), date(2025, 1, 20)
    kept, dropped = one_per_reschedule(
        [meeting("A", first), meeting("A", moved), meeting("A", next_quarter)], lambda m: m.day == first
    )
    assert [m.day for m in kept] == [first, next_quarter] and dropped == 1
    kept, _ = one_per_reschedule([meeting("A", first), meeting("A", moved)], lambda m: False)
    assert [m.day for m in kept] == [moved]  # no filing: the later one
    thirty = [meeting("A", date(2024, 10, 1)), meeting("A", date(2024, 10, 31))]
    assert one_per_reschedule(thirty, lambda m: False) == (thirty, 0)  # exactly 30 days apart: two events
    assert one_per_reschedule([], lambda m: False) == ([], 0)


def fo_everything(symbol, day):
    return True


def test_events_take_the_entry_before_d_and_r_from_the_filing():
    filings = Filings({"A": [(datetime(2024, 10, 15, 16, 5), QUARTER)]})
    events, counts = build_events([meeting("A", date(2024, 10, 15))], filings, S, fo_everything)
    (event,) = events
    assert (event.entry, event.results_day, event.reaction) == (
        date(2024, 10, 14),
        date(2024, 10, 15),
        date(2024, 10, 16),
    )
    assert counts == Counter()


def test_events_left_out_are_counted_by_reason():
    meetings = [
        meeting("BOARD", date(2024, 10, 15), "Fund raising"),  # not a results meeting: ignored, not counted
        meeting("EARLY", date(2024, 10, 15)),  # filed on the entry session before the close
        meeting("NOTFO", date(2024, 10, 15)),
        meeting("FIRST", date(2024, 10, 1)),  # no session before it in the list
        meeting("LAST", date(2025, 1, 31)),  # no session after it
    ]
    filings = Filings({"EARLY": [(datetime(2024, 10, 14, 12, 0), QUARTER)]})
    events, counts = build_events(meetings, filings, S, lambda symbol, day: symbol != "NOTFO")
    assert events == []
    assert counts == Counter({ev.FILED_BEFORE_ENTRY: 1, ev.NOT_FO: 1, ev.NO_ENTRY: 1, ev.NO_REACTION: 1})


def test_a_filing_later_than_d_plus_3_days_is_not_matched():
    filings = Filings({"A": [(datetime(2024, 10, 19, 10, 0), QUARTER)]})
    (event,), _ = build_events([meeting("A", date(2024, 10, 15))], filings, S, fo_everything)
    assert event.filed_at is None and event.reaction == date(2024, 10, 16)
    filings = Filings({"A": [(datetime(2024, 10, 18, 10, 0), QUARTER)]})
    (event,), _ = build_events([meeting("A", date(2024, 10, 15))], filings, S, fo_everything)
    assert event.reaction == date(2024, 10, 18)


def test_results_purpose_is_matched_in_any_case_in_purpose_or_description():
    assert ev.is_results_meeting(meeting("A", date(2024, 10, 1), "Board | to consider FINANCIAL RESULTS"))
    assert not ev.is_results_meeting(meeting("A", date(2024, 10, 1), "Dividend | "))


def test_a_filing_for_a_period_older_than_120_days_before_d_is_not_this_events():
    old = Filings({"A": [(datetime(2024, 10, 15, 17, 0), date(2024, 6, 16))]})  # 121 days before D
    (event,), _ = build_events([meeting("A", date(2024, 10, 15))], old, S, fo_everything)
    assert event.filed_at is None
    edge = Filings({"A": [(datetime(2024, 10, 15, 17, 0), date(2024, 6, 17))]})  # exactly 120 days: counts
    (event,), _ = build_events([meeting("A", date(2024, 10, 15))], edge, S, fo_everything)
    assert event.filed_at == datetime(2024, 10, 15, 17, 0)


def test_sessions_after_the_archive_are_counted_from_the_calendar_for_the_expiry_rule():
    archive = Sessions(
        weekdays(date(2026, 10, 1), date(2026, 10, 14)), weekdays(date(2026, 10, 15), date(2026, 11, 30))
    )
    assert archive.last == date(2026, 10, 14) and date(2026, 10, 15) not in archive
    assert choose_expiry(archive, [date(2026, 10, 27)], date(2026, 10, 13)) == (date(2026, 10, 27), False)
    bare = Sessions(weekdays(date(2026, 10, 1), date(2026, 10, 14)))
    assert choose_expiry(bare, [date(2026, 10, 27)], date(2026, 10, 13)) == (None, True)


def test_a_market_hours_filing_on_a_muhurat_day_is_after_hours():
    days = weekdays(date(2024, 10, 28), date(2024, 11, 8)) + [date(2024, 11, 3)]  # a Sunday muhurat session
    sessions = Sessions(days, irregular=[date(2024, 11, 3)])
    assert reaction_session(sessions, date(2024, 11, 3), datetime(2024, 11, 3, 11, 0)) == date(2024, 11, 4)
    assert reaction_session(sessions, date(2024, 11, 4), datetime(2024, 11, 4, 11, 0)) == date(2024, 11, 4)
