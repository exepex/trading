"""Story G7b part a: V2 and V3's close-proxy baselines and blends, V7's outcome, base rate and `v7_vix_vs_mean20`."""

from datetime import date, timedelta
from pathlib import Path

import pytest

from fno.constants import (
    V2_RV_5S,
    V3_RV_20S,
    V4_BASELINE_BASE_RATE,
    V4_BASELINE_EWMA,
    V4_BASELINE_HAR_DAILY,
    V4_BASELINE_TRAILING,
    V7_VIX_UP_5S,
)
from fno.forecast_scoring.v4.outcomes import OutcomeSeries, SeriesOutcomes
from fno.forecast_v4_rules import records
from fno.forecast_v4_rules.baselines import NOT_ELIGIBLE, OK, BaseRate, TrailingSum
from fno.forecast_v4_rules.capture import DayForecasts, Inputs
from fno.forecast_v4_rules.constants import V4_RULE_V2_CLOSE_BLEND, V4_RULE_V3_CLOSE_BLEND, V4_RULE_V7_VIX_SIDE
from fno.forecast_v4_rules.series import DayValue, closes_rows, regular_closes, vix_closes, vix_up_outcomes
from fno.forecast_v4_rules.vix_rule import MIN_CELL, VixSideRate

ROOT = Path(__file__).resolve().parents[2]
TEXT = (ROOT / "research" / "data" / "nifty-panel" / "warmup_closes.csv").read_text()
DAY = date(2026, 10, 14)


def forecasts(text: str = TEXT) -> DayForecasts:
    rows = closes_rows(text)
    closes = regular_closes(rows)
    lines = [line for line in text.splitlines()[1:] if line.split(",")[1] == "regular"]
    return DayForecasts(Inputs(closes, vix_closes(rows), lines, [], [c.day for c in closes], "m" * 64))


def days(n: int, start: date = date(2020, 1, 1)) -> list[date]:
    return [start + timedelta(days=i) for i in range(n)]


def test_trailing_sum_is_the_last_h_session_rvs_before_the_day():
    rv = [DayValue(d, v) for d, v in zip(days(6), (1e-4, 2e-4, 3e-4, 4e-4, 5e-4, 6e-4), strict=True)]
    trailing = TrailingSum(rv)
    assert trailing.forecast(rv[5].day, 5).value == pytest.approx(1.5e-3)  # sessions 0-4, never day 5's own
    assert trailing.forecast(rv[4].day, 5).status == NOT_ELIGIBLE  # only 4 sessions before it
    zeros = TrailingSum([DayValue(d, 0.0) for d in days(6)])
    assert zeros.forecast(rv[5].day, 5).status == "missing"  # a variance that is not strictly positive


def test_v2_and_v3_blends_are_the_mean_of_their_har_and_ewma():
    values = forecasts().values(DAY)
    for question, blend in ((V2_RV_5S, V4_RULE_V2_CLOSE_BLEND), (V3_RV_20S, V4_RULE_V3_CLOSE_BLEND)):
        har, ewma = values[(V4_BASELINE_HAR_DAILY, question)], values[(V4_BASELINE_EWMA, question)]
        assert har.status == ewma.status == OK
        assert values[(blend, question)].value == pytest.approx((har.value + ewma.value) / 2)
        assert values[(V4_BASELINE_TRAILING, question)].status == OK
    one = forecasts().ewma.forecast(DAY, 1).value
    assert values[(V4_BASELINE_EWMA, V3_RV_20S)].value == pytest.approx(20 * one)  # h x s2


def test_no_forecast_for_a_day_reads_that_days_own_close_or_vix():
    """The look-ahead test: changing the day's own NIFTY and VIX closes changes none of its V2, V3 or V7 values."""
    line = next(line for line in TEXT.splitlines() if line.startswith(DAY.isoformat()))
    parts = line.split(",")
    plain = forecasts().values(DAY)
    keys = [k for k in plain if k[1] in (V2_RV_5S, V3_RV_20S, V7_VIX_UP_5S)]
    assert len(keys) == 10
    for factor in (0.7, 1.3):  # the VIX close pushed below and above its mean
        moved = ",".join(parts[:2] + [str(float(parts[2]) * factor), str(float(parts[3]) * factor)] + parts[4:])
        after = forecasts(TEXT.replace(line, moved)).values(DAY)
        assert all(plain[k] == after[k] for k in keys)


def test_v7_outcome_is_strictly_higher_five_sessions_later():
    vix = [DayValue(d, v) for d, v in zip(days(7), (15.0, 1, 1, 1, 1, 15.0, 15.01), strict=True)]
    tie, up = vix_up_outcomes(vix, 5)
    assert (tie.day, tie.value, tie.resolved_on) == (vix[0].day, False, vix[5].day)  # a tie is "no"
    assert (up.value, up.resolved_on) == (True, vix[6].day)


