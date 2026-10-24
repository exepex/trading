"""G8 reads outcomes through G7's series rules on the real committed closes: the V6b outcomes equal the test's own
hand rebuild, and the regime inputs are the first session's VIX and log return."""

import math
from datetime import date, timedelta

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


def a16_row(session: date) -> dict:
    return {
        "session": session.isoformat(),
        "status": "ok",
        "rv_session": "0.00004",
        "first_seen_at": f"{session.isoformat()}T16:00:00+05:30",
        "method": "rv-quote-15m-v1",
    }


def test_v1_reads_only_the_a16_rows_it_is_given():
    # Dates come from the committed closes file, which grows every trading day (a fixed date broke on 16 Oct's close)
    sessions = regular_closes(date(2017, 1, 1), date(2099, 1, 1))
    (before_last, *_), (last, *_) = sessions[-2], sessions[-1]
    after_last = last + timedelta(days=7)  # surely not in the file yet
    series = G7Series(WARMUP.read_text(encoding="utf-8"), lambda: [a16_row(after_last)])
    assert series.intraday_rv() == {after_last: 4e-05}
    assert SeriesOutcomes(series).outcomes(V1_RV_1S) == {}  # its session is not in the closes file: unresolved
    resolved = SeriesOutcomes(G7Series(WARMUP.read_text(encoding="utf-8"), lambda: [a16_row(last)]))
    assert list(resolved.outcomes(V1_RV_1S)) == [before_last]  # in the file: resolves the session before it
    assert resolved.outcomes(V1_RV_1S)[before_last].value == 4e-05
