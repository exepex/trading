"""The draft card files load, carry the roles and roads of story 3.2, and build every driver (story MS-P1e)."""

import pytest

from fno.school.constants import DriverRole, RoadCode
from fno.school.drivers.card_params import CardError
from fno.school.drivers.cards import load_card
from fno.school.drivers.wiring import build_drivers
from tests.school.drivers import builders as b

MONTHLIES = {RoadCode.NIFTY_MONTHLY, RoadCode.BANKNIFTY_MONTHLY, RoadCode.FINNIFTY_MONTHLY, RoadCode.MIDCPNIFTY_MONTHLY}


def test_the_twelve_cards_of_the_story_load_with_a_hash_each():
    cards = b.cards()
    assert sorted(cards) == sorted(["CS1", "DB1", "DR1", "WS1", "PS2", "PS3", "PS4", "PS5", "KL1", "REF", "RC1", "N0"])
    assert all(len(c.card_sha256) == 64 and c.version == "1" for c in cards.values())
    assert len({c.card_sha256 for c in cards.values()}) == 12


def test_roles_and_roads_follow_the_story_table():
    cards = b.cards()
    for code in ("CS1", "DB1", "DR1", "PS2", "PS3", "PS4"):
        assert cards[code].role == DriverRole.RULE and set(cards[code].roads) == MONTHLIES
    assert cards["WS1"].roads == (RoadCode.NIFTY_WEEKLY,)
    assert {cards[c].role for c in ("REF", "RC1", "N0")} == {DriverRole.CONTROL}
    assert all(len(cards[c].roads) == 5 for c in ("REF", "RC1", "N0"))
    assert cards["PS5"].role == cards["KL1"].role == DriverRole.MEASUREMENT_ONLY
    assert cards["PS5"].roads == (RoadCode.BANKNIFTY_MONTHLY,) and cards["KL1"].roads == (RoadCode.NIFTY_MONTHLY,)


def test_every_card_builds_its_driver():
    assert sorted(d.card.code for d in b.drivers().values()) == sorted(b.cards())


def test_a_card_with_a_missing_number_is_refused_naming_it(tmp_path):
    text = (b.ROOT / "research/school/cards/CS1_v1.yaml").read_text().replace("  dte_min: 20\n", "")
    path = tmp_path / "CS1_v1.yaml"
    path.write_text(text)
    card = load_card(path)
    with pytest.raises(CardError, match="dte_min"):
        build_drivers({"CS1": card}, b.BUILDER, b.CALENDAR)


def test_a_card_with_an_unknown_key_or_wrong_file_name_is_refused(tmp_path):
    text = (b.ROOT / "research/school/cards/N0_v1.yaml").read_text()
    (tmp_path / "N0_v1.yaml").write_text(text + "extra: 1\n")
    with pytest.raises(CardError, match="exactly"):
        load_card(tmp_path / "N0_v1.yaml")
    (tmp_path / "wrong.yaml").write_text(text)
    with pytest.raises(CardError, match="file name"):
        load_card(tmp_path / "wrong.yaml")
