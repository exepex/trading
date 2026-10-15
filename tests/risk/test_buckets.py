"""Story C5 criteria 5-6: bucket assignment as design 6.2 defines it (one underlying group and one side of exposure), an
unmapped position refused (design 6.1a), and each held position's maximum loss equal to B2's for the same trade."""

from datetime import timedelta

import pytest

from fno.config import load_app_config
from fno.constants import (
    BUCKET_BULLISH,
    BUCKET_LONG_VOL,
    BUCKET_SHORT_VOL,
    OPTION_CALL,
    OPTION_PUT,
    RISK_PROFILE_BOOKS,
    STRUCTURE_LONG_IRON_FLY,
)
from fno.research_engine.structures import BOUGHT, SOLD
from fno.risk.buckets import Bucket, StructureBuckets, underlying_of
from fno.risk.inputs import RiskInputError
from fno.risk.open_risk import HeldMaxLoss
from fno.risk.profile_settings import profile_settings
from fno.risk.trade_costs import SimulatorTradeCosts
from fno.risk.wiring import build_risk_manager

from .builders import CHARGES, CONDOR, DAY, FLY, book, market, open_trade, proposal, short_condor, short_fly

SIDES = profile_settings(load_app_config(), RISK_PROFILE_BOOKS).bucket_sides
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
    assert BUCKETS.buckets_of(structure, ["NIFTY26OCT25000CE", "NIFTY26OCT25200CE"]) == (bucket,)


def test_banknifty_is_its_own_group():
    assert BUCKETS.buckets_of(FLY, ["BANKNIFTY26OCT52000CE"])[0].group == "BANKNIFTY"


def test_a_directional_spread_listed_with_two_sides_is_in_both_buckets():
    """Owner, 15 Oct 2026, "1 B": a credit vertical in its direction and short volatility, a debit vertical in its
    direction and long volatility (the codes are STR1's; these are placeholders)."""
    sides = {"BPS": (BUCKET_BULLISH, BUCKET_SHORT_VOL), "BCD": (BUCKET_BULLISH, BUCKET_LONG_VOL)}
    buckets = StructureBuckets(sides)
    assert buckets.buckets_of("BPS", ["NIFTY26OCT24800PE", "NIFTY26OCT24600PE"]) == (
        Bucket("NIFTY", BUCKET_BULLISH), Bucket("NIFTY", BUCKET_SHORT_VOL),
    )  # fmt: skip
    assert Bucket("NIFTY", BUCKET_LONG_VOL) in buckets.buckets_of("BCD", ["NIFTY26OCT25000CE"])


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
        BUCKETS.buckets_of(structure, contracts)
    assert problem in str(error.value)


def test_the_risk_manager_refuses_an_unmapped_proposal_with_the_reason(tmp_path):
    cfg = load_app_config()
    cfg["risk"]["profiles"]["books"]["bucket_sides"] = {CONDOR: BUCKET_SHORT_VOL}  # SF not mapped
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


@pytest.mark.parametrize(
    ("code", "sides"),
    [("PCS", (BUCKET_BULLISH, BUCKET_SHORT_VOL)), ("CCS", ("bearish", BUCKET_SHORT_VOL)),
     ("CDS", (BUCKET_BULLISH, BUCKET_LONG_VOL)), ("PDS", ("bearish", BUCKET_LONG_VOL))],
)  # fmt: skip
def test_the_repository_maps_str1s_verticals_to_the_owners_two_buckets(code, sides):
    """Owner, 15 Oct 2026, "1 B", with STR1's real codes in config.yaml."""
    assert BUCKETS.buckets_of(code, ["NIFTY26OCT24800PE"]) == tuple(Bucket("NIFTY", s) for s in sides)


@pytest.mark.parametrize("code", ["LC", "LP"])
def test_a_bought_option_stays_unmapped_until_the_owner_decides(code):
    with pytest.raises(RiskInputError, match=f"structure '{code}'"):
        BUCKETS.buckets_of(code, ["NIFTY26OCT25300CE"])


def test_a_real_bull_put_spread_counts_with_a_held_fly_and_a_held_call_debit_spread(tmp_path):
    """Through the app's wired caps: a PCS 100 counts in bullish with a held CDS and in short volatility with a held
    SF, its full maximum loss in each; each bucket binds at exactly its total."""
    from fno.risk.caps import BucketCap
    from fno.risk.wiring import build_position_risks

    prices = PRICES | {(24700, "PE"): 45.0, (25100, "CE"): 110.0}
    the_market = market(25000, prices, EXPIRY)
    risks = build_position_risks(load_app_config(), profile_settings(load_app_config(), RISK_PROFILE_BOOKS))
    pcs = proposal("new", "PCS", 100, [(24800, OPTION_PUT, SOLD), (24700, OPTION_PUT, BOUGHT)], EXPIRY)
    fly = open_trade("fly", FLY, 200, short_fly(25000, 200), EXPIRY, 10_000.0)
    cds = open_trade("cds", "CDS", 100, [(25000, OPTION_CALL, BOUGHT), (25100, OPTION_CALL, SOLD)], EXPIRY, -3_000.0)
    the_book = book([fly, cds])
    groups = BucketCap(risks, 1e9).check(pcs, the_book, the_market).numbers["groups"]
    own = risks.of_proposal(pcs, the_market).max_loss_rs
    assert set(groups["bucket NIFTY/bullish"]["counted_max_loss_rs"]) == {"cds", "new"}
    assert set(groups["bucket NIFTY/short_volatility"]["counted_max_loss_rs"]) == {"fly", "new"}
    assert all(g["counted_max_loss_rs"]["new"] == own for g in groups.values())
    binding = max(g["total_rs"] for g in groups.values())
    assert BucketCap(risks, binding).check(pcs, the_book, the_market).ok
    assert not BucketCap(risks, binding - 0.01).check(pcs, the_book, the_market).ok
