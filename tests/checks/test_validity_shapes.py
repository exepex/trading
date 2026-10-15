"""Story STR1 criteria 4, 5 and 8 (C4 side): C4 accepts a correct trade of each one- and two-leg structure, its
independent maximum loss equals B2's to the paisa, it refuses every planted naked short leg whatever code it claims
(shape and `bounded_loss`), and a 0 margin passes only for a bought-only structure."""

from pathlib import Path

import pytest

from fno.checks.validity_margin import MarginProblem, stressed_per_lot
from fno.checks.validity_money import ProposedLeg
from fno.checks.validity_settings import MarginSettings
from fno.checks.validity_shapes import shape_problem
from fno.checks.wiring import validity_shapes
from fno.constants import BOOK1_RULES
from fno.research_engine.structures import BOUGHT, SOLD
from tests.checks.validity_builders import CUTOFF, DAY, LOT, check, failed, legs_of, proposer_max_loss
from tests.checks.validity_proposal_builder import one_side_proposal
from tests.checks.validity_sources import FILE_DAY, MARGIN_ROWS, Margins

SHAPES = validity_shapes()
# code -> (legs on the 25,000 ATM strike, width) as STR1 builds them (tests/research_engine/test_one_side.py)
ONE_SIDE = {
    "LC": ([(25_300, "CE", BOUGHT)], 300.0),  # at ATM (width 0) the fixture call costs over the Rs 10,000 cap
    "LP": ([(24_700, "PE", BOUGHT)], 300.0),
    "CDS": ([(25_000, "CE", BOUGHT), (25_200, "CE", SOLD)], 200.0),
    "CCS": ([(25_000, "CE", SOLD), (25_100, "CE", BOUGHT)], 100.0),
    "PDS": ([(25_000, "PE", BOUGHT), (24_800, "PE", SOLD)], 200.0),
    "PCS": ([(25_000, "PE", SOLD), (24_900, "PE", BOUGHT)], 100.0),
}
ROWS = MARGIN_ROWS + [
    {"structure": code, "width": f"{width:g}", "scan_per_lot_rs": "6000.0", "nov_per_lot_rs": "3000.0",
     "exposure_per_lot_rs": "0.0" if code in ("LC", "LP") else "32500.0", "source": "test fixture",
     "as_of": FILE_DAY.isoformat()}
    for code, (_, width) in ONE_SIDE.items()
]  # fmt: skip


def legs(spec):
    return [ProposedLeg(k, kind, side, 100.0) for k, kind, side in spec]


@pytest.mark.parametrize("code", sorted(ONE_SIDE))
def test_a_correct_trade_of_each_one_side_structure_passes_c4(code):
    spec, width = ONE_SIDE[code]
    report = check(one_side_proposal(code, spec, width), margins=Margins(ROWS))
    assert report.ok, [(r.name, r.reason) for r in report.failures]
    loss = next(r for r in report.results if r.name == "max_loss").numbers
    assert loss["difference"] < 0.01  # C4's independent grid equals B2's strike-only model to the paisa


@pytest.mark.parametrize("code", sorted(ONE_SIDE))
def test_each_shape_rule_accepts_its_own_legs_only(code):
    spec, width = ONE_SIDE[code]
    assert shape_problem(SHAPES, code, legs(spec), width) == ""
    others = [other for other in ONE_SIDE if other != code]
    assert all(shape_problem(SHAPES, other, legs(spec), width) for other in others)


