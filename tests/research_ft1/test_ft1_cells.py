"""FT1 criteria 5 (cells), 6 (bootstrap) and 8 (splits): "insufficient data" over 10% left out, "too few days" under
30, the figures, the seeded intervals, the split bands, the paired difference and the flip shares by expiry."""

from datetime import date, time, timedelta

import numpy as np
import pytest
from ft1study.bootstrap import BLOCKS, generator, mean_interval, ratio_interval, stationary_indices
from ft1study.cells import INSUFFICIENT, OK, CellKey, flip_shares, main_cell, paired
from ft1study.figures import TOO_FEW, splits
from ft1study.observe import STALE, Observation

KEY = CellKey("SF", 200, time(15, 0), 60)
START = date(2025, 1, 1)


def obs(i: int, c: float | None, **fields) -> Observation:
    base = dict(family="SF", width=200, decision=time(15, 0), reaction=60, day=START + timedelta(days=i),
                expiry=date(2025, 1 + i // 20, 28) if i < 220 else date(2025, 12, 30), sessions_to_expiry=20,
                nights=1, e4_snapshot=False, c=c, risk=None if c is None else 200.0,
                excluded=STALE if c is None else None)  # fmt: skip
    return Observation(**(base | fields))


def series(n: int, left_out: int = 0) -> list[Observation]:
    return [obs(i, float((i * 7) % 41 - 15)) for i in range(n)] + [obs(n + i, None) for i in range(left_out)]


def test_more_than_10_percent_left_out_is_insufficient_data_and_under_30_days_too_few():
    assert main_cell(KEY, series(89, 11), 100, 65)["status"] == INSUFFICIENT
    ok = main_cell(KEY, series(90, 10), 100, 65)
    assert ok["status"] == OK and ok["left_out"] == {STALE: 10} and ok["n"] == 90
    short = main_cell(KEY, series(29), 29, 65)
    assert short["status"] == TOO_FEW and "mean_abs_c" not in short


def test_the_figures_of_a_cell():
    found = main_cell(KEY, series(100), 100, 65)
    values = np.array([float((i * 7) % 41 - 15) for i in range(100)])
    assert found["p10_c"] == pytest.approx(np.percentile(values, 10)) and found["p50_c"] == np.median(values)
    assert found["mean_abs_c"] == pytest.approx(np.abs(values).mean())
    assert found["share_above"]["10%"] == pytest.approx(np.mean(values > 20.0))  # strictly above 10% of 200
    assert found["share_above"]["5%"] == pytest.approx(np.mean(values > 10.0))
    assert found["rupees"]["mean_abs_c"] == pytest.approx(found["mean_abs_c"] * 65)
    assert set(found["mean_abs_c_interval"]) == set(BLOCKS)


def test_the_same_run_twice_gives_the_same_intervals_and_each_cell_its_own_stream():
    rows = series(100)
    assert main_cell(KEY, rows, 100, 65) == main_cell(KEY, rows, 100, 65)
    values = [abs(o.c) for o in rows]
    assert mean_interval(values, 5, "a") == mean_interval(values, 5, "a") != mean_interval(values, 5, "b")
    low, high = mean_interval(values, 5, "a")
    assert low < np.mean(values) < high


def test_the_stationary_bootstrap_draws_blocks_of_the_given_mean_length():
    picks = stationary_indices(400, 5, generator("x"), resamples=200)
    breaks = np.mean(picks[:, 1:] != (picks[:, :-1] + 1) % 400)
    assert picks.shape == (200, 400) and breaks == pytest.approx(1 / 5, abs=0.01)


def test_the_cluster_interval_resamples_whole_clusters():
    assert ratio_interval([1, 1, 1], [2, 2, 2], "same")[:2] == (0.5, 0.5)  # identical clusters: no spread
    low, high, dropped = ratio_interval([0, 3], [1, 3], "two")
    assert (low, high) == (0.0, 1.0) and dropped == 0


@pytest.mark.parametrize(("fields", "split", "band"), [
    ({"nights": 0}, "nights", "0"), ({"nights": 2}, "nights", "2"), ({"nights": 3}, "nights", "3 or more"),
    ({"nights": 4}, "nights", "3 or more"), ({"gap": 0.0049}, "gap band", "below 0.5%"),
    ({"gap": 0.005}, "gap band", "0.5-1%"), ({"gap": 0.01}, "gap band", "1% and more"),
    ({"gap": None}, "gap band", "gap unknown"), ({"vix": 12.99}, "VIX band", "below 13"),
    ({"vix": 13.0}, "VIX band", "13-18"), ({"vix": 18.0}, "VIX band", "13-18"),
    ({"vix": 18.01}, "VIX band", "above 18"), ({"sessions_to_expiry": 15}, "sessions to expiry", "8-15"),
    ({"sessions_to_expiry": 16}, "sessions to expiry", "16-25"),
    ({"sessions_to_expiry": 26}, "sessions to expiry", "26 and more"),
])  # fmt: skip
def test_fixture_days_land_in_the_right_split_band(fields, split, band):
    found = splits([obs(i, 5.0, **fields) for i in range(30)])[split]
    assert list(found) == [band] and found[band]["n"] == 30


def test_a_split_band_under_30_days_prints_too_few_days():
    rows = [obs(i, 5.0, vix=12.0) for i in range(29)] + [obs(29 + i, 6.0, vix=20.0) for i in range(30)]
    found = splits(rows)["VIX band"]
    assert found["below 13"] == {"n": 29, "status": TOO_FEW} and found["above 18"]["mean_abs_c"] == 6.0


def test_the_paired_difference_uses_only_days_both_paths_have():
    late = [obs(i, 10.0) for i in range(40)]
    early = [obs(i, 4.0 if i % 2 else -3.0, decision=time(14, 0)) for i in range(35)]
    cells = [main_cell(KEY, late, 40, 65), main_cell(CellKey("SF", 200, time(14, 0), 60), early, 35, 65)]
    found = paired(*cells, late, early, "SF")
    assert found["n"] == 35 and found["mean_d"] == pytest.approx(np.mean([6.0 if i % 2 else 10.0 for i in range(35)]))
    blocked = paired({"status": INSUFFICIENT}, cells[1], late, early, "SF")
    assert blocked["status"] == INSUFFICIENT and "mean_d" not in blocked


def test_flip_shares_pool_by_expiry_and_carry_no_win_count_or_pnl():
    rows = [obs(i, 1.0, pnl_decision=100.0 if i % 3 else -50.0, pnl_fill=-1.0 if i % 4 == 0 else 20.0)
            for i in range(60)]  # fmt: skip
    found = flip_shares(main_cell(KEY, rows, 60, 65), rows)
    wins = [i for i in range(60) if i % 3]
    assert found["bad_flip_share"]["share"] == pytest.approx(sum(i % 4 == 0 for i in wins) / len(wins))
    losses = [i for i in range(60) if not i % 3]
    assert found["good_flip_share"]["share"] == pytest.approx(sum(i % 4 != 0 for i in losses) / len(losses))
    assert found["expiries"] == 3 and found["not_settled"] == 0
    assert set(found) == {"cell", "status", "expiries", "not_settled", "bad_flip_share", "good_flip_share"}


def test_entries_into_an_unsettled_expiry_are_left_out_of_the_flip_share_and_counted():
    rows = [obs(i, 1.0, pnl_decision=10.0, pnl_fill=10.0) for i in range(40)] + [obs(40 + i, 1.0) for i in range(5)]
    assert flip_shares(main_cell(KEY, rows, 45, 65), rows)["not_settled"] == 5
