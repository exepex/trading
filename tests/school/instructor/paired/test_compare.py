"""Part d's entry point (story MS-INS): one driver against each control, both measures, each pair at its own batch."""

from pathlib import Path

from fno.school.drivers.cards import CARDS_FOLDER, load_cards
from fno.school.instructor.contracts import Measure
from fno.school.instructor.paired.compare import compare
from tests.school.instructor.builders import RULES
from tests.school.instructor.paired.test_series import CONTROL, DRIVER

CARDS = load_cards(Path(__file__).resolve().parents[4] / CARDS_FOLDER)


def test_each_control_and_measure_gets_its_row_at_the_pairs_batch():
    slots = {"CS1@1": DRIVER, "RC1@1": CONTROL, "N0@1": {}}
    common = {("CS1@1", "RC1@1"): set(DRIVER)}
    rows = compare(CARDS["CS1"], (CARDS["RC1"], CARDS["N0"]), CARDS.values(), slots, common, RULES)
    assert [(r.control_id, r.measure, r.batch, r.sessions) for r in rows] == [
        ("RC1@1", Measure.PER_OPPORTUNITY, 23, 3),
        ("RC1@1", Measure.EXECUTED, 23, 3),
    ]  # N0: no common day, no row


def test_a_driver_with_no_slots_yet_is_paired_on_unavailable_days_not_a_crash():
    common = {("DB1@1", "RC1@1"): set(CONTROL)}
    rows = compare(CARDS["DB1"], (CARDS["RC1"],), CARDS.values(), {"RC1@1": CONTROL}, common, RULES)
    assert rows[0].sessions == 0 and rows[0].unavailable == 6


def test_a_seller_shaped_drivers_rows_carry_its_false_rate_and_a_buyers_do_not():
    slots = {"CS1@1": DRIVER, "DB1@1": DRIVER, "RC1@1": CONTROL}
    common = {("CS1@1", "RC1@1"): set(DRIVER), ("DB1@1", "RC1@1"): set(DRIVER)}
    seller = compare(CARDS["CS1"], (CARDS["RC1"],), CARDS.values(), slots, common, RULES)
    buyer = compare(CARDS["DB1"], (CARDS["RC1"],), CARDS.values(), slots, common, RULES)
    assert all("falsely look positive" in r.note for r in seller)
    assert not any("falsely" in r.note for r in buyer)


SELLERS = {"CS1", "WS1", "PS2", "PS3", "PS4", "PS5", "KL1", "REF", "RC1"}


def test_each_cards_payoff_shape():
    from fno.school.instructor.paired.shapes import is_seller

    assert {code for code, card in CARDS.items() if is_seller(card)} == SELLERS


def test_a_pair_present_with_an_empty_common_set_gives_no_row():
    """Judge 516 minor: the key is there, its set is empty: still no row (criterion 9)."""
    slots = {"CS1@1": DRIVER, "RC1@1": CONTROL}
    assert compare(CARDS["CS1"], (CARDS["RC1"],), CARDS.values(), slots, {("CS1@1", "RC1@1"): set()}, RULES) == ()