WRONG = {
    "debit spread called a credit spread": ("CCS", [(25_000, "CE", BOUGHT), (25_100, "CE", SOLD)], 100.0),
    "spread at another width": ("PCS", [(25_000, "PE", SOLD), (24_900, "PE", BOUGHT)], 200.0),
    "outer leg on the wrong side": ("CDS", [(25_000, "CE", BOUGHT), (24_800, "CE", SOLD)], 200.0),
    "mixed types": ("PDS", [(25_000, "PE", BOUGHT), (24_800, "CE", SOLD)], 200.0),
    "two bought legs": ("CDS", [(25_000, "CE", BOUGHT), (25_200, "CE", BOUGHT)], 200.0),
    "bought put called a call": ("LC", [(25_000, "PE", BOUGHT)], 0.0),
    "three legs": ("CDS", [(25_000, "CE", BOUGHT), (25_200, "CE", SOLD), (25_300, "CE", BOUGHT)], 200.0),
    "spread called a fly": ("SF", [(25_000, "CE", SOLD), (25_100, "CE", BOUGHT)], 100.0),
    "unknown code": ("XS", [(25_000, "CE", BOUGHT)], 0.0),
}


@pytest.mark.parametrize("name", sorted(WRONG))
def test_wrong_legs_fail_the_shape(name):
    code, spec, width = WRONG[name]
    assert shape_problem(SHAPES, code, legs(spec), width)


NAKED = {
    "a short call called LC": ("LC", [(25_000, "CE", SOLD)], 0.0),
    "a short put called PCS": ("PCS", [(25_000, "PE", SOLD)], 100.0),
    "a short call over a bought put called CCS": ("CCS", [(25_000, "CE", SOLD), (24_900, "PE", BOUGHT)], 100.0),
    "a ratio call spread called CDS": ("CDS", [(25_000, "CE", BOUGHT), (25_200, "CE", SOLD), (25_300, "CE", SOLD)],
                                       200.0),
    "a condor without its call wing called SC": ("SC", [(25_500, "CE", SOLD), (24_500, "PE", SOLD),
                                                        (24_400, "PE", BOUGHT)], 100.0),
}  # fmt: skip


@pytest.mark.parametrize("name", sorted(NAKED))
def test_c4_refuses_every_planted_naked_short_leg(name):
    code, spec, width = NAKED[name]
    trade = one_side_proposal(code, spec, width, claimed_max_loss=1.0)
    report = check(trade, margins=Margins(ROWS))
    assert {"bounded_loss", "shape"} <= failed(report)
    assert not report.ok


def test_bounded_loss_is_checked_from_the_legs_whatever_the_code_and_shape_rules():
    """Even with no shape rule at all (an empty table), the naked short fails `bounded_loss` on its own."""
    code, spec, width = NAKED["a short call called LC"]
    report = check(one_side_proposal(code, spec, width, claimed_max_loss=1.0), margins=Margins(ROWS))
    bounded = next(r for r in report.results if r.name == "bounded_loss")
    assert not bounded.ok and "CE" in bounded.reason


SETTINGS = MarginSettings(Path("margins.csv"), 7, "multiplier", 1.45, "test", FILE_DAY, 30)


def zero_row(code: str, width: float, exposure: float = 0.0) -> dict:
    return {"structure": code, "width": f"{width:g}", "scan_per_lot_rs": "5000.0", "nov_per_lot_rs": "13000.0",
            "exposure_per_lot_rs": f"{exposure}", "source": "test", "as_of": FILE_DAY.isoformat()}  # fmt: skip


@pytest.mark.parametrize("code", ["LC", "LP"])
def test_a_bought_only_structure_may_need_no_margin(code):
    assert stressed_per_lot([zero_row(code, 0.0)], (code, 0.0, 1), DAY, SETTINGS) == 0.0


@pytest.mark.parametrize("code", ["CDS", "PDS", "SF"])
def test_a_structure_with_a_sold_leg_must_still_need_margin(code):
    with pytest.raises(MarginProblem, match="not above 0"):
        stressed_per_lot([zero_row(code, 100.0)], (code, 100.0, 1), DAY, SETTINGS)


def test_the_proposal_builder_matches_the_real_structure_and_the_day():
    spec, width = ONE_SIDE["CDS"]
    trade = one_side_proposal("CDS", spec, width)
    assert (trade.book, trade.day, trade.cutoff, trade.lot_size) == (BOOK1_RULES, DAY, CUTOFF, LOT)
    assert trade.claimed_max_loss == proposer_max_loss("CDS", spec, width)
    assert trade.legs == legs_of(spec)
