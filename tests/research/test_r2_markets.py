"""R2 exclusions between events and markets (PROTOCOL.md section 4, amendment 1 D3, amendment 2 item 4)."""

from collections import Counter
from datetime import date

from r2_synthetic import flat_chain, weekdays
from r2study import markets as mk
from r2study.bhav import DaySummary, Future
from r2study.events import Event
from r2study.markets import market, plan_event, screen_lots
from r2study.sessions import Sessions
from r2study.sources import CorporateActions, SymbolNames
from r2study.structures import Strikes

from fno.market_read_models.corporate_actions import CorporateAction

S = Sessions(weekdays(date(2025, 10, 1), date(2025, 12, 31)))
EVENT = Event("ABC", date(2025, 10, 15), date(2025, 10, 14), date(2025, 10, 16), None)


class FixedLots:
    def __init__(self, by_day):
        self.by_day = by_day

    def lot(self, symbol, day):
        return self.by_day.get(day)


def actions(*ex_dates):
    names = SymbolNames([])
    return CorporateActions([CorporateAction("ABC", d, "Bonus 1:1", "ratio", 2.0) for d in ex_dates], names)


def test_lot_unknown_lot_change_and_listed_action_are_excluded_and_counted():
    same = {EVENT.entry: 100, EVENT.reaction: 100}
    assert screen_lots([EVENT], FixedLots(same), actions()) == ([(EVENT, 100)], Counter())
    assert screen_lots([EVENT], FixedLots({}), actions())[1] == Counter({mk.LOT_UNKNOWN: 1})
    changed = {EVENT.entry: 100, EVENT.reaction: 200}
    assert screen_lots([EVENT], FixedLots(changed), actions())[1] == Counter({mk.CORPORATE_ACTION: 1})
    assert screen_lots([EVENT], FixedLots(same), actions(EVENT.reaction))[1] == Counter({mk.CORPORATE_ACTION: 1})
    assert screen_lots([EVENT], FixedLots(same), actions(EVENT.entry))[0] == [(EVENT, 100)]  # ex-date on entry: out
    assert screen_lots([], FixedLots(same), actions()) == ([], Counter())


def summary(close=1000.0):
    futures = {"ABC": [Future(date(2025, 10, 28), close, close, 10, 1, 1, 100)]}
    return DaySummary(EVENT.entry, futures, frozenset({"ABC"}))


def test_plan_needs_a_future_close_an_expiry_after_five_sessions_and_a_listed_strike():
    chains = {date(2025, 10, 28): flat_chain([980, 1000, 1020]), date(2025, 11, 25): flat_chain([980, 1000, 1020])}
    plan, reason = plan_event(EVENT, 100, summary(), chains, S)
    assert reason == "" and plan.expiry == date(2025, 10, 28) and not plan.pushed and plan.strikes.k0 == 1000.0
    assert plan_event(EVENT, 100, summary(0.0), chains, S) == (None, mk.NO_FUTURE)
    assert plan_event(EVENT, 100, summary(), {date(2025, 10, 21): {}}, S) == (None, mk.NO_EXPIRY)
    assert plan_event(EVENT, 100, summary(), {date(2025, 10, 28): {}}, S) == (None, mk.NO_ATM)


def test_market_is_none_when_k0_is_not_listed_on_r():
    chains = {date(2025, 10, 28): flat_chain([980, 1000, 1020])}
    plan, _ = plan_event(EVENT, 100, summary(), chains, S)
    assert market(plan, "IT", flat_chain([990, 1010]), None) is None
    assert market(plan, "IT", None, None) is None
    found = market(plan, None, flat_chain([1000]), None)
    assert found.strikes == Strikes(1000.0, 20.0, 20.0) and found.previous == {} and found.sector is None
