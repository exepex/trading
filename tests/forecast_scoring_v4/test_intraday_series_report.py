"""Story G7b completion, part f, criterion 17 (G8's side): V2's intraday version is its own reported series. It uses
V2's forecaster rows and primary baseline against the intraday outcome, has a seed word apart from V2's comparison,
is never a member, and starts at the first forecast day whose whole horizon is live A16 sessions."""

from datetime import date, timedelta

import pytest

from fno.constants import (
    V1_RV_1S,
    V2_RV_5S,
    V3_RV_20S,
    V4_BASELINE_HAR_DAILY,
    V4_BASELINE_PREMIUM_ADJUSTED,
    V4_COHORT_LIVE,
    V4_SLOT_RULES,
)
from fno.forecast_scoring.v4.comparison import seed_word
from fno.forecast_scoring.v4.inputs import V4ForecastSource
from fno.forecast_scoring.v4.outcomes import OutcomeSeries, SeriesOutcomes
from fno.forecast_scoring.v4.primary import primary_names
from fno.forecast_scoring.v4.records import NoRegistrations, Registration, SlotRegistry
from fno.forecast_scoring.v4.scoring import V4Scoring
from fno.forecast_v4.terms import FAMILY_SIZE
from fno.forecast_v4_rules.constants import V4_BASELINE_PREMIUM_ADJUSTED_INTRADAY
from tests.forecast_scoring_v4.helpers import values

SERIES = f"{V2_RV_5S}/intraday"
DAYS = [date(2026, 10, 12) + timedelta(n) for n in range(14) if (date(2026, 10, 12) + timedelta(n)).weekday() < 5]
FIRST_A16 = DAYS[1]  # A16's first live session: the series starts at DAYS[0]


def primary(comparisons):
    """The series' comparison against yardstick B (V2's or V3's primary); A's is apart (W3)."""
    (found,) = [c for c in comparisons if c.baseline == V4_BASELINE_PREMIUM_ADJUSTED]
    return found


class Series(OutcomeSeries):
    def __init__(self, intraday):
        self.rv = intraday

    def sessions(self):
        return [(d, 25000.0 + i, 14.0) for i, d in enumerate(DAYS)]

    def close_proxy_rv(self):
        return {d: 1e-4 for d in DAYS}

    def big_move_outcomes(self, question):
        return {}

    def vix_up_outcomes(self):
        return {}

    def intraday_rv(self):
        return self.rv


def test_the_intraday_outcome_starts_at_the_first_full_live_window_and_voids_on_a_void_session():
    intraday = {d: 2e-5 for d in DAYS if d >= FIRST_A16}
    outcomes = SeriesOutcomes(Series(intraday)).outcomes(SERIES)
    assert min(outcomes) == DAYS[0] and outcomes[DAYS[0]].value == 1e-4 and not outcomes[DAYS[0]].void
    assert DAYS[-5] not in outcomes  # its horizon runs past the rows: unresolved
    intraday[DAYS[3]] = None
    voided = SeriesOutcomes(Series(intraday)).outcomes(SERIES)
    assert voided[DAYS[0]].void and voided[DAYS[2]].void and not voided[DAYS[3]].void  # DAYS[3] is not ahead of itself
    assert SeriesOutcomes(Series({})).outcomes(SERIES) == {}


def test_the_close_proxy_series_is_unchanged_by_the_intraday_one():
    close = SeriesOutcomes(Series({})).outcomes(V2_RV_5S)
    assert close[DAYS[0]].value == 5e-4  # five close-proxy sessions of 1e-4


class V2Rows(V4ForecastSource):
    def forecasters(self, question):
        return ["v2_close_blend", V4_BASELINE_PREMIUM_ADJUSTED] if question == V2_RV_5S else []

    def values(self, question, forecaster):
        assert question == V2_RV_5S  # the series reads V2's rows, never rows of its own
        value = 1.2e-4 if forecaster == "v2_close_blend" else 1.5e-4
        return values({d: value for d in DAYS[:4]}, live=True)


class RulesSlot(SlotRegistry):
    def registered(self):
        return {(V2_RV_5S, V4_SLOT_RULES): Registration("v2_close_blend", DAYS[0])}


