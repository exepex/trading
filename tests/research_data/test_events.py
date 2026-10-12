"""Events calendar (story A6): validated rows, and only scheduled, already-announced events are usable."""

from datetime import date

import pytest

from fno.research_data.events import COLUMNS, in_window, known_on, read_events

HEADER = ",".join(COLUMNS) + "\n"
SRC = "https://rbi.org.in/x"


def csv_rows(*rows):
    return HEADER + "".join(r + "\n" for r in rows)


SAMPLE = csv_rows(
    f"2024-06-07,rbi_policy,yes,2024-02-08,{SRC},,MPC June,{SRC}",
    f"2020-03-27,rbi_policy,no,,,,Off-cycle cut,{SRC}",
    "2024-06-04,election_result,yes,2024-03-16,https://eci.gov.in/x,,Counting day,https://eci.gov.in/y",
)


def test_only_scheduled_events_announced_by_the_decision_day_are_known():
    events = read_events(SAMPLE)
    assert [e.day for e in known_on(events, date(2024, 5, 1))] == [date(2024, 6, 4), date(2024, 6, 7)]
    assert known_on(events, date(2024, 2, 1)) == []  # neither was announced yet
    assert all(e.day != date(2020, 3, 27) for e in known_on(events, date(2025, 1, 1)))  # unscheduled: never usable


def test_window_is_after_entry_and_up_to_exit():
    events = read_events(SAMPLE)
    hits = in_window(events, date(2024, 5, 20), start=date(2024, 5, 21), end=date(2024, 6, 5))
    assert [e.day for e in hits] == [date(2024, 6, 4)]


@pytest.mark.parametrize(
    "row",
    [
        f"2024-06-07,rbi_meeting,yes,2024-02-08,{SRC},,x,{SRC}",  # unknown type
        f"2024-06-31,rbi_policy,yes,2024-02-08,{SRC},,x,{SRC}",  # bad date
        "2024-06-07,rbi_policy,yes,2024-02-08,https://rbi.org.in/x,,x,",  # missing source
        f"2024-06-07,rbi_policy,yes,,,,x,{SRC}",  # scheduled without announcement
        f"2024-06-07,rbi_policy,yes,2024-06-07,{SRC},,x,{SRC}",  # announced on the day itself
    ],
)
def test_bad_rows_are_refused(row):
    with pytest.raises(ValueError):
        read_events(csv_rows(row))


def test_an_upcoming_announced_meeting_needs_no_happened_source_but_a_past_one_does():
    upcoming = f"2026-12-04,rbi_policy,yes,2026-03-23,{SRC},,future meeting,"
    assert read_events(csv_rows(upcoming), today=date(2026, 10, 12))[0].day == date(2026, 12, 4)
    with pytest.raises(ValueError, match="official"):
        read_events(csv_rows(upcoming), today=date(2026, 12, 5))


def test_the_repository_calendar_is_valid_and_covers_the_known_dates():
    from pathlib import Path

    events = read_events((Path(__file__).resolve().parents[2] / "research/data/events/events.csv").read_text(),
                         today=date(2026, 10, 12))  # fmt: skip
    days = {(e.day, e.kind) for e in events}
    for must in [(date(2020, 2, 1), "budget"), (date(2025, 2, 1), "budget"), (date(2026, 2, 1), "budget"),
                 (date(2019, 5, 23), "election_result"), (date(2024, 6, 4), "election_result"),
                 (date(2020, 3, 27), "rbi_policy")]:  # fmt: skip
        assert must in days
    off_cycle = [e for e in events if e.kind == "rbi_policy" and not e.scheduled]
    assert {e.day for e in off_cycle} == {date(2020, 3, 27), date(2020, 5, 22), date(2022, 5, 4)}
    assert all(e not in known_on(events, date(2026, 10, 12)) for e in off_cycle)  # never usable ahead
    assert len(events) == 61


def repository_events():
    from pathlib import Path

    text = (Path(__file__).resolve().parents[2] / "research/data/events/events.csv").read_text()
    return read_events(text, today=date(2026, 10, 12))


@pytest.mark.parametrize(
    "decision_day, end, known_day",
    [
        (date(2022, 1, 10), date(2022, 2, 20), date(2022, 2, 9)),  # Feb 2022 MPC known since 2021-03-31 as Feb 9
        (date(2022, 2, 6), date(2022, 2, 20), date(2022, 2, 10)),  # the move to Feb 10 was announced on Feb 6
        (date(2022, 6, 25), date(2022, 8, 10), date(2022, 8, 4)),  # Aug 2022 MPC known as Aug 4 until Jul 21
        (date(2020, 9, 1), date(2020, 10, 15), date(2020, 10, 1)),  # Oct 2020 MPC known as Oct 1 until postponed
        (date(2020, 5, 1), date(2020, 6, 10), date(2020, 6, 5)),  # June 2020 MPC known until the May 22 emergency
    ],
)
def test_a_moved_event_is_known_at_the_date_known_on_the_decision_day(decision_day, end, known_day):
    """Judge 8, finding 1: a rescheduled meeting never vanishes from what was known before the move."""
    hits = in_window(repository_events(), decision_day, decision_day, end)
    assert [e.day for e in hits] == [known_day]


def test_a_postponed_meeting_is_unknown_between_postponement_and_new_dates():
    events = repository_events()
    assert in_window(events, date(2020, 9, 28), date(2020, 9, 28), date(2020, 10, 5)) == []  # postponed, no new date
    assert [e.day for e in in_window(events, date(2020, 10, 6), date(2020, 10, 6), date(2020, 10, 20))] == [
        date(2020, 10, 9)
    ]


def test_an_emergency_meeting_is_never_known_ahead_but_the_meeting_it_replaced_was():
    events = repository_events()
    assert all(e.day != date(2020, 5, 22) for e in known_on(events, date(2020, 5, 21)))
    assert [e.day for e in in_window(events, date(2020, 5, 22), date(2020, 5, 22), date(2020, 6, 10))] == []


@pytest.mark.parametrize(
    "row, message",
    [
        (f"2024-06-07,rbi_policy,yes,2024-02-08,{SRC},,x,https://example.com/x", "official"),
        (f"2024-06-07,rbi_policy,yes,2024-02-08,{SRC},,x,http://rbi.org.in/x", "official"),
        (f"2024-06-07,rbi_policy,yes,2024-02-08,{SRC},,x,{SRC},2024-01-01,{SRC}", "revised_from"),
        (f"2024-06-07,rbi_policy,yes,2024-02-08,{SRC},2024-06-06,x,{SRC},2024-03-01,{SRC}", "after the revision"),
        (f"2024-06-07,rbi_policy,yes,2024-02-08,{SRC},2024-06-06,x,{SRC},,,2024-02-01", "first_withdrawn_on"),
    ],
)
def test_bad_sources_and_bad_revision_rows_are_refused(row, message):
    with pytest.raises(ValueError, match=message):
        read_events(csv_rows(row), today=date(2026, 10, 12))
