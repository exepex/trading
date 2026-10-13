"""Story G4 criterion 3: a forecast is never scored before its target date is resolvable."""

from __future__ import annotations

from datetime import date

from fno.constants import (
    BOOK1_RULES,
    FORECAST_Q1_UP_20D,
    FORECAST_Q4_VIX_UP_10D,
    FORECAST_Q5_RV_BELOW_IV,
)
from fno.forecast.iv30 import AtmIv30
from fno.forecast_scoring.resolution import PENDING, RESOLVED, VOID
from fno.forecast_scoring.score_inputs import CLOSE_PROXY
from fno.forecast_scoring.scoring import ForecastScorer
from tests.forecast_scoring.scoring_fixtures import DAYS, FIRST, forecast, horizon_day, nifty_close, outcomes

TARGET_20 = horizon_day(FIRST, 20)  # 30 Jan 2025: 20 trading days after 1 Jan with the 27 Jan holiday skipped
BEFORE = DAYS[DAYS.index(TARGET_20) - 1]


def test_the_target_day_counts_trading_days_and_skips_the_holiday():
    assert (date(2025, 1, 30), date(2025, 1, 29)) == (TARGET_20, BEFORE)


def test_pending_until_the_target_close_is_known_then_resolved():
    assert outcomes(BEFORE).resolve(FORECAST_Q1_UP_20D, FIRST).status == PENDING
    resolved = outcomes(TARGET_20).resolve(FORECAST_Q1_UP_20D, FIRST)
    assert resolved.status == RESOLVED and resolved.outcome == (nifty_close(DAYS.index(TARGET_20)) > nifty_close(0))


def test_data_after_the_as_of_day_is_never_read():
    """Closes exist through June, but as of the day before the target the outcome stays pending."""
    late = outcomes(BEFORE, data_through=date(2025, 6, 30))
    assert late.resolve(FORECAST_Q1_UP_20D, FIRST).status == PENDING


def test_closes_not_yet_arrived_keep_it_pending_and_a_missing_needed_close_voids_it():
    assert outcomes(date(2025, 3, 1), data_through=BEFORE).resolve(FORECAST_Q1_UP_20D, FIRST).status == PENDING
    gap = outcomes(date(2025, 3, 1), missing=(TARGET_20,))
    assert gap.resolve(FORECAST_Q1_UP_20D, FIRST).status == VOID


def test_the_ten_day_question_resolves_before_the_twenty_day_ones():
    as_of = horizon_day(FIRST, 10)
    resolver = outcomes(as_of)
    assert resolver.resolve(FORECAST_Q4_VIX_UP_10D, FIRST).status == RESOLVED
    assert resolver.resolve(FORECAST_Q1_UP_20D, FIRST).status == PENDING


def test_question_5_flagged_iv30_is_void_with_its_sensitivity_and_waits_for_the_panel():
    flagged = outcomes(TARGET_20, iv30=lambda d: (True, AtmIv30(40.0, True, (date(2025, 2, 27),))))
    res = flagged.resolve(FORECAST_Q5_RV_BELOW_IV, FIRST)
    assert res.status == VOID and res.flagged_outcome is not None
    assert outcomes(TARGET_20, iv30=lambda d: (True, None)).resolve(FORECAST_Q5_RV_BELOW_IV, FIRST) == (
        VOID,
        None,
        None,
    )
    assert outcomes(TARGET_20, iv30=lambda d: (False, None)).resolve(FORECAST_Q5_RV_BELOW_IV, FIRST).status == PENDING


def test_the_scorer_counts_pending_forecasts_and_scores_none_of_them():
    items = [
        forecast(BOOK1_RULES, FIRST, FORECAST_Q1_UP_20D, 0.6),
        forecast(BOOK1_RULES, DAYS[1], FORECAST_Q1_UP_20D, None),
    ]
    (mode,) = ForecastScorer({CLOSE_PROXY: outcomes(BEFORE)}).score(items)
    scores = mode.scores[(BOOK1_RULES, FORECAST_Q1_UP_20D)]
    assert scores.counts == {"forecasts": 2, "no_forecast": 1, PENDING: 1, VOID: 0, RESOLVED: 0}
    assert scores.primary.scored == 0 and scores.primary.mean_brier is None
    (mode,) = ForecastScorer({CLOSE_PROXY: outcomes(TARGET_20)}).score(items)
    assert mode.scores[(BOOK1_RULES, FORECAST_Q1_UP_20D)].counts[RESOLVED] == 1
