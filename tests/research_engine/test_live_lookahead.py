"""Story B7 criterion 1: the look-ahead harness passes for every live feature with the 15:00 cutoff (it changes the
decision day's own closes, every later session, events not yet announced and every snapshot finished after 15:00)."""

from datetime import time

import pytest
from live_fixtures import CUTOFF, DAY, DAYS, RATE, live_context, live_data, snapshot
from lookahead_harness import LIVE_PERTURBERS, assert_no_lookahead

from fno.research_engine.live_features import (
    LiveAtmIvMinusRealised,
    LiveFeature,
    LiveScheduledEventInWindow,
    LiveVixAboveMedian,
)

LIVE = (LiveAtmIvMinusRealised(CUTOFF, RATE), LiveVixAboveMedian(CUTOFF), LiveScheduledEventInWindow(CUTOFF))


@pytest.mark.parametrize("day", DAYS[255:259])
@pytest.mark.parametrize("feature", LIVE, ids=lambda f: f.name)
def test_every_live_feature_is_unchanged_by_data_after_15_00(feature, day):
    value = assert_no_lookahead(feature, live_data(), day, live_context(day), perturbers=LIVE_PERTURBERS)
    assert value is not None  # a real value, not None compared with None


def test_a_late_same_day_snapshot_is_changed_and_ignored():
    data = live_data({**live_data().snapshots, DAY: snapshot(DAY, finished=time(15, 5))})
    assert assert_no_lookahead(LIVE[0], data, DAY, live_context(), perturbers=LIVE_PERTURBERS) is None


class _IgnoresCaptureTime(LiveFeature):
    """A leaking live feature: uses the day's snapshot whenever it finished."""

    name = "snapshot spot whenever captured"

    def value(self, data, decision_day, context):
        return data.snapshots[decision_day].spot


class _ReadsTodaysClose(LiveFeature):
    """A leaking live feature: uses the decision day's 15:30 close."""

    name = "today's close at 15:00"

    def value(self, data, decision_day, context):
        return data.panel.session_on(decision_day).underlying


@pytest.mark.parametrize("leaky", [_IgnoresCaptureTime(CUTOFF), _ReadsTodaysClose(CUTOFF)], ids=lambda f: f.name)
def test_the_harness_catches_live_leaks(leaky):
    data = live_data({**live_data().snapshots, DAY: snapshot(DAY, finished=time(15, 5))})
    with pytest.raises(AssertionError, match="look-ahead"):
        assert_no_lookahead(leaky, data, DAY, live_context(), perturbers=LIVE_PERTURBERS)
