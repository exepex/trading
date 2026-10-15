"""R2 exclusions between events and markets (PROTOCOL.md section 4; amendment 1 D3-D4 revision 1; amendment 2)."""

from collections import Counter
from datetime import date

from r2_synthetic import weekdays
from r2study import markets as mk
from r2study.bhav import DaySummary, Future, Leg
from r2study.events import Event
from r2study.markets import market, plan_event, screen_actions
from r2study.sessions import Sessions
from r2study.sources import CorporateActions, SymbolNames
from r2study.structures import Strikes

from fno.market_read_models.corporate_actions import CorporateAction

S = Sessions(weekdays(date(2025, 10, 1), date(2025, 12, 31)))
EVENT = Event("ABC", date(2025, 10, 15), date(2025, 10, 14), date(2025, 10, 16), None)
OCT, NOV = date(2025, 10, 28), date(2025, 11, 25)


def actions(*ex_dates):
    return CorporateActions([CorporateAction("ABC", d, "Bonus 1:1", "ratio", 2.0) for d in ex_dates], SymbolNames([]))


def test_a_listed_action_in_entry_to_r_is_excluded_and_on_the_entry_day_is_not():
    assert screen_actions([EVENT], actions()) == ([EVENT], Counter())
    assert screen_actions([EVENT], actions(EVENT.reaction)) == ([], Counter({mk.CORPORATE_ACTION: 1}))
    assert screen_actions([EVENT], actions(EVENT.entry))[0] == [EVENT]
    assert screen_actions([], actions()) == ([], Counter())


def chain(lot=100, strikes=(980, 1000, 1020)):
    return {(float(k), kind): Leg(10.0, 100.0, 50_000.0, lot) for k in strikes for kind in ("CE", "PE")}


def summary(close=1000.0):
    return DaySummary(EVENT.entry, {"ABC": [Future(OCT, close, close, 10, 1, 1, 100)]}, frozenset({"ABC"}))


class FixedLegacy:
    def __init__(self, lot):
        self.lot = lot

    def derived(self, symbol, day, expiry):
        return self.lot


def test_plan_takes_the_chosen_expirys_lot_and_counts_what_is_missing():
    plan, reason = plan_event(EVENT, summary(), {OCT: chain(150), NOV: chain(300)}, S, None)
    assert reason == "" and plan.expiry == OCT and plan.lot == 150 and plan.lot_from_column
    assert plan.strikes.k0 == 1000.0 and not plan.pushed
    assert plan_event(EVENT, summary(0.0), {OCT: chain()}, S, None) == (None, mk.NO_FUTURE)
    assert plan_event(EVENT, summary(), {date(2025, 10, 21): chain()}, S, None) == (None, mk.NO_EXPIRY)
    assert plan_event(EVENT, summary(), {OCT: {}}, S, None) == (None, mk.NO_ATM)
    assert plan_event(EVENT, summary(), {OCT: chain(None)}, S, None) == (None, mk.LOT_UNKNOWN)


def test_legacy_rows_use_the_validated_derivation_and_skip_the_lot_check_on_r():
    plan, _ = plan_event(EVENT, summary(), {OCT: chain(None)}, S, FixedLegacy(250))
    assert plan.lot == 250 and not plan.lot_from_column
    found, reason = market(plan, "IT", chain(None), None)
    assert reason == "" and found.lot == 250


def test_market_checks_k0_and_the_contracts_lot_on_r():
    plan, _ = plan_event(EVENT, summary(), {OCT: chain(100)}, S, None)
    assert market(plan, "IT", chain(100, (990, 1010)), None) == (None, mk.CORPORATE_ACTION)
    assert market(plan, "IT", None, None) == (None, mk.CORPORATE_ACTION)
    assert market(plan, "IT", chain(200), None) == (None, mk.CORPORATE_ACTION)
    assert market(plan, "IT", chain(None), None) == (None, mk.LOT_UNKNOWN_ON_R)
    found, reason = market(plan, None, chain(100), None)
    assert reason == "" and found.strikes == Strikes(1000.0, 20.0, 20.0) and found.previous == {}
