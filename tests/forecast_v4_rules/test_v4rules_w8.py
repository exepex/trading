"""Wording W8 (owner, 24 Oct 2026: "W8 - yes"; story G7b completion): A16b's candle back-fill fills yardstick A's
ratio window where A16 has no live row, never overriding a live row (void included); the stored ratio counts its
`backfill_window` points; the back-fill / live pairs; and judge 591 m2's review trigger, raised once."""

import json
from datetime import date, timedelta

import pytest

from fno.forecast_v4_rules import pack_wiring
from fno.forecast_v4_rules.candle_history import PairedRv, drift_days, paired_rv
from fno.forecast_v4_rules.intraday_series import RATIO_CLOSE_PROXY, RATIO_INTRADAY, backfill_window_points
from fno.forecast_v4_rules.pack_followups import W8_REVIEW_FOLDER, review_w8
from fno.forecast_v4_rules.ratio_store import StoredRatio, ratio_path
from tests.forecast_v4_rules.test_v4rules_pack_capture import REFIT, Drive, unit_ratio

DAYS = [date(2026, 8, 1) + timedelta(n) for n in range(50)]


def test_a_window_point_is_backfill_window_when_its_horizon_holds_a_back_filled_session():
    sessions = DAYS[:6]
    assert backfill_window_points(sessions, 1, {DAYS[2]}) == {DAYS[1]}
    assert backfill_window_points(sessions, 2, {DAYS[2]}) == {DAYS[0], DAYS[1]}  # t+1..t+h, never t itself
    assert backfill_window_points(sessions, 5, set()) == set()


def test_the_stored_ratio_counts_its_backfill_window_points_and_the_close_proxy_none():
    points = [date(2024, 1, 1) + timedelta(n) for n in range(100)]
    drive = Drive()
    outside = {date(2023, 12, 1), REFIT}  # never window points: they count for nothing
    labelled = frozenset(points) | outside
    StoredRatio(unit_ratio(0.6), "q", RATIO_INTRADAY, REFIT, drive.get, drive.put, labelled).at(REFIT)
    StoredRatio(unit_ratio(0.6), "q", RATIO_CLOSE_PROXY, REFIT, drive.get, drive.put).at(REFIT)
    intraday = json.loads(drive.files[ratio_path(RATIO_INTRADAY, "q", REFIT)])
    assert intraday["backfill_window"] == 100 and intraday["count"] == 600
    assert json.loads(drive.files[ratio_path(RATIO_CLOSE_PROXY, "q", REFIT)])["backfill_window"] == 0


def test_the_window_measure_takes_the_back_fill_only_where_a16_has_no_live_row(monkeypatch):
    live = {DAYS[1]: 2e-5, DAYS[2]: None}  # a void live row stays void, never filled from the back-fill
    candle = {DAYS[0]: 1e-5, DAYS[1]: 9e-5, DAYS[2]: 3e-5, DAYS[3]: None}
    monkeypatch.setattr(pack_wiring, "live_rv", lambda: live)
    monkeypatch.setattr(pack_wiring, "candle_rv", lambda: candle)
    measure, backfilled = pack_wiring.intraday_rv()
    assert measure == {DAYS[0]: 1e-5, DAYS[1]: 2e-5, DAYS[2]: None, DAYS[3]: None}
    assert backfilled == {DAYS[0], DAYS[3]}


def test_the_one_pairing_keeps_sessions_where_both_rows_are_non_void_in_session_order():
    live = {DAYS[3]: 2e-5, DAYS[0]: 1e-5, DAYS[1]: None, DAYS[2]: 3e-5, DAYS[4]: 0.0}
    candle = {DAYS[0]: 1.1e-5, DAYS[1]: 4e-5, DAYS[2]: None, DAYS[3]: 1.8e-5, DAYS[4]: 1e-5}
    paired = paired_rv(live, candle)  # DAYS[1] void live, DAYS[2] void candle, DAYS[4] zero live: no pair
    assert [p.day for p in paired] == [DAYS[0], DAYS[3]]
    assert paired[0] == PairedRv(DAYS[0], 1e-5, 1.1e-5, pytest.approx(1.1))
    assert drift_days(paired) == [(DAYS[0], 1.1e-5, 1e-5), (DAYS[3], 1.8e-5, 2e-5)]  # candle / live for proxy_drift
    assert paired_rv({}, candle) == [] and paired_rv(live, {}) == []


def pairs(ratio: float, n: int = 20):
    return [(d, ratio * 1e-5, 1e-5) for d in DAYS[:n]]


@pytest.mark.parametrize(
    ("given", "raised"),
    [(pairs(1.2, 19), False), (pairs(1.05), False), (pairs(0.95), False), (pairs(1.2), True)],
)
def test_the_review_needs_20_paired_days_and_alerts_only_outside_the_band(given, raised):
    written, sent = {}, []
    lines = review_w8(DAYS[-1], given, False, written.__setitem__, lambda text: sent.append(text) or "alert sent")
    assert bool(lines) is raised and bool(written) is raised and len(sent) == int(raised)
    if raised:
        assert lines == [sent[0], "alert sent"] and "median 1.2000" in sent[0]
        assert list(written) == [f"{W8_REVIEW_FOLDER}/{DAYS[-1].isoformat()}.json"]


def test_the_review_uses_the_latest_20_and_is_raised_once():
    drifted = [(d, 1e-5, 1e-5) for d in DAYS[:30]] + [(d, 1.3e-5, 1e-5) for d in DAYS[30:]]
    sent = []
    assert review_w8(DAYS[-1], drifted, False, {}.__setitem__, sent.append)  # all days' median 1.0, latest 20 1.3
    assert review_w8(DAYS[-1], drifted, True, {}.__setitem__, sent.append) == []  # a marker exists: never again
    assert len(sent) == 1
