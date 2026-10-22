"""Story MS-P1d criterion 1: each law passes at its limit and refuses one rupee (or one unit) beyond it. The daily
stop and the brake act when the loss reaches their limit (story 3.3, C2's brake), so they pass one rupee short of it.
The C2 caps are checked at their own computed totals: the limit set to the total passes, a rupee less refuses."""

from dataclasses import replace

import pytest

from fno.research_engine.cycle_costs import PAD, CycleTerms, PositionCosts
from fno.research_engine.structures import BOUGHT, SOLD, Leg
from fno.risk.caps import BucketCap, NewRiskPerDay, OpenRiskCap
from fno.risk.open_risk import HeldMaxLoss, PositionRisks
from fno.risk.profile_settings import profile_settings
from fno.risk.rules import MarginRoom, MaxLossPerTrade
from fno.risk.trade_costs import SimulatorTradeCosts
from fno.school.constants import RefusalReason, RoadCode
from fno.school.contracts.decisions import LegSpec
from fno.school.safety.account_laws import BrakeLaw, DailyStopLaw
from fno.school.safety.buckets import SchoolBuckets
from fno.school.safety.c2_inputs import c2_inputs
from fno.school.safety.c2_laws import C2Law, MaxLossLaw, cap_numbers, margin_numbers
from fno.school.safety.quote_laws import ImpossiblePriceLaw, QuoteGateLaw
from tests.school.contracts import builders as b

from .law_builders import CFG, FixedMargin, held, view

COSTS = SimulatorTradeCosts(CFG["charges"])
RISKS = PositionRisks(SchoolBuckets(profile_settings(CFG, "books").bucket_sides), HeldMaxLoss(CFG["charges"]), COSTS)
SLOT = {RoadCode.BANKNIFTY_MONTHLY: b.snapshot()}


def check(law, proposal=None, account=None, snapshot=None):
    return law.check(proposal or b.put_spread(), account or b.account(), snapshot or b.snapshot(), b.SESSION)


def test_max_loss_at_the_limit_passes_and_a_rupee_over_refuses():
    law = MaxLossLaw(10_000, CFG["charges"], MaxLossPerTrade(COSTS, 10_000))
    assert check(law, b.put_spread(10_000)).passed
    refused = check(law, b.put_spread(10_001))
    assert refused.reason == RefusalReason.MAX_LOSS and refused.value == 10_001


def test_max_loss_counts_the_touch_the_fill_pays_not_only_the_mid():
    """A 100-point spread whose stated loss is small: B2 at the touch (bid 10 sold, ask 5 bought, Rs 1 pad) is what
    can be lost after the fill, and it is above C2's figure at the mids."""
    law = MaxLossLaw(1e9, CFG["charges"], MaxLossPerTrade(COSTS, 1e9))
    value = check(law, b.put_spread(100)).value
    legs = [Leg(1000.0, "PE", SOLD), Leg(900.0, "PE", BOUGHT)]
    at_touch = PositionCosts(CycleTerms(lot=30, charges=CFG["charges"], pad=PAD)).max_loss(legs, [10.0, 5.0])
    at_mids = PositionCosts(CycleTerms(lot=30, charges=CFG["charges"], pad=PAD)).max_loss(legs, [10.5, 4.5])
    assert value == pytest.approx(at_touch) and at_touch > at_mids
    assert not check(MaxLossLaw(at_touch - 1, CFG["charges"], MaxLossPerTrade(COSTS, 1e9)), b.put_spread(100)).passed


def at_own_total(rule_for, account) -> None:
    probe = C2Law("cap", rule_for(1e12), RefusalReason.BUCKET_CAP, cap_numbers, SLOT)
    total, alone = check(probe, account=account).value, check(probe).value
    assert total > alone, "the account's own positions count"
    assert check(C2Law("cap", rule_for(total), RefusalReason.BUCKET_CAP, cap_numbers, SLOT), account=account).passed
    refused = check(C2Law("cap", rule_for(total - 1), RefusalReason.BUCKET_CAP, cap_numbers, SLOT), account=account)
    assert not refused.passed and refused.reason == RefusalReason.BUCKET_CAP and refused.value == total


