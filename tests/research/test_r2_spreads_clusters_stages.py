"""R2 spread buckets, clusters, correlation and the decision (PROTOCOL.md sections 6.2, 7-9; amendment 1 A-C)."""

from datetime import date

import pytest
from r2_synthetic import quoted
from r2study.bhav import DaySummary, Future
from r2study.clusters import bootstrap_interval, cluster_key, icc_anova, kish_count
from r2study.events import Event
from r2study.moves import OutsideCorrelationYears, market_adjusted_move, within_week_correlation
from r2study.spreads import SpreadModel, make_bucket, merged_groups, tercile
from r2study.stages import CANNOT, NO, YES, StructureResult, decide


def test_thin_terciles_merge_toward_the_more_liquid_neighbour():
    assert merged_groups([10, 40, 40]) == [(0, 1), (2,)]
    assert merged_groups([40, 40, 10]) == [(0,), (1, 2)]  # the most liquid merges toward the middle
    assert merged_groups([10, 10, 10]) == [(0, 1, 2)]
    assert merged_groups([30, 30, 30]) == [(0,), (1,), (2,)]  # at 30: no merge
    assert merged_groups([29, 30, 30]) == [(0, 1), (2,)]  # just under: merged
    assert merged_groups([40, 10, 40]) == [(0,), (1, 2)]  # a thin middle merges up, toward more liquidity
    assert merged_groups([0, 0, 0]) == [(0, 1, 2)]


def test_bucket_with_more_than_20_percent_one_sided_legs_is_untradable():
    at_limit = [quoted(0, 10)] * 8 + [quoted(0, 10, two_sided=False)] * 2
    assert not make_bucket("K0", (0,), at_limit).untradable  # 20%: tradable
    over = [quoted(0, 10)] * 7 + [quoted(0, 10, two_sided=False)] * 3
    assert make_bucket("K0", (0,), over).untradable
    assert make_bucket("K0", (0,), []).untradable  # no quoted leg at all


def test_bucket_pad_is_the_75th_percentile_half_spread_and_depth_is_in_lots():
    legs = [quoted(0, 10, spread=s, qty=q) for s, q in ((0.01, 100), (0.02, 200), (0.03, 300), (0.04, 50))]
    bucket = make_bucket("K0", (0,), legs)
    assert bucket.half_spread_p75 == pytest.approx(0.0325)
    assert bucket.depth["bid_lots_median"] == pytest.approx(1.5)
    assert bucket.depth["share_one_lot_both_sides"] == pytest.approx(0.75)


def test_history_legs_use_the_snapshots_tercile_bounds():
    model = SpreadModel([quoted(steps, c) for steps in (0, 1, 2) for c in range(90)])
    low, high = model.bounds
    assert tercile(low, model.bounds) == 0 and tercile(low + 0.01, model.bounds) == 1
    assert tercile(high + 1, model.bounds) == 2
    assert model.bucket(-3, 0).moneyness == "2-3 steps" and model.bucket(-1, 0).moneyness == "1 step"
    with pytest.raises(ValueError):
        SpreadModel([])


def test_icc_of_identical_within_cluster_values_is_one_and_of_identical_means_is_minus_one():
    assert icc_anova([[1.0, 1.0], [3.0, 3.0]]) == pytest.approx(1.0)
    assert icc_anova([[1.0, 3.0], [1.0, 3.0]]) == pytest.approx(-1.0)
    assert icc_anova([[1.0, 2.0]]) is None  # one cluster
    assert icc_anova([[1.0], [2.0]]) is None  # no within-cluster degrees of freedom
    assert icc_anova([]) is None


def test_kish_count_and_bootstrap_are_deterministic():
    assert kish_count([2, 1], 1.0) == pytest.approx(2.0)
    assert kish_count([2, 1], None) == 3 and kish_count([2, 1], -0.5) == 3
    groups = [[0.1, 0.12], [0.5, 0.45], [0.2, 0.3], [0.9, 1.0]]
    first = bootstrap_interval(groups)
    assert first == bootstrap_interval(groups) and first[0] <= first[1]
    assert bootstrap_interval([[1.0]]) == (None, None)


def test_cluster_is_sector_by_iso_week_with_unknown_for_missing_sectors():
    assert cluster_key("IT", date(2024, 12, 30)) == ("IT", 2025, 1)
    assert cluster_key(None, date(2024, 10, 16)) == ("unknown", 2024, 42)


def summary(day, close, expiry=date(2021, 2, 25)):
    return DaySummary(day, {"ABC": [Future(expiry, close, close, 10, 1, 1, None)]}, frozenset({"ABC"}))


def test_event_move_is_read_only_for_2019_to_2021():
    event = Event("ABC", date(2021, 2, 1), date(2021, 1, 29), date(2021, 2, 2), None)
    m = market_adjusted_move(event, summary(event.entry, 100.0), summary(event.reaction, 110.0), 1000.0, 1000.0)
    assert m == pytest.approx(0.0953, abs=1e-4)
    late = Event("ABC", date(2022, 2, 1), date(2022, 1, 31), date(2022, 2, 2), None)
    with pytest.raises(OutsideCorrelationYears):
        market_adjusted_move(late, summary(late.entry, 100.0), summary(late.reaction, 110.0), 1000.0, 1000.0)


def test_within_week_correlation_reports_both_iccs_and_kish():
    moves = [(("IT", 2020, 5), 0.05), (("IT", 2020, 5), 0.06), (("FIN", 2020, 5), -0.04), (("FIN", 2020, 5), -0.03)]
    result = within_week_correlation(moves)
    assert result.events == 4 and result.clusters == 2
    assert result.rho_move > 0.9 and result.rho_abs is not None
    assert within_week_correlation([]).events == 0


