"""Story G8 criterion 1: outcomes formed from the series rules, rebuilt by hand on real 2024 regular sessions (the
1 Nov 2024 muhurat session and 20 Jan 2024's special session are not in the regular list, so a return runs from one
regular close to the next); the last horizons are unresolved; V1 from A16 rows, a void row a void outcome."""

import math
from datetime import date

import pytest

from fno.constants import V1_RV_1S, V2_RV_5S, V6_BIG_MOVE_5S, V7_VIX_UP_5S
from fno.forecast_scoring.v4.outcomes import OutcomeSeries, SeriesOutcomes
from fno.forecast_v4.pairs import DatedForecasts, pair_point
from tests.forecast_scoring_v4.helpers import regular_closes, v6b_outcomes


class RealSeries(OutcomeSeries):
    def __init__(self, sessions, intraday=None):
        self.rows, self.intraday = sessions, intraday or {}

    def sessions(self):
        return self.rows

    def close_proxy_rv(self):
        r = self.rows
        return {r[i][0]: math.log(r[i][1] / r[i - 1][1]) ** 2 for i in range(1, len(r))}

    def big_move_outcomes(self, question):
        return {day: o.value for day, o in v6b_outcomes(self.rows).items()}

    def intraday_rv(self):
        return self.intraday


@pytest.fixture(scope="module")
def sessions():
    return regular_closes(date(2024, 1, 1), date(2024, 12, 31))


def test_v2_sums_the_next_five_regular_sessions_across_the_muhurat_and_special_days(sessions):
    days = [s[0] for s in sessions]
    assert date(2024, 11, 1) not in days and date(2024, 1, 20) not in days
    outcomes = SeriesOutcomes(RealSeries(sessions)).outcomes(V2_RV_5S)
    i = days.index(date(2024, 10, 29))  # 30 Oct, 31 Oct, 4 Nov, 5 Nov, 6 Nov: the muhurat session sits inside 4 Nov
    by_hand = sum(math.log(sessions[j][1] / sessions[j - 1][1]) ** 2 for j in range(i + 1, i + 6))
    assert outcomes[days[i]].value == pytest.approx(by_hand)
    assert days[i + 5] == date(2024, 11, 6)
    assert outcomes[days[i]].vix == sessions[i + 1][2]
    assert outcomes[days[i]].log_return == pytest.approx(math.log(sessions[i + 1][1] / sessions[i][1]))
    assert days[-6] in outcomes and days[-5] not in outcomes  # the last five horizons are unresolved


def test_v7_is_strictly_higher_and_v6_comes_from_the_series_rules(sessions):
    days = [s[0] for s in sessions]
    v7 = SeriesOutcomes(RealSeries(sessions)).outcomes(V7_VIX_UP_5S)
    assert all(v7[d].value == (sessions[i + 5][2] > sessions[i][2]) for i, d in enumerate(days[:-5]))
    tie = [(date(2024, 1, k + 1), 100.0 + k, 15.0) for k in range(7)]
    assert SeriesOutcomes(RealSeries(tie)).outcomes(V7_VIX_UP_5S)[date(2024, 1, 1)].value is False
    v6 = SeriesOutcomes(RealSeries(sessions)).outcomes(V6_BIG_MOVE_5S)
    assert {d: o.value for d, o in v6.items()} == {d: o.value for d, o in v6b_outcomes(sessions).items()}


def test_v1_reads_the_next_sessions_a16_row_and_a_void_row_is_a_void_outcome(sessions):
    days = [s[0] for s in sessions[:4]]
    series = RealSeries(sessions[:4], {days[1]: 4e-5, days[2]: None})
    outcomes = SeriesOutcomes(series).outcomes(V1_RV_1S)
    assert outcomes[days[0]].value == 4e-5 and not outcomes[days[0]].void
    assert outcomes[days[1]].void and days[2] not in outcomes  # day 3 has no A16 row: unresolved
    rows = [DatedForecasts(d, 5e-5, 5e-5, outcomes[d].value if d in outcomes else None,
                           d in outcomes and outcomes[d].void) for d in days[:3]]  # fmt: skip
    pairing = pair_point(rows)
    assert (pairing.void, pairing.unresolved, len(pairing.scored.days)) == (1, 1, 1)
