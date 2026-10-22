"""The adapter that runs C2's rules unedited on school inputs: the bucket map covers the pilot's four indices and fails
closed otherwise; a mid exists only at a valid two-sided quote of this slot; a held position on another road is marked
at its own road's snapshot; C2's width is the widest bought-sold gap of one option type."""

from dataclasses import replace

import pytest

from fno.risk.inputs import RiskInputError
from fno.risk.profile_settings import profile_settings
from fno.school.constants import OptionKind, RoadCode
from fno.school.contracts.decisions import LegSpec
from fno.school.safety.buckets import SchoolBuckets
from fno.school.safety.c2_inputs import PROPOSAL_ID, c2_inputs, structure_width
from tests.school.contracts import builders as b

from .law_builders import CFG, held, view

BUCKETS = SchoolBuckets(profile_settings(CFG, "books").bucket_sides)


@pytest.mark.parametrize(
    ("index", "group"),
    [("NIFTY", "NIFTY"), ("BANKNIFTY", "BANKNIFTY+FINNIFTY"), ("FINNIFTY", "BANKNIFTY+FINNIFTY"),
     ("MIDCPNIFTY", "MIDCPNIFTY")],
)  # fmt: skip
def test_the_pilot_bucket_groups(index, group):
    """Orchestrator, 22 Oct 2026: FINNIFTY shares BANKNIFTY's bucket (one shock hits the same banks)."""
    buckets = BUCKETS.buckets_of("PCS", [f"{index}20261123PE1000", f"{index}20261123PE900"])
    assert [(x.group, x.side) for x in buckets] == [(group, "bullish"), (group, "short_volatility")]


@pytest.mark.parametrize(
    ("structure", "contracts", "why"),
    [
        ("PCS", ["NIFTY20261123PE1000", "BANKNIFTY20261123PE900"], "two indices"),
        ("PCS", ["SENSEX20261123PE1000"], "not a pilot index"),
        ("XYZ", ["NIFTY20261123PE1000"], "no side"),
    ],
)
def test_an_unmapped_position_fails_closed(structure, contracts, why):
    with pytest.raises(RiskInputError, match="unmapped"):
        BUCKETS.buckets_of(structure, contracts)


def test_a_mid_only_at_a_valid_two_sided_quote_of_this_slot():
    one_sided = b.snapshot(quotes={b.key(1000.0): replace(b.quote(), ask=None), b.key(900.0): b.quote(4.0, 5.0)})
    market = c2_inputs(b.put_spread(), RoadCode.BANKNIFTY_MONTHLY, view(), {RoadCode.BANKNIFTY_MONTHLY: one_sided},
                       b.SESSION).market  # fmt: skip
    assert market.quote("BANKNIFTY20261123PE900").mid == 4.5
    with pytest.raises(RiskInputError, match="no valid two-sided quote"):
        _ = market.quote("BANKNIFTY20261123PE1000").mid
    with pytest.raises(RiskInputError, match="no contract"):
        market.quote("BANKNIFTY20261123PE800")


def test_a_position_on_another_road_is_marked_at_that_road_s_snapshot():
    nifty = held("n1", road=RoadCode.NIFTY_MONTHLY)
    slot = {
        RoadCode.BANKNIFTY_MONTHLY: b.snapshot(),
        RoadCode.NIFTY_MONTHLY: b.snapshot(RoadCode.NIFTY_MONTHLY, {b.key(1000.0): b.quote(20.0, 22.0)}),
    }
    inputs = c2_inputs(b.put_spread(), RoadCode.BANKNIFTY_MONTHLY, view(open_positions=(nifty,)), slot, b.SESSION)
    assert inputs.market.quote("NIFTY20261123PE1000").mid == 21.0  # NIFTY's own quote, not BANKNIFTY's 10.5
    assert inputs.market.quote("BANKNIFTY20261123PE1000").mid == 10.5
    assert [t.trade_id for t in inputs.book.open_trades] == ["n1"] and inputs.proposal.trade_id == PROPOSAL_ID


def test_c2_width_is_the_widest_bought_sold_gap_of_one_type():
    call = OptionKind.CALL
    condor = (LegSpec(b.key(900.0), "buy", 1), LegSpec(b.key(1000.0), "sell", 1),
              LegSpec(b.key(1200.0, call), "sell", 1), LegSpec(b.key(1350.0, call), "buy", 1))  # fmt: skip
    assert structure_width(condor) == 150.0
    assert structure_width((LegSpec(b.key(1000.0), "buy", 1),)) == 0.0