def result(name, s1=0.5, s2=0.5, s3=0.5, med=10.0, mean=10.0, per_year=200.0):
    return StructureResult(name, 100, s1, s2, s3, med, mean, clusters_a_year=per_year)


@pytest.mark.parametrize(
    ("structures", "spreads", "answer", "stage"),
    [
        ([result("A", s1=0.24, s2=0.2)], True, NO, "stopped at stage 1 (cap)"),
        ([result("A", s1=0.25, s2=0.249)], True, NO, "stopped at stage 2 (liquidity)"),
        ([result("A")], False, CANNOT, "stopped before stage 3"),
        ([result("A", med=0.0)], True, NO, "stopped at stage 3 (cost wall)"),
        ([result("A", mean=-1.0)], True, NO, "stopped at stage 3 (cost wall)"),
        ([result("A", per_year=129.9)], True, NO, "stopped at stage 4 (clusters)"),
        ([result("A", per_year=130.0)], True, YES, "passed stage 4"),
        ([result("A", s1=0.1, s2=0.1), result("B")], True, YES, "passed stage 4"),
    ],
)
def test_decision_stops_at_the_first_stage_no_structure_passes(structures, spreads, answer, stage):
    decision = decide(structures, spreads)
    assert (decision["answer"], decision["stage"]) == (answer, stage)


def test_yes_below_the_80_percent_power_need_is_labelled_and_first_failures_are_named():
    low = decide([result("A", per_year=130.0)], True)
    assert low["reason"] == "YES under the registered rule; below the 80%-power need"
    assert decide([result("A", per_year=297.0)], True)["reason"] == ""
    structures = [result("A", s1=0.1), result("B", med=-1.0)]
    decide(structures, True)
    assert [s.first_failed for s in structures] == ["cap", "cost wall"]


def test_a_crossed_quote_counts_as_one_sided():
    crossed = quoted(0, 10)
    crossed = type(crossed)(**{**crossed.__dict__, "bid": 10.5, "ask": 10.0})
    bucket = make_bucket("K0", (0,), [quoted(0, 10)] * 3 + [crossed])
    assert bucket.two_sided == 3 and bucket.untradable  # 25% one-sided


def test_passing_clusters_are_split_into_october_to_september_parts():
    from r2study.evaluate import Outcome
    from r2study.stages import Scored, clusters_by_part, part_of

    assert part_of(date(2025, 9, 30)) == "Oct 2024 - Sep 2025" and part_of(date(2025, 10, 1)) == "Oct 2025 - Sep 2026"
    passing = Outcome("S1", fits_without_pads=True, liquid=True, fits_with_pads=True, expected_net=1.0)
    rows = [Scored(passing, date(2024, 10, 16), "IT"), Scored(passing, date(2024, 10, 17), "IT"),
            Scored(passing, date(2025, 10, 16), "IT")]  # fmt: skip
    assert clusters_by_part(rows) == {"Oct 2024 - Sep 2025": 1, "Oct 2025 - Sep 2026": 1}


def test_a_fitting_liquid_event_with_expected_net_at_or_below_zero_adds_no_cluster():
    from r2study.evaluate import Outcome
    from r2study.stages import Scored, score_structure

    fits = dict(fits_without_pads=True, liquid=True, fits_with_pads=True, break_even_edge=0.05, gross_to_cost=1.0)
    rows = [Scored(Outcome("S1", expected_net=0.0, **fits), date(2024, 10, 16), "IT"),
            Scored(Outcome("S1", expected_net=-5.0, **fits), date(2024, 10, 23), "IT"),
            Scored(Outcome("S1", expected_net=1.0, **fits), date(2024, 10, 30), "FIN")]  # fmt: skip
    result = score_structure("S1", rows, (date(2024, 10, 1), date(2025, 9, 30)), None)
    assert result.stage3_share == 1.0 and result.clusters == 1  # only the EN > 0 event's cluster


def test_kish_uses_the_icc_of_absolute_moves_not_signed_moves():
    moves = [(("IT", 2020, 5), 0.05), (("IT", 2020, 5), -0.05), (("FIN", 2020, 5), 0.01), (("FIN", 2020, 5), -0.01)]
    result = within_week_correlation(moves)
    assert result.rho_move != result.rho_abs
    assert result.kish == pytest.approx(kish_count([2, 2], result.rho_abs))


def summary_with(stocks):
    return DaySummary(date(2024, 10, 1), {s: [Future(date(2024, 10, 31), 1, 1, 1, 1, 1, 1)] for s in stocks},
                      frozenset(stocks))  # fmt: skip


def test_stage_0_passes_at_exactly_80_percent_coverage_and_10_percent_lot_unknown():
    from r2study.descriptive import results_date_coverage, stage0
    from r2study.events import Meeting
    from r2study.sessions import Sessions

    days = [date(2024, 10, 1), date(2024, 12, 31), date(2025, 1, 1)]
    stocks = ["A", "B", "C", "D", "E"]
    summaries = {d: summary_with(stocks) for d in days}
    meetings = [Meeting(s, date(2024, 11, 5), "Financial Results") for s in stocks[:4]]
    coverage = results_date_coverage(meetings, summaries, Sessions(days), date(2024, 10, 1))
    assert coverage["share"] == 0.8 and coverage["passes"]  # 4 of 5: exactly 80%
    under = results_date_coverage(meetings[:3], summaries, Sessions(days), date(2024, 10, 1))
    assert not under["passes"]
    assert stage0(coverage, 10, 100)["passes"]  # exactly 10% lot unknown
    assert not stage0(coverage, 11, 100)["passes"]
