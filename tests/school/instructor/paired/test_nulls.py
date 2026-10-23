"""Part d's own checks on fakes (story MS-INS, criteria 7-8; orchestrator's rulings and conditions, 22 Oct 2026):
the Gaussian null's false-positive share of the descriptive bound, at the holds the cards hold today (read at test
time, so a card change re-checks the gate), with the upper end of its 95% interval at 10% or less; the skewed seller's
far higher share, which is why v1 shows no Watching (ruling D) and prints that rate on seller rows; a planted edge."""

import csv
import math
from pathlib import Path

import pytest

from fno.school.drivers.cards import CARDS_FOLDER, load_cards
from fno.school.instructor.paired.holds import hold_sessions
from fno.school.instructor.paired.nulls import (
    Market,
    SellerShape,
    seller_cell,
    seller_cells,
    seller_slots,
    share_positive,
    share_watching,
    wilson_upper,
)
from fno.school.instructor.thresholds import BATCH_HOLD_MULTIPLE, MIN_BATCH, MIN_BATCHES, SELLER_FALSE_POSITIVE_PCT

CARDS = load_cards(Path(__file__).resolve().parents[4] / CARDS_FOLDER)
GRID = Path(__file__).resolve().parents[4] / "research" / "school" / "instructor_seller_null.csv"
HOLDS = sorted({h for c in CARDS.values() if (h := hold_sessions(c, CARDS.values()))})


@pytest.mark.parametrize("hold", HOLDS)
def test_the_gaussian_null_passes_at_every_hold_the_cards_hold_today(hold):
    """At the first session count with a bound (two batches) and at twice that."""
    batch = max(math.ceil(BATCH_HOLD_MULTIPLE * hold), MIN_BATCH)
    for sessions in (MIN_BATCHES * batch, 2 * MIN_BATCHES * batch):
        share = share_watching(0.0, sessions, range(2000), batch, Market(hold=hold))
        assert wilson_upper(share, 2000) <= 0.10, (hold, sessions, share)


def test_the_printed_seller_rate_is_the_committed_grids_worst_upper_end_and_the_grid_covers_the_cards():
    """research/school/instructor_seller_null.csv is `tools/ins_seller_null.py`'s seeded output: its cells are the
    grid for the holds the cards hold today, and its worst upper end, rounded up, is the rate seller rows print."""
    rows = list(csv.DictReader(GRID.read_text().splitlines()))
    cells = [(int(r["hold"]), float(r["loss_chance"]), int(r["sessions"]), int(r["batch"])) for r in rows]
    assert cells == seller_cells(HOLDS)
    assert math.ceil(max(float(r["wilson_upper"]) for r in rows) * 100) == SELLER_FALSE_POSITIVE_PCT


def test_the_grids_worst_cell_recomputes_from_the_same_seeded_runs():
    rows = list(csv.DictReader(GRID.read_text().splitlines()))
    worst = max(rows, key=lambda r: float(r["wilson_upper"]))
    cell = (int(worst["hold"]), float(worst["loss_chance"]), int(worst["sessions"]), int(worst["batch"]))
    share, upper = seller_cell(*cell)
    assert (f"{share:.4f}", f"{upper:.4f}") == (worst["share"], worst["wilson_upper"])
    assert math.ceil(upper * 100) == SELLER_FALSE_POSITIVE_PCT


def test_the_round_1_table_cell_measured_with_the_shipped_code():
    """Judge 516: loss chance 10%, hold 10, batch 15, 30 sessions is 22.6% (upper end 24.5%), not 14.9%."""
    share = share_positive(lambda seed: seller_slots(seed, 30, SellerShape(0.1)), range(2000), 15)
    assert share == pytest.approx(0.226, abs=0.0005)


def test_the_rejected_rule_batch_equal_to_hold_fails_the_gate_at_hold_15():
    """Why the batch is 1.5 x the hold: batch = hold leaves neighbouring batches linked by open positions."""
    share = share_watching(0.0, 120, range(2000), 15, Market(hold=15))
    assert wilson_upper(share, 2000) > 0.10


def test_a_planted_edge_of_one_shows_a_positive_bound():
    assert share_watching(1.0, 30, range(500), 15, Market(hold=10)) >= 0.5
    assert share_watching(1.0, 60, range(500), 15, Market(hold=10)) >= 0.95


def test_the_wilson_upper_end():
    """p 0.1, n 2000, z 1.96: centre 0.1 + 3.8416 / 4000 = 0.10096; spread 1.96 x sqrt(0.09 / 2000 + 3.8416 / 16e6)
    = 0.01318; (0.10096 + 0.01318) / 1.00192 = 0.11392."""
    assert wilson_upper(0.1, 2000) == pytest.approx(0.11392, abs=1e-5) and wilson_upper(0.0, 100) > 0
