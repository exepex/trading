"""Fixtures for story D2's evaluation tests: a NIFTY chain with fixed prices, approved and research versions, fixed
live feature values and trade counts, and a risk manager with the per-trade and slot rules."""

from __future__ import annotations

import math
from datetime import date, timedelta
from pathlib import Path

from fno.composition import build_session_calendar, build_structures
from fno.constants import BOOKS
from fno.playbook.allocation import Allocator
from fno.playbook.candidates import CandidateBuilder
from fno.playbook.evaluate import LiveFeatureValues, RuleEvaluator
from fno.playbook.loader import Playbook
from fno.playbook.opportunities import OpportunityFinder
from fno.playbook.schema import parse_strategy
from fno.playbook.shadow import RealBooks, ShadowAccount, ShadowBooks
from fno.research_engine.cycles import TradingDays
from fno.risk.manager import RiskManager
from fno.risk.rules import MaxLossPerTrade, MaxOpenTrades
from fno.risk.trade_costs import SimulatorTradeCosts
from tests.risk.builders import CONDOR, LOT, ZERO_CHARGES, book, market, open_trade, short_condor

from .builders import document

DAY = date(2026, 10, 13)  # a Tuesday session; the expiry below is 45 days away, 46 on the session before
EXPIRY = DAY + timedelta(days=45)
SPOT = 25_000.0
LIVE_TRUE = {"F1_live_atm_iv_minus_rv20": 2.5, "F2_live_vix_above_250d_median": True,
             "F3_live_scheduled_event_in_window": False}  # fmt: skip
COSTS = SimulatorTradeCosts(ZERO_CHARGES)


def price(strike: float, kind: str) -> float:
    intrinsic = max(SPOT - strike, 0.0) if kind == "CE" else max(strike - SPOT, 0.0)
    return round(intrinsic + 200 * math.exp(-abs(strike - SPOT) / 400), 2)


def chain_market(prices=None, day: date = DAY):
    strikes = [24_000 + 50 * n for n in range(41)]
    prices = prices or {(k, kind): price(k, kind) for k in strikes for kind in ("CE", "PE")}
    return market(SPOT, prices, EXPIRY, day=day)


def strategy(name: str, status: str = "paper", expected: float | str = 150.0, **changes):
    doc = document(name=name, status=status, **changes)
    doc["evaluation_plan"]["expected_net_per_opportunity"] = expected  # a number, or "none" (research only)
    return parse_strategy(doc)


def playbook(*strategies, registered=()):
    return Playbook(tuple(strategies), frozenset(registered))


class FixedValues(LiveFeatureValues):
    def __init__(self, values=None):
        self.given = dict(LIVE_TRUE if values is None else values)

    def values(self, day, context):
        return self.given


class Counts:
    def __init__(self, completed=25, open_=0):
        self.done, self.held = completed, open_

    def completed(self, name, version):
        return self.done

    def open(self, name, version):
        return self.held


REPO = Path("/repo")  # resolve() works on paths that do not exist: no files are touched
REAL = RealBooks(BOOKS, [REPO / "journal" / name for name in BOOKS])


class OwnShadowBooks(ShadowBooks):
    def __init__(self, books=None, counts=None, storage=None):
        self.books, self.counts, self.asked = dict(books or {}), counts or Counts(completed=0), []
        self.storage = storage

    def account(self, strategy):
        self.asked.append(strategy.key)
        the_book = self.books.get(strategy.name, book(name=f"shadow-{strategy.name}"))
        return ShadowAccount(the_book, self.counts, self.storage or REPO / "journal" / "shadow" / strategy.name)


def evaluator(max_open: int = 3) -> RuleEvaluator:
    risk = RiskManager((MaxLossPerTrade(COSTS, 10_000), MaxOpenTrades(max_open)), {})
    structures = {s.code: s for s in build_structures()}
    builder = CandidateBuilder(structures, COSTS, 10_000, LOT)
    return RuleEvaluator(
        OpportunityFinder(TradingDays(build_session_calendar())), builder, Allocator(risk, COSTS), REAL
    )


def book_with_open(count: int, name: str = "book1_rules"):
    trades = [
        open_trade(f"old-{n}", CONDOR, 100, short_condor(25_500, 24_500, 100), EXPIRY, 1_000.0) for n in range(count)
    ]
    return book(open_trades=trades, name=name)


def run(strategies, values=None, the_book=None, counts=None, shadow=None, registered=(), prices=None):
    return evaluator().evaluate(
        DAY, playbook(*strategies, registered=registered), chain_market(prices), FixedValues(values),
        the_book or book(), counts or Counts(), shadow or OwnShadowBooks(),
    )  # fmt: skip
