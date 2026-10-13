"""Story G4 for the AI books (judge 58's list): their records, the days never scored, coverage per book from the common
start, the isolation label, and live question 5 scored against the forecast's own 15:00 pack IV30 (response 69, 7)."""

from __future__ import annotations

import json
from datetime import date

import pytest

from fno.constants import BOOK1_RULES, BOOK2_HYBRID, BOOK3_AI, FORECAST_Q5_RV_BELOW_IV
from fno.forecast.iv30 import AtmIv30
from fno.forecast_scoring.coverage import book_coverage
from fno.forecast_scoring.q5_thresholds import pack_iv30
from fno.forecast_scoring.score_inputs import CLOSE_PROXY, LIVE, ScoredForecast
from fno.forecast_scoring.score_report import ReportContext, report_document, weekly_summary
from fno.forecast_scoring.scoring import ForecastScorer
from tests.forecast_scoring.scoring_fixtures import FIRST, horizon_day, outcomes

DAY = date(2026, 10, 14)


def live(book, day, p=0.6):
    return ScoredForecast(LIVE, book, day, FORECAST_Q5_RV_BELOW_IV, p, "interpolated")


def test_coverage_counts_from_the_common_start_and_a_missed_day_lowers_it():
    days = [date(2026, 10, 13), date(2026, 10, 14), date(2026, 10, 15), date(2026, 10, 16)]
    scored = [live(BOOK1_RULES, d) for d in days] + [live(BOOK2_HYBRID, days[2]), live(BOOK2_HYBRID, days[3])]
    scored += [live(BOOK3_AI, days[1], None)]  # "no forecast" is not a counted day
    cov = book_coverage(days, scored, date(2026, 10, 14), date(2026, 10, 16))
    assert cov == {BOOK1_RULES: {"counted_days": 3, "pack_days": 3}, BOOK2_HYBRID: {"counted_days": 2, "pack_days": 3},
                   BOOK3_AI: {"counted_days": 0, "pack_days": 3}}  # fmt: skip
    assert book_coverage(days, scored, None, date(2026, 10, 16)) is None


def test_the_report_shows_coverage_common_start_isolation_and_unscored_days():
    cov = {BOOK1_RULES: {"counted_days": 3, "pack_days": 3}}
    context = ReportContext(DAY, {}, False, 0, (), DAY, cov, {}, ({"day": "2026-10-14", "book": BOOK2_HYBRID,
                                                                  "reason": "status exposed"},))  # fmt: skip
    document = report_document(context, [])
    assert document["common_start"] == "2026-10-14" and document["coverage"] == cov
    assert document["ai_isolation"] == {BOOK2_HYBRID: ["sealed_same_day"], BOOK3_AI: ["sealed_same_day"]}
    assert document["unscored_ai_days"][0]["reason"] == "status exposed"
    lines = weekly_summary(document)
    assert any(line.startswith("Live coverage since 2026-10-14") and "book1_rules 3 of 3" in line for line in lines)
    assert any("sealed_same_day" in line for line in lines)


def test_live_question_5_is_scored_against_the_pack_iv30_and_history_against_the_panel():
    """Planted disagreement: the panel's close IV30 is 1 point below the next 20-day realised volatility (outcome no),
    the pack's 15:00 IV30 1 point above it (outcome yes). The same day and probability score differently by mode."""
    as_of = horizon_day(FIRST, 20)
    rv = outcomes(as_of).targets.next_rv(FIRST)
    panel, pack = AtmIv30(rv - 1, False, (date(2025, 2, 27),)), AtmIv30(rv + 1, False, (date(2025, 2, 27),))
    resolvers = {CLOSE_PROXY: outcomes(as_of, iv30=lambda d: (True, panel)),
                 LIVE: outcomes(as_of, iv30=lambda d: (True, pack))}  # fmt: skip
    items = [ScoredForecast(mode, BOOK1_RULES, FIRST, FORECAST_Q5_RV_BELOW_IV, 0.9, "interpolated")
             for mode in (CLOSE_PROXY, LIVE)]  # fmt: skip
    by_mode = {
        m.mode: m.scores[(BOOK1_RULES, FORECAST_Q5_RV_BELOW_IV)].primary for m in ForecastScorer(resolvers).score(items)
    }
    assert by_mode[LIVE].mean_brier == pytest.approx(0.01) and by_mode[CLOSE_PROXY].mean_brier == pytest.approx(0.81)


def test_the_pack_iv30_is_read_from_the_pack_and_none_or_unknown_is_no_value():
    pack = {"iv30": {"points": 14.8151, "status": "interpolated", "expiries": ["2026-10-27", "2026-11-24"]}}
    assert pack_iv30(json.dumps(pack).encode()) == AtmIv30(14.8151, False, (date(2026, 10, 27), date(2026, 11, 24)))
    flagged = {"iv30": {"points": 14.0, "status": "flagged", "expiries": ["2026-10-27"]}}
    assert pack_iv30(json.dumps(flagged).encode()).flagged
    assert pack_iv30(b'{"iv30": null}') is None
