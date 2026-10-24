"""Part c's frozen card (story MS-INS, criterion 8): the thresholds in `research/school/INSTRUCTOR_V1.md` are the
code's, and each driver's stop comes from its frozen card file."""

import re
from pathlib import Path

import yaml

from fno.school.drivers.cards import CARDS_FOLDER, load_cards
from fno.school.instructor.adapters import CardStops
from fno.school.instructor.thresholds import THRESHOLDS

ROOT = Path(__file__).resolve().parents[4]
CARD = ROOT / "research" / "school" / "INSTRUCTOR_V1.md"


def test_the_card_and_the_code_hold_the_same_thresholds():
    block = re.search(r"```thresholds\n(.*?)```", CARD.read_text(encoding="utf-8"), re.S).group(1)
    assert yaml.safe_load(block) == THRESHOLDS


def test_each_drivers_stop_is_its_cards_loss_multiple():
    cards = load_cards(ROOT / CARDS_FOLDER)
    stops = CardStops(cards.values())
    for card in cards.values():
        expected = card.parameters.get("exit_loss_multiple")
        assert stops.loss_multiple(card.driver_id) == (None if expected is None else float(expected))
    assert stops.loss_multiple("XX@9") is None
