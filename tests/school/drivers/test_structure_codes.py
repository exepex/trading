"""MS-P1m's `RoadTradeTerms` accepts only SC, SF, BF, PCS, CCS, CDS and PDS, each with its right legs (orchestrator, 22
Oct 2026). Every proposal of every driver uses exactly these codes with these legs; the oracle is the definition of
each structure, not the code under test."""

import functools
from datetime import timedelta

import pytest

from fno.school.constants import Outcome
from tests.school.drivers import builders as b
from tests.school.drivers.test_quotes_and_estimates import CASES

ACCEPTED = {"SC", "SF", "BF", "PCS", "CCS", "CDS", "PDS"}


def legs_of(proposal):
    return [(leg.key.strike, str(leg.key.kind), leg.side) for leg in proposal.legs]


def check_shape(proposal):
    code, legs = proposal.structure, legs_of(proposal)
    assert code in ACCEPTED, code
    by = lambda kind, side: sorted(s for s, k, sd in legs if k == kind and sd == side)  # noqa: E731
    if code in ("PCS", "CCS", "CDS", "PDS"):
        kind = "PE" if code in ("PCS", "PDS") else "CE"
        near_side = "sell" if code in ("PCS", "CCS") else "buy"
        far_side = "buy" if near_side == "sell" else "sell"
        assert len(legs) == 2 and {k for _, k, _ in legs} == {kind}
        (near,), (far,) = by(kind, near_side), by(kind, far_side)
        assert (far < near) if kind == "PE" else (far > near)  # the far leg is further out of the money
    else:
        body_side = "buy" if code == "BF" else "sell"
        wing_side = "sell" if code == "BF" else "buy"
        assert len(legs) == 4
        (body_call,), (body_put,) = by("CE", body_side), by("PE", body_side)
        (wing_call,), (wing_put,) = by("CE", wing_side), by("PE", wing_side)
        assert wing_call - body_call == body_put - wing_put > 0  # equal wings beyond the body
        assert (body_call == body_put) if code in ("SF", "BF") else (body_call > body_put)


@functools.cache
def proposals():
    found = []
    for code, ((road_day, snapshot), history) in CASES.items():
        decision = b.drivers()[code].decide(road_day, snapshot, history, ())
        assert decision.outcome == Outcome.TRADE, code
        found.append((code, decision.proposal))
    for n in range(80):  # RC1 draws all six shapes over many days
        road_day, snapshot = b.scene(session=b.SESSION + timedelta(days=n))
        found.append(("RC1", b.drivers()["RC1"].decide(road_day, snapshot, (), ()).proposal))
    return tuple(found)


def test_every_proposal_uses_an_accepted_code_with_its_right_legs():
    seen = set()
    for _, proposal in proposals():
        check_shape(proposal)
        seen.add(proposal.structure)
    assert seen == ACCEPTED


EXPECTED = {"PS5": "SF", "KL1": "SC", "REF": "SC", "WS1": "SC", "DB1": "BF", "DR1": "CDS", "CS1": "PCS",
            "PS2": "SC", "PS3": "SC", "PS4": "SC"}  # fmt: skip


@pytest.mark.parametrize("code, expected", sorted(EXPECTED.items()))
def test_each_family_uses_its_codes_table_structure(code, expected):
    found = {p.structure for name, p in proposals() if name == code}
    assert found == {expected}
