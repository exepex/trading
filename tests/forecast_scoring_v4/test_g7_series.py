"""G8 reads outcomes through G7's series rules on the real committed closes: the V6b outcomes equal the test's own
hand rebuild, and the regime inputs are the first session's VIX and log return."""

import math
from datetime import date

from fno.constants import V1_RV_1S, V6_BIG_MOVE_5S
from fno.forecast_scoring.v4.g7_series import G7Series
from fno.forecast_scoring.v4.outcomes import SeriesOutcomes
from tests.forecast_scoring_v4.helpers import WARMUP, regular_closes, v6b_outcomes


def test_real_v6b_outcomes_through_g7s_rules_match_the_hand_rebuild():
    sessions = regular_closes(date(2017, 1, 1), date(2099, 1, 1))
    outcomes = SeriesOutcomes(G7Series(WARMUP.read_text(encoding="utf-8"), list)).outcomes(V6_BIG_MOVE_5S)
    assert outcomes == v6b_outcomes(sessions) and len(outcomes) == len(sessions) - 5
    first = outcomes[sessions[0][0]]
    assert first.vix == sessions[1][2] and math.isclose(first.log_return, math.log(sessions[1][1] / sessions[0][1]))


def test_v1_reads_only_the_a16_rows_it_is_given():
    rows = [
        {
            "session": "2026-10-16",
            "status": "ok",
            "rv_session": "0.00004",
            "first_seen_at": "2026-10-16T16:00:00+05:30",
            "method": "rv-quote-15m-v1",
        }
    ]
    series = G7Series(WARMUP.read_text(encoding="utf-8"), lambda: rows)
    assert series.intraday_rv() == {date(2026, 10, 16): 4e-05}
    outcomes = SeriesOutcomes(series).outcomes(V1_RV_1S)
    # V1 for 15 Oct is 16 Oct's session RV: unresolved until the closes file reaches 16 Oct, then exactly the given row
    assert set(outcomes) <= {date(2026, 10, 15)} and all(o.value == 4e-05 for o in outcomes.values())