@pytest.mark.parametrize("cap", [BucketCap, OpenRiskCap, NewRiskPerDay])
def test_each_cap_at_its_total_passes_and_a_rupee_under_refuses(cap):
    holding = (held("h1", (1100.0, 1000.0)), held("h2", (1200.0, 1100.0)))
    at_own_total(lambda limit: cap(RISKS, limit), view(open_positions=holding, opened_this_session=holding))


def test_margin_room_at_the_cash_it_needs_passes_and_a_rupee_less_refuses():
    law = C2Law("margin_room", MarginRoom(FixedMargin(), COSTS), RefusalReason.MARGIN_ROOM, margin_numbers, SLOT)
    rich = view(cash=1e7, equity=1e7)
    verdict = MarginRoom(FixedMargin(), COSTS)
    inputs = c2_inputs(b.put_spread(), RoadCode.BANKNIFTY_MONTHLY, rich, SLOT, b.SESSION)
    numbers = verdict.check(inputs.proposal, inputs.book, inputs.market).numbers
    slack = min(numbers["available_after_entry_rs"] - numbers["needed_rs"],
                numbers["free_before_entry_rs"] - numbers["needed_at_entry_rs"])  # fmt: skip
    exact = view(cash=1e7 - slack, equity=1e7 - slack)
    assert check(law, account=exact).passed
    refused = check(law, account=view(cash=1e7 - slack - 1, equity=1e7 - slack - 1))
    assert refused.reason == RefusalReason.MARGIN_ROOM


def test_the_daily_stop_passes_a_rupee_short_and_stops_at_its_limit():
    assert check(DailyStopLaw(25_000), account=view(loss_since_previous_slot=24_999)).passed
    stopped = check(DailyStopLaw(25_000), account=view(loss_since_previous_slot=25_000))
    assert stopped.reason == RefusalReason.DAILY_STOP and (stopped.limit, stopped.value) == (25_000, 25_000)


def test_the_brake_passes_a_rupee_short_and_stops_at_its_limit():
    assert check(BrakeLaw(120_000), account=view(equity=1_880_001)).passed
    assert check(BrakeLaw(120_000), account=view(equity=1_880_000)).reason == RefusalReason.BRAKE


def sized(ask_size: int, bid_size: int = 1000):
    quote = replace(b.quote(4.0, 5.0), ask_qty=ask_size, bid_qty=bid_size)
    return b.snapshot(quotes={b.key(1000.0): b.quote(), b.key(900.0): quote})


def test_displayed_size_equal_to_the_units_passes_and_one_unit_short_refuses():
    law = QuoteGateLaw(RefusalReason.SIZE_ABOVE_DISPLAYED)
    assert check(law, snapshot=sized(30)).passed
    assert check(law, snapshot=sized(29)).reason == RefusalReason.SIZE_ABOVE_DISPLAYED


def test_sell_back_size_equal_to_the_units_passes_and_one_unit_short_refuses():
    law = QuoteGateLaw(RefusalReason.PROTECTION_UNSELLABLE)
    assert check(law, snapshot=sized(1000, 30)).passed
    assert check(law, snapshot=sized(1000, 29)).reason == RefusalReason.PROTECTION_UNSELLABLE


def test_a_price_inside_the_payoff_passes_and_one_at_its_bound_refuses():
    law = ImpossiblePriceLaw()

    def credit(bid):  # tight quotes, so the vertical at the mids stays within its 100-point width
        return b.snapshot(quotes={b.key(1000.0): b.quote(bid, bid + 0.01), b.key(900.0): b.quote(4.99, 5.0)})

    assert check(law, snapshot=credit(104.99)).passed  # worth -99.99 a unit: within -100 and 0 (vertical 100.0 at mids)
    refused = check(law, snapshot=credit(105.0))  # a credit of the full width: it cannot lose
    assert refused.reason == RefusalReason.IMPOSSIBLE_LEG_PRICE and refused.value == -100.0


