"""The idea card's ```factory block (story R1a, criterion 1): a missing or malformed field is refused, named."""

import pytest

from fno.factory.card import G0_FIELDS, CardError, read_card

from .helpers import BLOCK, CARD, write_card


def test_a_valid_block_gives_the_card(tmp_path):
    card = read_card(tmp_path, write_card(tmp_path))
    assert (card.idea_id, card.version, card.trial_id, card.experiment) == ("X1", 1, "3", "x1-test")
    assert (card.description, card.question, card.hypothesis, card.measurement) == (
        "X1: a planted idea", "planted-question", True, False,
    )  # fmt: skip
    assert card.path == CARD


@pytest.mark.parametrize("field", G0_FIELDS)
def test_a_missing_field_is_named(tmp_path, field):
    block = "".join(line + "\n" for line in BLOCK.splitlines() if not line.startswith(f"{field}:"))
    with pytest.raises(CardError, match=f"field '{field}' is missing"):
        read_card(tmp_path, write_card(tmp_path, block))


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        ("hypothesis: yes", "hypothesis: maybe", "field 'hypothesis' must be yes or no"),
        ("trial: 3", "trial: 0", "field 'trial' must be a whole number"),
        ("version: 1", "version: 1.5", "field 'version' must be a whole number"),
        ("question: planted-question", "question: Planted Question", "field 'question' must be lower-case"),
        ("id: X1", "id: X2", "field 'id' is 'X2', the file name says 'X1'"),
        ("measurement: no", "measurement: no\nstrike: 1", "unknown field 'strike'"),
        ("version: 1", "version: [1", "not valid YAML"),
    ],
)
def test_a_malformed_field_is_named(tmp_path, old, new, message):
    with pytest.raises(CardError, match=message):
        read_card(tmp_path, write_card(tmp_path, BLOCK.replace(old, new)))


def test_a_card_needs_exactly_one_block(tmp_path):
    path = write_card(tmp_path)
    card = tmp_path / path
    card.write_text(card.read_text().replace("```factory", "```yaml"))
    with pytest.raises(CardError, match="exactly one ```factory block, found 0"):
        read_card(tmp_path, path)
    card.write_text(card.read_text().replace("```yaml", "```factory") * 2)
    with pytest.raises(CardError, match="found 2"):
        read_card(tmp_path, path)
