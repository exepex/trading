"""F3 (story B1 criteria 5 and 6): only events known on the decision day, read through story A6's functions."""

import ast
import inspect
from datetime import date

import pytest
from feature_fixtures import context, data, make_panel, session_days

from fno.composition import load_research_data
from fno.research_data.events import Event
from fno.research_engine import event_features
from fno.research_engine.event_features import ScheduledEventInWindow

F3 = ScheduledEventInWindow()
EMPTY = make_panel(session_days(1), [20000.0])
MEETING = date(2025, 2, 7)


def f3(events, decision_day, entry, exit_day):
    return F3.value(data(EMPTY, events), decision_day, context(entry, exit_day))


def test_f3_sees_a_scheduled_event_after_entry_and_up_to_exit():
    known = [Event(MEETING, "rbi_policy", True, date(2024, 3, 27), "MPC")]
    assert f3(known, date(2025, 1, 20), date(2025, 1, 21), date(2025, 2, 7)) is True  # exit day included
    assert f3(known, date(2025, 2, 6), date(2025, 2, 7), date(2025, 2, 20)) is False  # on the entry day: excluded
    assert f3(known, date(2025, 1, 20), date(2025, 1, 21), date(2025, 2, 6)) is False


def test_f3_ignores_an_event_announced_after_the_decision_day():
    late = [Event(MEETING, "rbi_policy", True, date(2025, 1, 25), "MPC announced late")]
    assert f3(late, date(2025, 1, 20), date(2025, 1, 21), date(2025, 2, 10)) is False
    assert f3(late, date(2025, 1, 25), date(2025, 1, 27), date(2025, 2, 10)) is True  # known from its announcement


def test_f3_ignores_an_unscheduled_event():
    emergency = [Event(MEETING, "rbi_policy", False, None, "off-cycle")]
    assert f3(emergency, date(2025, 2, 10), date(2025, 1, 21), date(2025, 2, 10)) is False


@pytest.fixture(scope="module")
def repository_events():
    return load_research_data(years=()).events


def test_f3_ignores_the_unscheduled_22_may_2020_rbi_decision(repository_events):
    """The off-cycle MPC of 22 May 2020 (it replaced the 5 Jun meeting) is never usable ahead."""
    assert f3(repository_events, date(2020, 5, 15), date(2020, 5, 18), date(2020, 5, 29)) is False
    assert f3(repository_events, date(2020, 5, 25), date(2020, 5, 18), date(2020, 5, 29)) is False


def test_f3_sees_a_moved_meeting_at_the_date_known_on_the_decision_day(repository_events):
    """Feb 2022 MPC: known as 9 Feb from 31 Mar 2021, moved to 10 Feb on 6 Feb 2022. Deciding on 10 Jan 2022, a
    window ending 9 Feb holds it; one ending 8 Feb does not; after the move a window ending 9 Feb no longer does."""
    assert f3(repository_events, date(2022, 1, 10), date(2022, 1, 11), date(2022, 2, 9)) is True
    assert f3(repository_events, date(2022, 1, 10), date(2022, 1, 11), date(2022, 2, 8)) is False
    assert f3(repository_events, date(2022, 2, 7), date(2022, 2, 8), date(2022, 2, 9)) is False
    assert f3(repository_events, date(2022, 2, 7), date(2022, 2, 8), date(2022, 2, 10)) is True


def test_f3_reads_events_only_through_story_a6s_in_window():
    """Criterion 6: no own filter on event fields; the window comes from `fno.research_data.events.in_window`."""
    tree = ast.parse(inspect.getsource(event_features))
    attributes = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    assert not attributes & {"day", "announced_on", "scheduled", "revised_from", "first_announced_on"}
    calls = {n.func.id for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    assert "in_window" in calls


def test_the_composition_root_wires_f1_to_black76_on_the_future_and_the_configured_rate():
    from fno.composition import build_features
    from fno.research_engine.implied_vol import Black76

    f1, f2, f3 = build_features({"risk_free_rate": 0.065})
    assert [f.name for f in (f1, f2, f3)] == [
        "F1_atm_iv_minus_rv20",
        "F2_vix_above_250d_median",
        "F3_scheduled_event_in_window",
    ]
    assert isinstance(f1.model, Black76) and f1.rate == 0.065 and isinstance(f3, ScheduledEventInWindow)
