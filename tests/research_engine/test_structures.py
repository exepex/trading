"""Story B2 criterion 6 (strikes): equal-distance ties and unlisted wings."""

from fno.constants import OPTION_CALL as CE
from fno.constants import OPTION_PUT as PE
from fno.research_engine.structures import BOUGHT, SOLD, LongIronFly, ShortCondor, ShortIronFly, nearest_strike


def chain(strikes):
    return frozenset((k, kind) for k in strikes for kind in (CE, PE))


def test_an_atm_tie_takes_the_lower_strike():
    legs = ShortIronFly().legs(chain([23700.0 + 50 * i for i in range(13)]), 24025.0, 300)
    assert [(leg.strike, leg.kind, leg.side) for leg in legs] == [
        (24000, CE, SOLD), (24000, PE, SOLD), (24300, CE, BOUGHT), (23700, PE, BOUGHT)
    ]  # fmt: skip
    assert LongIronFly().legs(chain([24000.0, 24050.0, 24100.0, 23950.0]), 24025.0, 50)[0].strike == 24000


def test_a_short_out_of_the_money_tie_takes_the_strike_farther_from_spot():
    """Spot 25000: the call target 25500 is halfway between 25450 and 25550 (takes 25550), the put target 24500 halfway
    between 24450 and 24550 (takes 24450)."""
    strikes = [24150.0, 24450.0, 24550.0, 25000.0, 25450.0, 25550.0, 25850.0]
    legs = ShortCondor().legs(chain(strikes), 25000.0, 300)
    assert [(leg.strike, leg.kind, leg.side) for leg in legs] == [
        (25550, CE, SOLD), (24450, PE, SOLD), (25850, CE, BOUGHT), (24150, PE, BOUGHT)
    ]  # fmt: skip


def test_nearest_strike_without_a_tie_ignores_the_tie_rule():
    assert nearest_strike([100.0, 150.0], 120.0, tie_higher=True) == 100.0
    assert nearest_strike([100.0, 150.0], 130.0, tie_higher=False) == 150.0


def test_a_wing_not_listed_exactly_makes_the_width_unavailable():
    strikes = [23700.0 + 50 * i for i in range(13)]
    listed = chain(strikes) - {(24300.0, CE)}
    assert ShortIronFly().legs(listed, 24010.0, 300) is None
    assert ShortIronFly().legs(listed, 24010.0, 250) is not None
    assert ShortIronFly().legs(chain([24000.0, 24290.0, 23700.0]), 24010.0, 300) is None  # 24290 is not 24300
    assert ShortIronFly().legs(frozenset(), 24010.0, 300) is None
