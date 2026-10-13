"""Story B7 live features: hand values, criterion 4 (invalid or missing quotes give None, never the last price) and a
capture that finished after the cutoff is not used."""

import math
from datetime import time

import pytest
from live_fixtures import CUTOFF, DAY, RATE, live_context, live_data, quotes, snapshot

from fno.research_engine.implied_vol import Black76
from fno.research_engine.live_features import LiveAtmIvMinusRealised, LiveScheduledEventInWindow, LiveVixAboveMedian
from fno.research_engine.volatility_features import AtmIvMinusRealised

F1_LIVE, F2_LIVE, F3_LIVE = (
    LiveAtmIvMinusRealised(CUTOFF, RATE, Black76()),
    LiveVixAboveMedian(CUTOFF),
    LiveScheduledEventInWindow(CUTOFF),
)


def f1(snap):
    return F1_LIVE.value(live_data({DAY: snap}), DAY, live_context())


def test_live_f1_equals_the_hand_calculation():
    """Black-76 on the recorded same-expiry future (20,100) gives 17% for both mids; realised from 20 +-1% returns =
    15.87; live F1 = 1.13."""
    assert f1(snapshot(DAY)) == pytest.approx(17.0 - 0.01 * math.sqrt(252) * 100, abs=1e-6)


def test_live_features_are_known_at_the_cutoff_and_differ_from_the_research_names():
    assert F1_LIVE.known_at(DAY).time() == time(15, 0) and F1_LIVE.name != AtmIvMinusRealised.name


def test_invalid_quotes_give_none_never_the_last_price():
    assert f1(snapshot(DAY, valid=False)) is None


@pytest.mark.parametrize("leg", [(20000.0, "CE"), (20000.0, "PE")])
def test_a_missing_or_one_sided_atm_quote_gives_none(leg):
    snap = snapshot(DAY)
    missing = snap.__class__(snap.day, snap.finished_at, snap.spot, snap.vix, tuple(
        q for q in snap.quotes if (q.strike, q.kind) != leg
    ))  # fmt: skip
    assert f1(missing) is None
    one_sided = snap.__class__(snap.day, snap.finished_at, snap.spot, snap.vix, tuple(
        q.__class__(q.expiry, q.strike, q.kind, 0.0, q.ask, True) if (q.strike, q.kind) == leg else q
        for q in snap.quotes
    ))  # fmt: skip
    assert f1(one_sided) is None


def test_a_snapshot_finished_after_the_cutoff_or_missing_is_not_used():
    assert f1(snapshot(DAY, finished=time(15, 5))) is None
    assert F1_LIVE.value(live_data({}), DAY, live_context()) is None


def test_live_f2_needs_vix_at_the_cutoff():
    data = live_data({DAY: snapshot(DAY, vix=None)})
    assert F2_LIVE.value(data, DAY, live_context()) is None  # A4 records no VIX today: live F2 is never computed
    assert F2_LIVE.value(live_data({DAY: snapshot(DAY, vix=14.0)}), DAY, live_context()) is True  # median 13
    assert F2_LIVE.value(live_data({DAY: snapshot(DAY, vix=12.0)}), DAY, live_context()) is False


def test_live_f3_is_f3_at_the_cutoff():
    assert F3_LIVE.value(live_data(), DAY, live_context()) is True
    assert F3_LIVE.known_at(DAY).time() == CUTOFF


def test_quotes_helper_prices_mids_at_the_model():
    assert all(q.mid is not None for q in quotes(DAY))


def test_live_f1_needs_the_recorded_same_expiry_future_and_that_it_traded():
    assert f1(snapshot(DAY, future_volume=None)) is None  # an older capture without futures
    assert f1(snapshot(DAY, future_volume=0)) is None  # recorded but not traded today: never a stale price


def test_live_f2_history_ends_at_the_previous_session():
    """Judge 44 minor 1: the 250 previous closes are 125 x 10 and 125 x 20 (median 15). If today's own close (100)
    were counted, the oldest 10 would drop out and the median become 20, flipping the answer for a 3 pm VIX of 17."""
    from feature_fixtures import make_panel, session_days

    from fno.research_engine.features import ResearchData

    days = session_days(251)
    vix = [10.0] * 125 + [20.0] * 125 + [100.0]
    data = ResearchData(make_panel(days, [20000.0] * 251, vix=vix), (), {days[-1]: snapshot(days[-1], vix=17.0)})
    assert F2_LIVE.value(data, days[-1], live_context(days[-1])) is True
