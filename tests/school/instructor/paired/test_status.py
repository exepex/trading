"""Part d's bound and status (story MS-INS, criteria 5-6; orchestrator's ruling, 22 Oct 2026): a one-sided 95% t bound
on whole batch means counted back from the last session, Exploratory below 30 sessions, "too few independent batches"
said in words, and each card's frozen hold."""

from datetime import date, timedelta
from pathlib import Path

import pytest

from fno.school.drivers.cards import CARDS_FOLDER, load_cards
from fno.school.instructor.contracts import MapStatus, Measure
from fno.school.instructor.paired.holds import hold_sessions, pair_batch
from fno.school.instructor.paired.series import PairedSeries
from fno.school.instructor.paired.status import TOO_FEW_BATCHES, batch_bound, paired_row, status
from tests.school.instructor.builders import RULES

ROOT = Path(__file__).resolve().parents[4]
CARDS = load_cards(ROOT / CARDS_FOLDER)


def series(values) -> PairedSeries:
    days = tuple(date(2027, 1, 1) + timedelta(days=i) for i in range(len(values)))
    return PairedSeries(days, tuple(values), len(values), 0, 0, 0, 0)


def test_the_hand_computed_bound_on_three_batches():
    """Seven values, batch 2: the first is left out, batch means 0.15, 0.35, 0.25 -> mean 0.25, sd 0.1, k = 3:
    bound = 0.25 - t(2 df) 2.920 x 0.1 / sqrt(3) = 0.25 - 0.16859 = 0.08141."""
    assert batch_bound((9.0, 0.1, 0.2, 0.3, 0.4, 0.2, 0.3), 2) == pytest.approx(0.08141, abs=1e-5)


def test_below_two_whole_batches_there_is_no_bound():
    assert batch_bound((0.1,) * 19, 10) is None and batch_bound((0.1, 0.2) * 10, 10) is not None


@pytest.mark.parametrize("sessions, bound, expected", [
    (29, 1.0, MapStatus.EXPLORATORY), (30, 0.0001, MapStatus.WATCHING), (30, 0.0, MapStatus.NOT_ESTABLISHED),
    (30, None, MapStatus.NOT_ESTABLISHED), (0, None, MapStatus.EXPLORATORY),
])  # fmt: skip
def test_the_status_boundaries(sessions, bound, expected):
    assert status(sessions, bound) == expected


def test_a_row_says_too_few_independent_batches_in_words():
    row = paired_row("REF@1", "N0@1", Measure.PER_OPPORTUNITY, series([0.5] * 30), 38, RULES)
    assert (row.status, row.bound, row.note) == (MapStatus.NOT_ESTABLISHED, None, TOO_FEW_BATCHES)
    short = paired_row("REF@1", "N0@1", Measure.PER_OPPORTUNITY, series([0.5] * 29), 38, RULES)
    assert (short.status, short.note) == (MapStatus.EXPLORATORY, "")
    empty = paired_row("REF@1", "N0@1", Measure.PER_OPPORTUNITY, series([]), 38, RULES)
    assert (empty.sessions, empty.mean, empty.status) == (0, None, MapStatus.EXPLORATORY)


def test_a_clear_positive_series_reads_watching():
    row = paired_row("CS1@1", "N0@1", Measure.PER_OPPORTUNITY, series([0.3, 0.5] * 15), 10, RULES)
    assert row.status == MapStatus.WATCHING and row.bound > 0 and row.mean == pytest.approx(0.4)


@pytest.mark.parametrize("code, hold", [("CS1", 10), ("DB1", 10), ("DR1", 10), ("PS2", 15), ("PS5", 18), ("KL1", 33),
                                        ("REF", 26), ("RC1", 26), ("WS1", 3), ("N0", 0)])  # fmt: skip
def test_each_cards_frozen_hold(code, hold):
    assert hold_sessions(CARDS[code]) == hold


@pytest.mark.parametrize("pair, batch", [(("CS1", "N0"), 15), (("WS1", "N0"), 10), (("CS1", "REF"), 39),
                                         (("PS2", "N0"), 23), (("KL1", "RC1"), 50), (("CS1", "RC1"), 23)])  # fmt: skip
def test_a_pairs_batch_is_one_and_a_half_times_its_longer_hold_and_at_least_ten(pair, batch):
    assert pair_batch(CARDS[pair[0]], CARDS[pair[1]], CARDS.values()) == batch


def test_rc1_holds_as_long_as_its_longest_rule_twin_and_without_twins_its_cycle():
    """RC1 drives every road with a random rule family's structure and exit: PS2-4's 21 days (15 sessions) is the
    longest twin; with no cards given it falls back to the 36-day monthly cycle (26 sessions)."""
    assert hold_sessions(CARDS["RC1"], CARDS.values()) == 15 and hold_sessions(CARDS["RC1"]) == 26