class CommittedSeries(OutcomeSeries):
    def __init__(self):
        rows = closes_rows(TEXT)
        self.rows = [(c.day, c.value, v.value) for c, v in zip(regular_closes(rows), vix_closes(rows), strict=True)]

    def sessions(self):
        return self.rows

    def close_proxy_rv(self):
        return {}

    def big_move_outcomes(self, question):
        return {}

    def intraday_rv(self):
        return {}


def test_the_shared_v7_rule_reproduces_g8s_v7_outcomes_on_the_committed_closes():
    g8 = SeriesOutcomes(CommittedSeries()).outcomes(V7_VIX_UP_5S)
    ours = {o.day: o.value for o in vix_up_outcomes(vix_closes(closes_rows(TEXT)), 5)}
    assert len(g8) > 2_400 and all(g8[d].value == ours[d] for d in g8)
    assert set(g8) == set(ours)


def outcome_series(n: int):
    vix = [DayValue(d, 10.0 + (i % 7)) for i, d in enumerate(days(n))]
    return vix, vix_up_outcomes(vix, 5)


def test_v7_base_rate_needs_500_resolved_outcomes():
    for n, status in ((505, NOT_ELIGIBLE), (506, OK)):  # outcomes resolved before the last day: n - 6
        vix, outcomes = outcome_series(n)
        assert BaseRate(outcomes).forecast(vix[-1].day).status == status


def test_vix_side_rule_is_the_lagged_two_cell_rate_with_its_fallback():
    vix, outcomes = outcome_series(600)
    rule = VixSideRate(vix, outcomes)
    d = vix[-1].day
    window = [o for o in outcomes if o.resolved_on < d][-750:]
    side = vix[-2].value < sum(v.value for v in vix[-21:-1]) / 20  # the side at d-1, mean over d-20..d-1
    cell = [o for o in window if rule.side_before(o.day) == side]
    assert len(cell) >= MIN_CELL
    assert rule.forecast(d).value == pytest.approx(sum(o.value for o in cell) / len(cell))
    assert rule.side_before(vix[19].day) is None and rule.side_before(vix[20].day) is not None  # 20 sessions needed
    flat = [DayValue(v.day, 12.0) for v in vix]  # always equal to its mean: "not below" (strict), one cell
    assert VixSideRate(flat, vix_up_outcomes(flat, 5)).forecast(d).value == 0.0
    rare = [DayValue(v.day, 30.0 if i == 590 else 12.0) for i, v in enumerate(vix)]  # a spike: 8 "below" days
    rare_out = vix_up_outcomes(rare, 5)
    rare_rule = VixSideRate(rare, rare_out)
    assert rare_rule.side_before(d) is True  # 12 sits below a mean lifted by the spike
    known = [o for o in rare_out if o.resolved_on < d][-750:]
    assert rare_rule.forecast(d).value == pytest.approx(sum(o.value for o in known) / len(known))  # plain share


def test_v7_side_rule_and_base_rate_are_not_eligible_below_500():
    vix, outcomes = outcome_series(400)
    assert VixSideRate(vix, outcomes).forecast(vix[-1].day).status == NOT_ELIGIBLE


def test_records_validate_v2_v3_as_variances_and_v7_as_a_probability():
    audit = dict(label="live", kind="rule", slot="reported", method_sha256="m", inputs_sha256="i", made_at="t")
    for question in (V2_RV_5S, V3_RV_20S):
        with pytest.raises(records.InvalidRecord):
            records.record(DAY, question, OK, 0.0, **audit)
        assert records.record(DAY, question, OK, 1.5, **audit).value == "1.5"  # a variance may exceed 1
    with pytest.raises(records.InvalidRecord):
        records.record(DAY, V7_VIX_UP_5S, OK, 1.01, **audit)


def test_every_new_forecaster_has_a_value_on_a_recent_day():
    values = forecasts().values(DAY)
    for key in ((V4_BASELINE_BASE_RATE, V7_VIX_UP_5S), (V4_RULE_V7_VIX_SIDE, V7_VIX_UP_5S)):
        assert values[key].status == OK and 0 < values[key].value < 1


def test_the_three_g7b_protocol_wordings_are_in_the_text():
    text = " ".join((ROOT / "research" / "forecasts" / "PROTOCOL_v4.md").read_text().split())
    for wording in (
        "A flagged IV30** (single expiry, `AtmIv30.flagged`) gives no raw and no premium-adjusted value that day",
        "V4's and V5's base rates count live outcomes only:** no end-of-day history fills them",
        "the first sighting in A8's release-check log (`release_times.first_seen_times`)",
    ):
        assert wording in text
