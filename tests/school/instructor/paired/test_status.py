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
from fno.school.instructor.paired.status import DESCRIPTIVE, batch_bound, paired_row, status
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


LADDER = [(0, MapStatus.EXPLORATORY), (29, MapStatus.EXPLORATORY), (30, MapStatus.NOT_ESTABLISHED),
          (500, MapStatus.NOT_ESTABLISHED)]  # fmt: skip


@pytest.mark.parametrize("sessions, expected", LADDER)
def test_the_v1_ladder_is_exploratory_then_not_established(sessions, expected):
    assert status(sessions) == expected


def test_v1_never_assigns_watching_even_on_a_clearly_positive_series():
    """Ruling D: the bound is shown, labelled descriptive, and never turned into Watching."""
    row = paired_row("CS1@1", "N0@1", Measure.PER_OPPORTUNITY, series([0.3, 0.5] * 30), 10, RULES)
    assert row.bound > 0 and row.status == MapStatus.NOT_ESTABLISHED and row.note.startswith(DESCRIPTIVE)


def test_no_v1_module_assigns_watching():
    sources = (ROOT / "fno" / "school" / "instructor").rglob("*.py")
    assigning = [p.name for p in sources if "MapStatus.WATCHING" in p.read_text(encoding="utf-8")]
    assert assigning == ["contracts.py"]  # only the type's own guard names it


def test_a_row_says_in_words_when_there_is_no_bound_and_when_its_shape_can_mislead():
    row = paired_row("REF@1", "N0@1", Measure.PER_OPPORTUNITY, series([0.5] * 30), 39, RULES, seller=True)
    assert (row.status, row.bound) == (MapStatus.NOT_ESTABLISHED, None)
    assert "no bound before 78 sessions" in row.note and "falsely look positive up to 21%" in row.note
    short = paired_row("DB1@1", "N0@1", Measure.PER_OPPORTUNITY, series([0.5] * 29), 15, RULES)
    assert short.status == MapStatus.EXPLORATORY and "no bound before 30 sessions" in short.note
    assert "falsely" not in short.note  # a debit buyer is not seller-shaped
    empty = paired_row("REF@1", "N0@1", Measure.PER_OPPORTUNITY, series([]), 39, RULES)
    assert (empty.sessions, empty.mean, empty.status, empty.note) == (0, None, MapStatus.EXPLORATORY, DESCRIPTIVE)


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
