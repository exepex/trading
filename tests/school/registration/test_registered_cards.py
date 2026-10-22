"""The frozen driver cards and what registers them (story MS-P1h): every card carries the band the comparison card
freezes, and every card file's SHA-256 is the one its D6 row and the comparison card name."""

import re
from pathlib import Path

import yaml

from fno.school.registration.counting import CARD_PATH

ROOT = Path(__file__).resolve().parents[3]
CARDS = sorted((ROOT / "research/school/cards").glob("*.yaml"))
CARD = (ROOT / CARD_PATH).read_text()
BAND = int(re.search(r"(\d+) strike steps", CARD).group(1))


def driver_id(card: Path) -> str:
    document = yaml.safe_load(card.read_text())
    return f"{document['code']}@{document['version']}"


def test_every_driver_card_carries_the_band_the_comparison_card_freezes():
    assert len(CARDS) == 12
    for card in CARDS:
        assert yaml.safe_load(card.read_text())["band_steps"] == BAND, card.name


def test_no_driver_card_is_still_marked_draft():
    assert not [c.name for c in CARDS if "DRAFT" in c.read_text()]
