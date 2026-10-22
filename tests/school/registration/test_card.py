"""Criterion 4 (story MS-P1h): `read_card` accepts the card; the cost block it names is the one in config.yaml."""

import hashlib
import re
from pathlib import Path

from fno.factory.card import read_card
from fno.school.registration.counting import CARD_PATH

ROOT = Path(__file__).resolve().parents[3]
FROZEN_CHARGES_SHA256 = "5177fb366c49ac3b5ba420c34930a0978eefe463a525b24d5bee79982d1e1889"


def test_read_card_accepts_the_card_as_a_measurement():
    card = read_card(ROOT, CARD_PATH)
    assert (card.idea_id, card.version, card.measurement, card.hypothesis) == ("CARD_P1", 1, True, False)


def test_the_card_names_the_charges_block_that_config_yaml_holds():
    block = re.search(r"^charges:\n(?:  .*\n)+", (ROOT / "config.yaml").read_text(), re.M)
    assert hashlib.sha256(block.group(0).encode()).hexdigest() == FROZEN_CHARGES_SHA256
    assert FROZEN_CHARGES_SHA256 in (ROOT / CARD_PATH).read_text()


def test_the_card_leaves_the_first_counted_session_unset_and_names_no_driver_sha_yet():
    text = (ROOT / CARD_PATH).read_text()
    assert "**Not set.**" in text and "school.first_counted" in text