def test_a_leg_ratio_c2_cannot_size_is_refused():
    ratio = replace(b.put_spread(), legs=(LegSpec(b.key(1000.0), "sell", 1), LegSpec(b.key(900.0), "buy", 2)))
    law = MaxLossLaw(1e9, CFG["charges"], MaxLossPerTrade(COSTS, 1e9))
    assert check(law, ratio).reason == RefusalReason.MAX_LOSS


CALL = b.OptionKind.CALL
CONDOR = replace(b.put_spread(), structure="SC", legs=(
    LegSpec(b.key(1000.0), "sell", 1), LegSpec(b.key(900.0), "buy", 1),
    LegSpec(b.key(1100.0, CALL), "sell", 1), LegSpec(b.key(1200.0, CALL), "buy", 1)))  # fmt: skip
PUTS = {b.key(1000.0): b.quote(10.0, 11.0), b.key(900.0): b.quote(4.0, 5.0)}


def condor_at(c1100: tuple, c1200: tuple):
    quotes = {**PUTS, b.key(1100.0, CALL): b.quote(*c1100), b.key(1200.0, CALL): b.quote(*c1200)}
    return check(ImpossiblePriceLaw(), CONDOR, snapshot=b.snapshot(quotes=quotes))


def test_a_stale_vertical_never_hides_behind_another_in_the_total():
    """Judge 488's condor: the call vertical 1100/1200 quoted 1.5/2.5 against 4.5/5.5 is worth less than nothing on
    any price in its range (2.5 - 4.5 = -2), though the condor's total at the touch sits inside its payoff bounds."""
    refused = condor_at((1.5, 2.5), (4.5, 5.5))
    assert refused.reason == RefusalReason.IMPOSSIBLE_LEG_PRICE and (refused.value, refused.limit) == (-2.0, 100.0)
    assert condor_at((1.5, 2.5), (0.5, 1.5)).passed


def test_a_vertical_whose_range_overlaps_its_payoff_is_valid():
    """Judge 486 add. 1 (the owner's decision: ranges): 1.5/2.5 against 1.0/4.0 is worth -0.5 at the mids but can be
    worth 2.5 - 1.0 = 1.5, so the quotes are not impossible."""
    assert condor_at((1.5, 2.5), (1.0, 4.0)).passed


@pytest.mark.parametrize(("c1200", "passed"), [((2.5, 3.0), True), ((2.51, 3.0), False)])
def test_the_lower_bound_dearer_ask_less_cheaper_bid_at_zero_passes_below_refuses(c1200, passed):
    assert condor_at((1.5, 2.5), c1200).passed is passed


@pytest.mark.parametrize(("p1000_bid", "passed"), [(101.0, True), (101.01, False)])
def test_the_upper_bound_dearer_bid_less_cheaper_ask_at_the_width_passes_above_refuses(p1000_bid, passed):
    """A bought put vertical (1000/900, width 100) with a sold call vertical, so the total stays inside its bounds:
    101.0 - 1.0 = 100 is possible, 100.01 is not."""
    legs = (LegSpec(b.key(1000.0), "buy", 1), LegSpec(b.key(900.0), "sell", 1),
            LegSpec(b.key(1100.0, CALL), "sell", 1), LegSpec(b.key(1200.0, CALL), "buy", 1))  # fmt: skip
    quotes = {b.key(1000.0): b.quote(p1000_bid, 101.5), b.key(900.0): b.quote(0.5, 1.0),
              b.key(1100.0, CALL): b.quote(50.0, 51.0), b.key(1200.0, CALL): b.quote(0.5, 1.0)}  # fmt: skip
    result = check(ImpossiblePriceLaw(), replace(b.put_spread(), legs=legs), snapshot=b.snapshot(quotes=quotes))
    assert result.passed is passed and (passed or result.value == pytest.approx(100.01))
