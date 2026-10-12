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
    with pytest.raises(ValueError, match="missing source"):
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