def test_the_series_scores_v2s_rows_against_the_intraday_outcome_apart_from_v2():
    intraday = {d: 2e-5 for d in DAYS if d >= FIRST_A16}
    scoring = V4Scoring(V2Rows(), SeriesOutcomes(Series(intraday)), RulesSlot())
    series = scoring.question_report(SERIES).cohorts[V4_COHORT_LIVE]
    close = scoring.question_report(V2_RV_5S).cohorts[V4_COHORT_LIVE]
    assert series.scores["v2_close_blend"].n == 4 and close.scores["v2_close_blend"].n == 4
    assert series.scores["v2_close_blend"] != close.scores["v2_close_blend"]  # other outcomes, never pooled
    comparison = primary(series.comparisons)
    assert comparison.baseline == V4_BASELINE_PREMIUM_ADJUSTED and comparison.question == V2_RV_5S  # V2's loss, block
    assert seed_word(SERIES, None, "v2_close_blend") > FAMILY_SIZE
    assert seed_word(SERIES, None, "v2_close_blend") != seed_word(V2_RV_5S, None, "v2_close_blend")


def test_the_series_is_never_a_member():
    intraday = {d: 2e-5 for d in DAYS if d >= FIRST_A16}
    members = V4Scoring(V2Rows(), SeriesOutcomes(Series(intraday)), RulesSlot()).member_comparisons(None)
    assert set(members) == {(V2_RV_5S, V4_SLOT_RULES)}
    assert V4Scoring(V2Rows(), SeriesOutcomes(Series(intraday)), NoRegistrations()).member_comparisons(None) == {}


def test_the_report_seeds_the_series_comparison_with_its_own_number_never_v2s_member_seed(monkeypatch):
    import fno.forecast_scoring.v4.scoring as scoring_module

    seeds = []
    real = scoring_module.compare
    monkeypatch.setattr(scoring_module, "compare", lambda *a: seeds.append((a[0], a[5])) or real(*a))
    intraday = {d: 2e-5 for d in DAYS if d >= FIRST_A16}
    scoring = V4Scoring(V2Rows(), SeriesOutcomes(Series(intraday)), RulesSlot())
    scoring.question_report(SERIES)
    series_seeds = {k for _, k in seeds}
    seeds.clear()
    scoring.question_report(V2_RV_5S)
    yardstick_a = f"{SERIES}|{V4_BASELINE_PREMIUM_ADJUSTED_INTRADAY}"
    assert series_seeds == {seed_word(SERIES, None, "v2_close_blend"), seed_word(yardstick_a, None, "v2_close_blend")}
    assert series_seeds.isdisjoint({k for _, k in seeds})  # V2's own comparison uses the rules member's seed


def test_with_rows_but_no_live_window_the_series_has_not_enough_data():
    assert V4Scoring(V2Rows(), SeriesOutcomes(Series({})), NoRegistrations()).question_report(SERIES).status == (
        "not enough data yet"
    )


def test_forecast_days_before_the_series_start_are_neither_unresolved_nor_missed():
    # A16 from DAYS[2]: the series starts at DAYS[1]; V2's rows on DAYS[0..3]; DAYS[0] is before the start
    intraday = {d: 2e-5 for d in DAYS if d >= DAYS[2]}
    report = V4Scoring(V2Rows(), SeriesOutcomes(Series(intraday)), NoRegistrations()).question_report(SERIES)
    comparison = primary(report.cohorts[V4_COHORT_LIVE].comparisons)
    assert report.live_forecasts == 6  # 3 days x 2 forecasters, DAYS[0] left out
    assert comparison.pairing.scored.days == tuple(DAYS[1:4]) and comparison.pairing.unresolved == 0


def test_a_void_window_is_counted_void_in_the_pairing():
    intraday = {d: 2e-5 for d in DAYS if d >= FIRST_A16}
    intraday[DAYS[2]] = None  # voids the windows of DAYS[0], DAYS[1]
    report = V4Scoring(V2Rows(), SeriesOutcomes(Series(intraday)), NoRegistrations()).question_report(SERIES)
    comparison = primary(report.cohorts[V4_COHORT_LIVE].comparisons)
    assert comparison.pairing.void == 2 and comparison.pairing.scored.days == tuple(DAYS[2:4])


class BothYardsticks(V2Rows):
    def forecasters(self, question):
        return super().forecasters(question) + ([V4_BASELINE_PREMIUM_ADJUSTED_INTRADAY] if question == V2_RV_5S else [])

    def values(self, question, forecaster):
        if forecaster == V4_BASELINE_PREMIUM_ADJUSTED_INTRADAY:
            return values({d: 1.4e-4 for d in DAYS[:4]}, live=True)
        return super().values(question, forecaster)


