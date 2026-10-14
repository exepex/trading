"""Story S2: the daily pairs and S1's uncertainty criterion by hand. Net per unit of risk is total net / risk-days (the
ratio of the means); a trade adds risk on the days it is held at the close; operating costs land on their month's
last session; the block bootstrap is reproducible and exact on a series with one ratio."""

from datetime import date

from fno.scoreboard.book_trades import ScoredTrade
from fno.scoreboard.daily_values import TradeDay
from fno.scoreboard.series import DailySeries, costs_by_session, daily_series
from fno.scoreboard.uncertainty import BLOCK_DAYS, MIN_DAYS_SINCE_START, lower_bound, uncertainty
from tests.scoreboard.builders import facts

D1, D2, D3 = date(2026, 10, 29), date(2026, 10, 30), date(2026, 11, 2)


def scored(values, opened, closed, max_loss):
    days = tuple(TradeDay(d, v) for d, v in values)
    return ScoredTrade("t", "s-v1", opened, closed, True, None, facts(max_loss=max_loss), days)


def test_net_per_unit_of_risk_is_total_net_over_risk_days():
    trade = scored([(D1, -100.0), (D2, 400.0), (D3, 900.0)], D1, D3, 5000.0)
    series = daily_series([trade], {D2: 50.0}, [D1, D2, D3])
    assert series.net == (-100.0, 450.0, 500.0)  # D2: +500 from the trade, -50 operating costs
    assert series.risk == (5000.0, 5000.0, 0.0)  # held at the close of D1 and D2; closed on D3
    assert series.net_per_risk == 850.0 / 10_000.0


def test_operating_costs_land_on_their_month_s_last_session_in_the_period():
    assert costs_by_session({"2026-10": 300.0, "2026-11": 70.0, "2026-09": 5.0}, [D1, D2, D3]) == {D2: 300.0, D3: 70.0}


def test_the_bootstrap_is_reproducible_and_exact_when_every_day_has_one_ratio():
    days = tuple(date(2026, 1, 1).fromordinal(date(2026, 1, 1).toordinal() + i) for i in range(40))
    flat = DailySeries(days, tuple(20.0 for _ in days), tuple(1000.0 for _ in days))
    assert lower_bound(flat, resamples=200) == 0.02
    mixed = DailySeries(days, tuple(float((i * 37) % 11 - 4) for i in range(40)), tuple(100.0 for _ in days))
    assert lower_bound(mixed, resamples=300) == lower_bound(mixed, resamples=300)  # the same seed, the same bound
    assert lower_bound(mixed, resamples=300) < mixed.net_per_risk


def test_no_bound_shorter_than_one_block_and_no_claim_before_the_sample():
    short = DailySeries(tuple(range(BLOCK_DAYS - 1)), (1.0,) * (BLOCK_DAYS - 1), (10.0,) * (BLOCK_DAYS - 1))
    assert lower_bound(short) is None
    judged = uncertainty(short, positions=25, months=6)
    assert (
        not judged.sample_met
        and not judged.claim_allowed
        and f"of {MIN_DAYS_SINCE_START} trading days" in judged.reason
    )


def nearest_rank_bound(series, seed, resamples):
    """The protocol's procedure written out once more, as the test's oracle: moving blocks of BLOCK_DAYS started
    uniformly, cut at the series length, ratio of sums, nearest-rank 5th percentile."""
    import math
    import random

    rng, n, ratios = random.Random(seed), len(series.days), []
    for _ in range(resamples):
        picked = []
        while len(picked) < n:
            start = rng.randrange(n - BLOCK_DAYS + 1)
            picked += list(range(start, start + BLOCK_DAYS))[: n - len(picked)]
        ratios.append(sum(series.net[i] for i in picked) / sum(series.risk[i] for i in picked))
    return sorted(ratios)[math.ceil(0.05 * resamples) - 1]


def test_the_bound_is_the_nearest_rank_fifth_percentile_of_block_resamples():
    days = tuple(range(45))
    series = DailySeries(days, tuple(float((i * 37) % 11 - 4) for i in days), tuple(100.0 + i for i in days))
    assert lower_bound(series, seed=7, resamples=400) == nearest_rank_bound(series, 7, 400)
