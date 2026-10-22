"""Part d's own checks on fakes (story MS-INS, criteria 7-8; orchestrator's rulings and conditions, 22 Oct 2026):
the Gaussian null's false-positive share of the descriptive bound, at the holds the cards hold today (read at test
time, so a card change re-checks the gate), with the upper end of its 95% interval at 10% or less; the skewed seller's
far higher share, which is why v1 shows no Watching (ruling D) and prints that rate on seller rows; a planted edge."""

import math
from pathlib import Path

import pytest

from fno.school.drivers.cards import CARDS_FOLDER, load_cards
from fno.school.instructor.paired.holds import hold_sessions
from fno.school.instructor.paired.nulls import (
    Market,
    SellerShape,
    seller_slots,
    share_positive,
    share_watching,
    wilson_upper,
)
from fno.school.instructor.thresholds import BATCH_HOLD_MULTIPLE, MIN_BATCH, MIN_BATCHES, SELLER_FALSE_POSITIVE_PCT

CARDS = load_cards(Path(__file__).resolve().parents[4] / CARDS_FOLDER)
HOLDS = sorted({h for c in CARDS.values() if (h := hold_sessions(c, CARDS.values()))})


@pytest.mark.parametrize("hold", HOLDS)
def test_the_gaussian_null_passes_at_every_hold_the_cards_hold_today(hold):
    """At the first session count with a bound (two batches) and at twice that."""
    batch = max(math.ceil(BATCH_HOLD_MULTIPLE * hold), MIN_BATCH)
    for sessions in (MIN_BATCHES * batch, 2 * MIN_BATCHES * batch):
        share = share_watching(0.0, sessions, range(2000), batch, Market(hold=hold))
        assert wilson_upper(share, 2000) <= 0.10, (hold, sessions, share)


def test_the_skewed_seller_null_fails_the_gate_and_stays_under_the_rate_printed_on_seller_rows():
    """The measured worst case (loss chance 10%, hold 10, batch 15, 120 sessions: 18.9%, upper end 20.7%)."""
    share = share_positive(lambda seed: seller_slots(seed, 120, SellerShape(0.1)), range(2000), 15)
    assert wilson_upper(share, 2000) > 0.10 and wilson_upper(share, 2000) <= SELLER_FALSE_POSITIVE_PCT / 100


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