def test_w3_both_yardsticks_compare_the_series_forecasters_each_labelled_and_seeded_apart():
    intraday = {d: 2e-5 for d in DAYS if d >= FIRST_A16}
    scoring = V4Scoring(BothYardsticks(), SeriesOutcomes(Series(intraday)), NoRegistrations())
    comparisons = scoring.question_report(SERIES).cohorts[V4_COHORT_LIVE].comparisons
    pairs = {(c.forecaster, c.baseline) for c in comparisons}
    assert ("v2_close_blend", V4_BASELINE_PREMIUM_ADJUSTED) in pairs
    assert ("v2_close_blend", V4_BASELINE_PREMIUM_ADJUSTED_INTRADAY) in pairs
    assert (V4_BASELINE_PREMIUM_ADJUSTED_INTRADAY, V4_BASELINE_PREMIUM_ADJUSTED_INTRADAY) not in pairs
    close = scoring.question_report(V2_RV_5S).cohorts[V4_COHORT_LIVE].comparisons
    assert {c.baseline for c in close} == {V4_BASELINE_PREMIUM_ADJUSTED}  # V2's own series: yardstick B only
    close_scores = scoring.question_report(V2_RV_5S).cohorts[V4_COHORT_LIVE].scores
    assert V4_BASELINE_PREMIUM_ADJUSTED_INTRADAY not in close_scores  # A is no forecaster of the close-proxy block
    assert seed_word(f"{SERIES}|{V4_BASELINE_PREMIUM_ADJUSTED_INTRADAY}", None, "v2_close_blend") != seed_word(
        SERIES, None, "v2_close_blend"
    )


def test_v3s_series_uses_v3s_rows_block_and_horizon():
    days = [date(2026, 9, 1) + timedelta(n) for n in range(60) if (date(2026, 9, 1) + timedelta(n)).weekday() < 5]

    class Wide(Series):
        def sessions(self):
            return [(d, 25000.0, 14.0) for d in days]

    class V3Rows(V4ForecastSource):
        def forecasters(self, question):
            return ["v3_close_blend", V4_BASELINE_PREMIUM_ADJUSTED] if question == V3_RV_20S else []

        def values(self, question, forecaster):
            assert question == V3_RV_20S
            return values({d: 4e-4 for d in days[:3]}, live=True)

    outcomes = SeriesOutcomes(Wide({d: 2e-5 for d in days})).outcomes(f"{V3_RV_20S}/intraday")
    assert outcomes[days[0]].value == pytest.approx(20 * 2e-5)  # 20 sessions
    report = V4Scoring(V3Rows(), SeriesOutcomes(Wide({d: 2e-5 for d in days})), NoRegistrations())
    comparison = primary(report.question_report(f"{V3_RV_20S}/intraday").cohorts[V4_COHORT_LIVE].comparisons)
    assert comparison.question == V3_RV_20S  # V3's loss and block 20


class V1Rows(V4ForecastSource):
    NAMES = (
        V4_BASELINE_HAR_DAILY,
        "v1_close_blend",
        V4_BASELINE_PREMIUM_ADJUSTED,
        V4_BASELINE_PREMIUM_ADJUSTED_INTRADAY,
    )

    def forecasters(self, question):
        return list(self.NAMES) if question == V1_RV_1S else []

    def values(self, question, forecaster):
        if forecaster not in self.NAMES:
            return {}  # no intraday HAR rows yet
        return values({d: 2e-5 * (1 + self.NAMES.index(forecaster) / 10) for d in DAYS[:4]}, live=True)


def test_w3_v1s_forecasters_are_compared_against_both_yardsticks_beside_its_primary():
    """Review finding (G7b completion): V1 had only its HAR primary; W3 and criterion 4 say both yardsticks too."""
    scoring = V4Scoring(V1Rows(), SeriesOutcomes(Series({d: 2e-5 for d in DAYS})), NoRegistrations())
    pairs = {(c.forecaster, c.baseline) for c in scoring.question_report(V1_RV_1S).cohorts[V4_COHORT_LIVE].comparisons}
    assert {
        ("v1_close_blend", y) for y in (V4_BASELINE_PREMIUM_ADJUSTED, V4_BASELINE_PREMIUM_ADJUSTED_INTRADAY)
    } <= pairs
    primary_name = " / ".join(sorted(primary_names(V1_RV_1S)))
    assert ("v1_close_blend", primary_name) in pairs
    assert (V4_BASELINE_PREMIUM_ADJUSTED, V4_BASELINE_PREMIUM_ADJUSTED_INTRADAY) not in pairs  # never one against other
