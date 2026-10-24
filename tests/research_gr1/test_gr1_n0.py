"""GR1 protocol section 11: N0-A by hand (the 09:15 price as centre, implied's deviations at sqrt(0.607), the outcome
against the 09:15 price), the same target as N1, the seal by the N0 issue day, N0-C's two conditioners known at
09:15, and the rule: N0-B and N0-C against N0-A on 2024, N0-A carried when neither is eligible and better."""

import math
from datetime import date

import pytest
from gr1study.n0 import REMAINING_SHARE, n0_candidates, n0_pairs, n0_study
from gr1study.rows import Row

from tests.research_gr1.gr1_fakes import context, rows

Q = (-0.02, -0.01, 0.002, 0.012, 0.022)


def n1(day, target, outcome=0.004, s_ref=22_000.0):
    return Row("NIFTY", day, "N1", target, s_ref, Q, outcome)


def test_n0_a_by_hand_on_the_same_target():
    row = n1(date(2024, 3, 5), date(2024, 3, 6))
    ((n0, same),) = n0_pairs([row], {date(2024, 3, 6): 22_110.0}, final_open=False)
    root = math.sqrt(REMAINING_SHARE)
    assert same is row and n0.day == n0.target_day == date(2024, 3, 6) and n0.s_ref == 22_110.0
    assert n0.quantiles == pytest.approx(tuple(root * (q - 0.002) for q in Q)) and n0.quantiles[2] == 0.0
    close = 22_000.0 * math.exp(0.004)
    assert n0.outcome == pytest.approx(math.log(close / 22_110.0))


def test_n0_is_sealed_by_its_own_day_and_needs_a_09_15_price():
    late = n1(date(2024, 12, 31), date(2025, 1, 1))  # N1 issued in 2024, N0 issued on 1 Jan 2025: final
    opens = {date(2025, 1, 1): 22_000.0}
    assert n0_pairs([late], opens, final_open=False) == []
    assert len(n0_pairs([late], opens, final_open=True)) == 1
    assert n0_pairs([n1(date(2024, 3, 5), date(2024, 3, 6))], {}, final_open=False) == []
    banknifty = Row("BANKNIFTY", date(2024, 3, 5), "N1", date(2024, 3, 6), 50_000.0, Q, 0.0)
    assert n0_pairs([banknifty], {date(2024, 3, 6): 50_000.0}, final_open=False) == []


def test_n0_c_reads_the_gap_and_the_09_15_sp500_move_and_drops_a_day_without_them():
    day = date(2024, 3, 6)
    cands = n0_candidates({day: -0.01}, lambda d: 0.012 if d == day else None)
    (row,) = rows(day, day)
    assert cands["N0-C"].features(row, context()) == [1.0, 0.01, 0.012]
    (other,) = rows(date(2024, 3, 7), date(2024, 3, 7))
    assert cands["N0-C"].features(other, context()) is None and cands["N0-B"].features(other, context()) == [1.0]


def pairs(first, last, seed, true_sd):
    found = []
    for r in rows(first, last, seed=seed, implied_sd=0.01, true_sd=true_sd):
        found.append((r, r))
    return found


def test_the_rule_carries_n0_a_unless_a_variant_is_eligible_and_better():
    cands = n0_candidates({}, lambda d: None)
    wide = {"train": pairs(date(2022, 1, 1), date(2023, 12, 31), 1, 0.008),
            "select": pairs(date(2024, 1, 1), date(2024, 12, 31), 2, 0.008)}  # fmt: skip
    assert n0_study(wide, context(), cands)["winner"] == "N0-B"  # one scale fixes a too-wide N0-A
    right = {"train": pairs(date(2022, 1, 1), date(2023, 12, 31), 1, 0.01),
             "select": pairs(date(2024, 1, 1), date(2024, 12, 31), 2, 0.02)}  # fmt: skip
    assert n0_study(right, context(), cands)["winner"] == "N0-A"  # 2024 far wider than train: nothing eligible
