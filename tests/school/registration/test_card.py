"""Criterion 4 (story MS-P1h): `read_card` accepts the card; what the card freezes is on the page; the cost block it
names is the one `config.yaml` held when the card was last committed (a later charge change is a new card version,
forward only, so nothing here forces an edit)."""

import hashlib
import re
from pathlib import Path

import pytest

from fno.factory.card import read_card
from fno.research_engine.ledger import Git
from fno.school.registration.counting import CARD_PATH, CONFIG_PATH
from fno.school.registration.wiring import CARD_COMPONENT

ROOT = Path(__file__).resolve().parents[3]
CHARGES = re.compile(r"^charges:\n(?:  .*\n)+", re.M)
CARD = (ROOT / CARD_PATH).read_text()


def test_read_card_accepts_the_card_as_a_measurement():
    card = read_card(ROOT, CARD_PATH)
    assert (card.idea_id, card.version, card.measurement, card.hypothesis) == ("CARD_P1", 1, True, False)


def test_the_cost_block_named_by_the_card_is_the_one_config_held_at_the_cards_last_commit():
    git = Git(ROOT)
    if git.is_shallow():
        pytest.skip("a shallow clone cannot show the card's commit")
    commits = git.commits_touching(CARD_PATH)
    if not commits:
        pytest.skip("the card is not committed yet")
    block = CHARGES.search(git.committed_text(CONFIG_PATH, commits[-1]))
    assert hashlib.sha256(block.group(0).encode()).hexdigest() in git.committed_text(CARD_PATH, commits[-1])


def test_the_card_freezes_the_pieces_judge_480_named():
    for words in ("24 variants (trials 71-98)", "does not prove no edge exists", "25 strike steps", "revision 7",
                  "BANKNIFTY-M)", "NIFTY-M)", "first_counted_not_frozen_before", "new card version"):  # fmt: skip
        assert words in CARD, words
    assert "98 counted trials" not in CARD


def test_the_card_says_how_the_first_counted_session_is_set_and_proved():
    assert "school.first_counted" in CARD and "strictly before the decision's commit" in CARD


def test_the_version_component_name_part_e_must_use_is_pinned():
    assert CARD_COMPONENT == "card_sha256" and f"`{CARD_COMPONENT}`" in CARD
