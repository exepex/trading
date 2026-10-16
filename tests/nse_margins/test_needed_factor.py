"""Story A14c (owner, 16 Oct 2026, decision 07f62385): a held position's needed factor is the smallest k for which C2c's
stressed margin of its entry parts covers what C2 counts on a later day. On the real BF 200 entered 8 Apr 2020 (NSE's
files; entry scan 57,720.00, NOV 56,910.75, exposure 22,859.72 a lot, 65 units; peak 4 May 2020, 83,969.925) it is
1.7483, which rounds to 1.75 and covers the peak, where the plain ratio of counted margins said 3.5477. For a credit
structure (NOV below 0) it equals that plain ratio."""

import random
from datetime import date
from types import SimpleNamespace

import pytest

from fno.nse_margins.calculator import MarginFigure
from fno.nse_margins.held_rise import FACTOR_PRECISION, HeldRiseTracker, needed_factor
from fno.nse_margins.stress_log import rounded_up
from fno.research_engine.structures import Leg
from fno.risk.margins import MarginParts

BF_200 = MarginParts(57_720.0, 56_910.75, 22_859.72, "BF 200 entered 2020-04-08")
BF_200_PEAK = 83_969.925  # what C2 counted on 4 May 2020


def test_the_april_2020_bf_200_needs_1_75_not_3_55():
    needed = needed_factor(BF_200, BF_200_PEAK)
    assert needed == pytest.approx(1.748339, abs=1e-6)
    assert BF_200_PEAK / BF_200.initial() == pytest.approx(3.5477, abs=1e-4)  # the plain ratio, not used
    assert rounded_up(needed) == 1.75 and BF_200.stressed(1.75) >= BF_200_PEAK  # 84,104 a lot
    assert BF_200.stressed(1.70) < BF_200_PEAK  # response 77's gross measure (1.70) leaves it 3,895 short


@pytest.mark.parametrize(("scan", "nov", "exposure", "later"), [
    (523.25, -5_885.75, 59_793.11, 71_456.0), (9_429.55, -11_306.75, 29_538.53, 40_000.0),
    (126.10, -7_299.50, 78_931.10, 120_000.0),
])  # fmt: skip
def test_for_a_credit_structure_it_equals_the_plain_ratio(scan, nov, exposure, later):
    parts = MarginParts(scan, nov, exposure, "credit")
    assert needed_factor(parts, later) == pytest.approx(later / parts.initial(), abs=2 * FACTOR_PRECISION)


def test_a_margin_at_or_below_the_entry_s_needs_one():
    assert needed_factor(BF_200, BF_200.initial()) == 1.0 and needed_factor(BF_200, 10_000.0) == 1.0


def test_it_is_the_smallest_k_that_covers_on_random_parts():
    """Debits and credits alike: the factor always covers (it is the bisection's upper end) and a factor
    `FACTOR_PRECISION` x 2 smaller never does."""
    rng = random.Random(20261016)
    for _ in range(500):
        parts = MarginParts(rng.uniform(0, 60_000), rng.uniform(-30_000, 60_000), rng.uniform(1, 90_000), "random")
        later = parts.initial() * rng.uniform(1.0, 4.0)
        needed = needed_factor(parts, later)
        assert parts.stressed(needed) >= later
        assert needed == 1.0 or parts.stressed(needed - 2 * FACTOR_PRECISION) < later


class FiguresByDay:
    """A calculator that answers the BF 200's real parts by day (entry 8 Apr, peak 4 May, exit 7 May 2020)."""

    lot_size = 65

    def __init__(self, figures):
        self.figures = figures

    def per_lot(self, span, expiry, legs, day):
        return self.figures[day]


class OneStructure:
    """One bought call (worth 0 or more, so any positive NOV is possible); the real BF 200's legs are below."""

    code = "BF"

    def __init__(self, legs=None):
        self.chosen = legs or (Leg(8800.0, "CE", 1),)

    def legs(self, chain, underlying, width):
        return self.chosen


BF_200_LEGS = (Leg(8800.0, "CE", 1), Leg(8800.0, "PE", 1), Leg(9000.0, "CE", -1), Leg(8600.0, "PE", -1))


def test_the_tracker_records_the_needed_factor_of_a_held_debit():
    entry, peak, exit_day, expiry = date(2020, 4, 8), date(2020, 5, 4), date(2020, 5, 7), date(2020, 5, 28)
    figures = {entry: MarginFigure(BF_200.scan, BF_200.nov, BF_200.exposure),
               peak: MarginFigure(90_000.0, 30_000.0, BF_200_PEAK - 60_000.0),
               exit_day: MarginFigure(60_000.0, 30_000.0, 30_000.0)}  # fmt: skip
    tracker = HeldRiseTracker((OneStructure(),), lambda _: (200.0,), FiguresByDay(figures), lambda d: d.weekday() < 5)
    for day in sorted(figures):
        tracker.feed(day, SimpleNamespace(monthly_expiries=(expiry,), series={expiry: {}}, underlying=8_750.0))
    (held,) = tracker.found.completed
    assert (held.entry, held.exit, held.peak_day) == (entry, exit_day, peak)
    assert held.needed == pytest.approx(1.748339, abs=1e-6) and held.peak_margin == pytest.approx(BF_200_PEAK)


def test_the_real_bf_200_of_april_2020_is_an_impossible_entry_and_is_skipped():
    """Owner, 16 Oct 2026: NSE's file valued that 200-wide long iron fly at 875.55 a unit (NOV 56,910.75 / 65); the
    position can never be worth more than 200, so it is not entered, and it is named."""
    entry, expiry = date(2020, 4, 8), date(2020, 5, 28)
    figures = {entry: MarginFigure(BF_200.scan, BF_200.nov, BF_200.exposure)}
    tracker = HeldRiseTracker((OneStructure(BF_200_LEGS),), lambda _: (200.0,), FiguresByDay(figures),
                              lambda d: d.weekday() < 5)  # fmt: skip
    tracker.feed(entry, SimpleNamespace(monthly_expiries=(expiry,), series={expiry: {}}, underlying=8_750.0))
    assert tracker.open == [] and tracker.found.impossible == [
        "BF 200 2020-04-08: impossible price in NSE's file (875.55 a unit, the position is worth 0 to 200)"
    ]
