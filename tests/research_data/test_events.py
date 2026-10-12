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
