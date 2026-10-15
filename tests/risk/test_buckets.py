"""Story C5 criteria 5-6: bucket assignment as design 6.2 defines it (one underlying group and one side of exposure), an
unmapped position refused (design 6.1a), and each held position's maximum loss equal to B2's for the same trade."""

from datetime import timedelta

import pytest

from fno.config import load_app_config
from fno.constants import BUCKET_LONG_VOL, BUCKET_SHORT_VOL, OPTION_CALL, OPTION_PUT, STRUCTURE_LONG_IRON_FLY
from fno.research_engine.structures import BOUGHT, SOLD
from fno.risk.buckets import Bucket, StructureBuckets, underlying_of
from fno.risk.cap_settings import cap_settings
from fno.risk.inputs import RiskInputError
from fno.risk.open_risk import HeldMaxLoss
from fno.risk.trade_costs import SimulatorTradeCosts
from fno.risk.wiring import build_risk_manager

from .builders import CHARGES, CONDOR, DAY, FLY, book, market, open_trade, proposal, short_condor, short_fly

SIDES = cap_settings(load_app_config()).bucket_sides
BUCKETS = StructureBuckets(SIDES)
EXPIRY = DAY + timedelta(days=14)
PRICES = {
    (25000, "CE"): 150.0, (25000, "PE"): 140.0, (25200, "CE"): 70.0, (24800, "PE"): 60.0,
    (25500, "CE"): 40.0, (24500, "PE"): 35.0, (25700, "CE"): 15.0, (24300, "PE"): 12.0,
}  # fmt: skip


@pytest.mark.parametrize(
    ("contract", "underlying"),
    [("NIFTY26OCT25000CE", "NIFTY"), ("BANKNIFTY26O2852000PE", "BANKNIFTY"), ("M&M26OCT3000CE", "M&M")],
)
def test_the_underlying_is_the_symbol_before_its_first_digit(contract, underlying):
    assert underlying_of(contract) == underlying


@pytest.mark.parametrize(
    ("structure", "bucket"),
    [
        (FLY, Bucket("NIFTY", BUCKET_SHORT_VOL)),
        (CONDOR, Bucket("NIFTY", BUCKET_SHORT_VOL)),
        (STRUCTURE_LONG_IRON_FLY, Bucket("NIFTY", BUCKET_LONG_VOL)),
    ],
)
def test_each_built_structure_has_one_bucket(structure, bucket):
    assert BUCKETS.bucket_of(structure, ["NIFTY26OCT25000CE", "NIFTY26OCT25200CE"]) == bucket


def test_banknifty_is_its_own_group():
    assert BUCKETS.bucket_of(FLY, ["BANKNIFTY26OCT52000CE"]).group == "BANKNIFTY"


@pytest.mark.parametrize(
    ("structure", "contracts", "problem"),
    [
        ("BCS", ["NIFTY26OCT25000CE"], "structure 'BCS'"),  # a directional spread: STR1, the owner maps it first
        (FLY, ["RELIANCE26OCT3000CE"], "'RELIANCE'"),  # a stock: its group and the results week are not wired
        (FLY, ["FINNIFTY26OCT24000CE"], "'FINNIFTY'"),  # an index 6.2 does not name
        (FLY, ["NIFTY26OCT25000CE", "BANKNIFTY26OCT52000PE"], "not one"),
    ],
)
def test_an_unmapped_position_is_an_input_error(structure, contracts, problem):
    with pytest.raises(RiskInputError, match="unmapped bucket") as error:
        BUCKETS.bucket_of(structure, contracts)
    assert problem in str(error.value)


def test_the_risk_manager_refuses_an_unmapped_proposal_with_the_reason(tmp_path):
    cfg = load_app_config()
    cfg["risk"]["caps"]["bucket_sides"] = {CONDOR: BUCKET_SHORT_VOL}  # SF not mapped
    decision = build_risk_manager(cfg, tmp_path).evaluate(
        proposal("new", FLY, 200, short_fly(25000, 200), EXPIRY), book(), market(25000, PRICES, EXPIRY)
    )
    refused = {v.rule: v.reason for v in decision.verdicts if not v.ok}
    assert {"bucket_cap", "open_risk_cap", "new_risk_per_day"} <= set(refused)
    assert "unmapped bucket: structure 'SF'" in refused["bucket_cap"]


@pytest.mark.parametrize(
    ("structure", "spec", "lots"),
    [(FLY, short_fly(25000, 200), 1), (FLY, short_fly(25000, 200), 3), (CONDOR, short_condor(25500, 24500, 200), 2)],
)
def test_a_held_trade_just_entered_has_b2s_maximum_loss(structure, spec, lots):
    """The open trade's maximum loss from the ledger's cash equals the per-trade check's number for the same entry."""
    costs, the_market = SimulatorTradeCosts(CHARGES), market(25000, PRICES, EXPIRY)
    new = proposal("t", structure, 200, spec, EXPIRY, lots=lots)
    held = open_trade("t", structure, 200, spec, EXPIRY, costs.entry_cash_flow(new, the_market), lots=lots)
    loss = HeldMaxLoss(CHARGES).max_loss(held.units, held.cash_flow, the_market)
    assert loss == pytest.approx(costs.max_loss(new, the_market), abs=1e-6)


def test_a_held_position_with_a_net_short_tail_is_refused_never_measured():
    the_market = market(25000, PRICES, EXPIRY)
    naked = {next(c for c, q in the_market.quotes.items() if (q.strike, q.kind) == (25000, OPTION_CALL)): -65}
    with pytest.raises(RiskInputError, match="CE units sold than bought"):
        HeldMaxLoss(CHARGES).max_loss(naked, 9_750.0, the_market)


def test_a_flat_or_locked_in_position_counts_zero_never_negative():
    the_market = market(25000, PRICES, EXPIRY)
    puts = [(25000, OPTION_PUT, BOUGHT), (24800, OPTION_PUT, SOLD)]
    held = open_trade("t", FLY, 200, puts, EXPIRY, cash_flow=50_000.0)  # far more cash in than it can lose
    assert HeldMaxLoss(CHARGES).max_loss(held.units, held.cash_flow, the_market) == 0.0
    assert HeldMaxLoss(CHARGES).max_loss({}, 0.0, the_market) == 0.0
