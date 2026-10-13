"""Story B1 criteria 1 and 4: no feature moves when data after its cutoff changes; the harness catches leaks."""

from datetime import date, datetime, time, timedelta
from random import Random

import pytest
from lookahead_harness import assert_no_lookahead
from real_cycles import decision_days, real_context

from fno.composition import build_features
from fno.config import load_app_config
from fno.research_engine.features import Feature
from fno.research_engine.volatility_features import VixAboveMedian

LIVE_CUTOFF = time(15, 0)
SEED = 20261013


def twenty_random_days(real_data):
    days = decision_days(real_data, date(2025, 1, 15), date(2026, 9, 10))
    return sorted(Random(SEED).sample(days, 20))


def test_every_feature_is_unchanged_by_data_after_its_cutoff_on_20_random_days(real_data):
    days, features = twenty_random_days(real_data), build_features(load_app_config())
    values = {f.name: [] for f in features}
    for day in days:
        for feature in features:
            context = real_context(real_data, day)
            values[feature.name].append(assert_no_lookahead(feature, real_data, day, context, trials=1))
    f1, f2, f3 = values.values()
    # the test must exercise real values, not compare None with None
    assert all(v is not None for v in f1) and all(v is not None for v in f2)
    assert {True, False} <= set(f2) and set(f3) == {False}  # see the next test for F3 days that are true


@pytest.mark.parametrize("day", [date(2025, 7, 14), date(2025, 9, 22), date(2025, 11, 24)])
def test_f3_is_unchanged_on_days_with_a_known_meeting_in_the_window(real_data, day):
    """The random days above all give F3 false (41 of 202 decision days in 2025-26 have a meeting in the window)."""
    f3 = build_features(load_app_config())[2]
    assert assert_no_lookahead(f3, real_data, day, real_context(real_data, day)) is True


class _LiveVersion(Feature):
    """A feature declared as a 15:00 live feature (story B7), wrapping another feature's computation."""

    def __init__(self, inner: Feature):
        self.inner, self.name = inner, f"live {inner.name}"

    def known_at(self, decision_day):
        return datetime.combine(decision_day, LIVE_CUTOFF)

    def value(self, data, decision_day, context):
        return self.inner.value(data, decision_day, context)


class _PreviousCloseAboveFirst(Feature):
    """A correct live feature: uses only closes of sessions before the decision day."""

    name = "previous close above the first close"

    def known_at(self, decision_day):
        return datetime.combine(decision_day, LIVE_CUTOFF)

    def value(self, data, decision_day, context):
        before = [s for s in data.panel.sessions if s.day < decision_day]
        return before[-1].underlying > before[0].underlying


class _NextClose(Feature):
    """A leaking daily feature: reads the next session's close."""

    name = "next close"

    def value(self, data, decision_day, context):
        return next(s.underlying for s in data.panel.sessions if s.day > decision_day)


class _EventsIgnoringAnnouncement(Feature):
    """A leaking F3: counts every event dated in the window, whenever it was announced."""

    name = "events by date only"

    def value(self, data, decision_day, context):
        return any(context.entry_day < e.day <= context.exit_day for e in data.events)


class _LateDeclaredLeakyF1(Feature):
    """F1 plus the next session's close, declaring itself known a week after the decision day."""

    name = "leaky F1 known a week later"

    def __init__(self, f1):
        self.f1 = f1

    def known_at(self, decision_day):
        return datetime.combine(decision_day + timedelta(days=7), time(15, 30))

    def value(self, data, decision_day, context):
        later = next(s.underlying for s in data.panel.sessions if s.day > decision_day)
        return self.f1.value(data, decision_day, context) + later


DAY = date(2025, 6, 16)  # a decision day: the 31 Jul 2025 monthly expiry is 45 days away


@pytest.mark.parametrize("leaky", [_NextClose(), _EventsIgnoringAnnouncement()], ids=lambda f: f.name)
def test_the_harness_catches_a_feature_that_reads_data_after_the_decision_day(real_data, leaky):
    with pytest.raises(AssertionError, match="look-ahead"):
        assert_no_lookahead(leaky, real_data, DAY, real_context(real_data, DAY))


def test_a_feature_cannot_hide_a_leak_behind_a_later_known_at(real_data):
    """Judge 26 minor: the cutoff is never later than the decision day's close, whatever the feature declares."""
    leaky = _LateDeclaredLeakyF1(build_features(load_app_config())[0])
    with pytest.raises(AssertionError, match="look-ahead"):
        assert_no_lookahead(leaky, real_data, DAY, real_context(real_data, DAY))


def test_a_live_cutoff_changes_the_decision_days_own_closing_data(real_data):
    """Criterion 4: with a 15:00 cutoff the same day's closes (15:30) are changed too, so a live version that reads
    them fails, and the daily-close features cannot pass as live versions."""
    for day in twenty_random_days(real_data)[:5]:
        context = real_context(real_data, day)
        with pytest.raises(AssertionError, match="look-ahead"):
            assert_no_lookahead(_LiveVersion(VixAboveMedian()), real_data, day, context)
        assert assert_no_lookahead(_PreviousCloseAboveFirst(), real_data, day, context) in (True, False)


def test_the_harness_refuses_to_pass_when_nothing_follows_the_cutoff(real_data):
    last = real_data.panel.sessions[-1].day
    with pytest.raises(AssertionError, match="prove nothing"):
        assert_no_lookahead(VixAboveMedian(), real_data, last, real_context(real_data, date(2026, 9, 1)))
