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
    rows = compare(CARDS["CS1"], (CARDS["RC1"], CARDS["N0"]), slots, common, RULES)
    assert [(r.control_id, r.measure, r.batch, r.sessions) for r in rows] == [
        ("RC1@1", Measure.PER_OPPORTUNITY, 38, 3), ("RC1@1", Measure.EXECUTED, 38, 3),
        ("N0@1", Measure.PER_OPPORTUNITY, 15, 0), ("N0@1", Measure.EXECUTED, 15, 0)]  # fmt: skip
