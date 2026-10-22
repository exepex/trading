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
    assert (card.idea_id, card.version, card.measurement, card.hypothesis) == ("CARD_P1", 2, True, False)


def test_the_charges_block_in_force_matches_the_cost_hash_frozen_in_the_current_card_version():
    """A charge change fails here until a new card version is cut; versions apply forward only, so no decision made
    under an earlier version is touched (judge 480, addendum 1)."""
    block = CHARGES.search((ROOT / CONFIG_PATH).read_text())
    assert hashlib.sha256(block.group(0).encode()).hexdigest() in CARD, "cut a new card version for the new charges"


def test_the_cost_block_named_by_the_card_is_the_one_config_held_at_the_cards_last_commit():
    git = Git(ROOT)
    if git.is_shallow():
        pytest.skip("a shallow clone cannot show the card's commit")
    commits = git.commits_touching(CARD_PATH)
    if not commits:
        pytest.skip("the card is not committed yet")
    block = CHARGES.search(git.committed_text(CONFIG_PATH, commits[-1]))
    assert hashlib.sha256(block.group(0).encode()).hexdigest() in git.committed_text(CARD_PATH, commits[-1])


FROZEN_WORDS = (
    "24 variants (trials 71-98)",
    "does not prove no edge exists",
    "10 strike steps",
    "DEFAULT_BAND_STEPS",
    "impossible_keys",
    "revision 7",
    "BANKNIFTY-M)",
    "NIFTY-M)",
    "first_counted_not_frozen_before",
    "new card version",
    "ImpossiblePriceLaw",
    "SEBI 2024/132",
    "k = 2.1",
    "A14c",
    "margin_room",
    "impossible_leg_price",
)


def test_the_card_freezes_the_pieces_judge_480_named():
    for words in FROZEN_WORDS:
        assert words in CARD, words
    assert "98 counted trials" not in CARD


def test_the_card_says_how_the_first_counted_session_is_set_and_proved():
    assert "school.first_counted" in CARD and "strictly before the decision's commit" in CARD


def test_the_version_component_name_part_e_must_use_is_pinned():
    assert CARD_COMPONENT == "card_sha256" and f"`{CARD_COMPONENT}`" in CARD


def test_the_cards_band_is_the_quality_gates_constant():
    band = pytest.importorskip("fno.school.quality.band", reason="part b (MS-P1b) is not on this branch yet")
    assert f"{band.DEFAULT_BAND_STEPS} strike steps" in CARD, "the card must freeze exactly part b's band"


def test_the_law_the_card_names_for_traded_legs_exists_in_part_d():
    quote_laws = pytest.importorskip("fno.school.safety.quote_laws", reason="part d (MS-P1d) is not on this branch yet")
    assert hasattr(quote_laws, "ImpossiblePriceLaw") and "ImpossiblePriceLaw" in CARD
