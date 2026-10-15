"""Story STR1 criteria 6 and 7: D1 loads a version with each new structure code (width 0 only for the bought-only
codes) and D2 builds its candidate through the structures, widest width within the cap first."""

from datetime import timedelta

import pytest

from fno.composition import build_tradable_structures
from fno.playbook.candidates import CandidateBuilder, NotBuilt
from fno.playbook.fields import PlaybookError
from fno.playbook.opportunities import BOOK, Opportunity
from fno.research_engine.features import DecisionContext
from fno.research_engine.structures import BOUGHT, SOLD
from tests.playbook.evaluation_builders import COSTS, DAY, EXPIRY, chain_market, strategy
from tests.risk.builders import LOT

NEW_CODES = ("LC", "LP", "CDS", "CCS", "PDS", "PCS")
STRUCTURES = {s.code: s for s in build_tradable_structures()}


def version(code: str, widths: list[float]):
    return strategy(f"str1-{code.lower()}", structure={**_structure(), "code": code, "widths": widths})


def _structure():
    from tests.playbook.builders import document

    return document()["structure"]


@pytest.mark.parametrize("code", NEW_CODES)
def test_d1_loads_a_version_with_each_new_code(code):
    loaded = version(code, [300, 200, 100])
    assert (loaded.structure.code, loaded.structure.widths) == (code, (300.0, 200.0, 100.0))


@pytest.mark.parametrize("code", ["LC", "LP"])
def test_a_bought_only_code_may_list_width_0_the_atm_strike(code):
    assert version(code, [100, 0]).structure.widths == (100.0, 0.0)


@pytest.mark.parametrize("code", ["CDS", "CCS", "PDS", "PCS", "SF", "SC", "BF"])
def test_a_code_with_a_sold_leg_refuses_width_0(code):
    with pytest.raises(PlaybookError, match="positive point widths"):
        version(code, [100, 0])


@pytest.mark.parametrize("code", ["LC", "XS"])
def test_negative_widths_and_unknown_codes_are_refused(code):
    with pytest.raises(PlaybookError):
        version(code, [100, -50]) if code == "LC" else version(code, [100])


def build(code: str, widths: list[float], cap: float = 10_000.0):
    opportunity = Opportunity(version(code, widths), DecisionContext(EXPIRY, DAY, EXPIRY - timedelta(days=21)), BOOK)
    return CandidateBuilder(STRUCTURES, COSTS, cap, LOT).build(opportunity, chain_market(), "t1")


# A credit spread 300 wide can lose (300 - about 106 credit) x 65 = about Rs 12,600, over the cap: 200 is kept
EXPECTED = {
    "LC": ([(25_300, "CE", BOUGHT)], 300.0),
    "LP": ([(24_700, "PE", BOUGHT)], 300.0),
    "CDS": ([(25_000, "CE", BOUGHT), (25_300, "CE", SOLD)], 300.0),
    "CCS": ([(25_000, "CE", SOLD), (25_200, "CE", BOUGHT)], 200.0),
    "PDS": ([(25_000, "PE", BOUGHT), (24_700, "PE", SOLD)], 300.0),
    "PCS": ([(25_000, "PE", SOLD), (24_800, "PE", BOUGHT)], 200.0),
}


@pytest.mark.parametrize("code", NEW_CODES)
def test_d2_builds_each_new_code_at_the_widest_width_within_the_cap(code):
    candidate = build(code, [300, 200, 100])
    legs = [(p.leg.strike, p.leg.kind, p.leg.side) for p in candidate.proposal.legs]
    assert (legs, candidate.proposal.terms.width) == EXPECTED[code]
    assert 0 < candidate.max_loss <= 10_000


def test_d2_skips_widths_over_the_cap_and_names_each_when_none_fits():
    """A bought ATM call (about Rs 200 x 65 here) is over a Rs 5,000 cap; 300 points out (about Rs 94) fits."""
    assert build("LC", [300, 0], cap=10_000).proposal.terms.width == 300.0
    with pytest.raises(NotBuilt, match="0: maximum loss .* above the cap 5000"):
        build("LC", [0], cap=5_000)


def test_d1_c4_d2_and_a14_know_the_same_nine_codes():
    """A code D1 accepts but D2 cannot build would crash the evaluation (KeyError), and one C4 has no shape for would
    fail every trade: the four lists must stay equal."""
    from fno.checks.wiring import validity_shapes
    from fno.config import load_app_config
    from fno.nse_margins.wiring import build_row_builder
    from fno.playbook.vocabulary import STRUCTURE_CODES

    margins = {s.code for s in build_row_builder(load_app_config()).structures}
    assert set(STRUCTURE_CODES) == set(validity_shapes()) == set(STRUCTURES) == margins and len(margins) == 9


@pytest.mark.parametrize("widths", [[float("nan")], [float("inf"), 100], [100, True]])
def test_widths_that_are_not_finite_numbers_are_refused(widths):
    with pytest.raises(PlaybookError, match="point widths"):
        version("LC", widths)


def test_minus_zero_is_read_as_the_atm_width_0():
    assert str(version("LC", [-0.0]).structure.widths[0]) == "0.0"
