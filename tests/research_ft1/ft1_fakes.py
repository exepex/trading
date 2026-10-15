"""Synthetic inputs for the FT1 tests: a session calendar, an expiry's chain, candle rows and a market. No real data."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta

from ft1study.bars import Bar, BarBook
from ft1study.contracts import MonthlyContracts, option_symbol
from ft1study.entries import IndexLevels
from ft1study.observe import Market, Observer, Terms
from ft1study.times import Moment

from fno.research_data.calendar import SessionCalendar
from fno.research_engine.one_side import BoughtOption, VerticalSpread
from fno.research_engine.structures import BOUGHT, SOLD, LongIronFly, ShortCondor, ShortIronFly

CHARGES = {"brokerage_per_order": 20.0, "exchange_txn_pct": 0.03503, "sebi_per_crore": 10.0, "ipft_per_crore": 50.0,
           "stt_sell_pct": 0.1, "stamp_duty_buy_pct": 0.003, "gst_pct": 18.0, "stt_exercise_pct": 0.15}  # fmt: skip
TERMS = Terms(lot=65, charges=CHARGES, rate=0.065)
STRIKES = [float(k) for k in range(20000, 26050, 50)]


def structures():
    return (ShortIronFly(), ShortCondor(), LongIronFly(), BoughtOption("LC", "CE"), BoughtOption("LP", "PE"),
            VerticalSpread("CDS", "CE", BOUGHT), VerticalSpread("CCS", "CE", SOLD),
            VerticalSpread("PDS", "PE", BOUGHT), VerticalSpread("PCS", "PE", SOLD))  # fmt: skip


class FakeCalendar(SessionCalendar):
    """Weekdays are regular sessions except `holidays`; `kinds` overrides a day (special, muhurat)."""

    def __init__(self, holidays=(), kinds=None):
        self.holidays, self.kinds = set(holidays), dict(kinds or {})

    def session_kind(self, day: date) -> str | None:
        if day in self.kinds:
            return self.kinds[day]
        return "regular" if day.weekday() < 5 and day not in self.holidays else None

    def calendar_sha256(self) -> str:
        return "fake"


def chain(strikes=STRIKES) -> frozenset:
    return frozenset((k, kind) for k in strikes for kind in ("CE", "PE"))


def contracts(expiries, first: date, last: date, calendar: FakeCalendar, settlement=None) -> MonthlyContracts:
    found = MonthlyContracts()
    for expiry in expiries:
        for day in calendar.sessions(first, min(last, expiry)):
            found.listed[expiry][day] = chain()
    found.settlement = dict(settlement or {})
    return found


def row(day: date, at: time, close: float, volume: float = 100.0) -> list:
    """A Groww candle row starting at `at` (IST text without an offset)."""
    return [datetime.combine(day, at).isoformat(), close, close, close, close, volume, 1000]


def index_book(levels: dict[tuple[date, time], float]) -> IndexLevels:
    """`levels`: (day, mark time) -> index level at that mark (the candle starting 15 minutes earlier)."""
    rows = [row(d, (datetime.combine(d, t) - timedelta(minutes=15)).time(), v, 0) for (d, t), v in levels.items()]
    return IndexLevels(BarBook([rows]))


class Prices:
    """Leg prices by (symbol, day, mark): a dict-backed `Market.bar`. A price given as None is a stale candle."""

    def __init__(self):
        self.bars: dict[tuple[str, datetime], Bar] = {}

    def set(self, symbol: str, day: date, at: time, close: float | None) -> None:
        self.bars[(symbol, datetime.combine(day, at))] = Bar(close or 0.0, 0.0 if close is None else 100.0)

    def option(self, expiry: date, strike: float, kind: str, day: date, at: time, close: float | None) -> None:
        self.set(option_symbol(expiry, strike, kind), day, at, close)

    def bar(self, symbol: str, moment: Moment) -> Bar | None:
        return self.bars.get((symbol, moment.naive))


def observer(prices: Prices, index: IndexLevels, calendar: FakeCalendar, settlement=None, vix=None) -> Observer:
    market = Market(prices.bar, index, dict(vix or {}), dict(settlement or {}), calendar.next_session)
    return Observer(market, TERMS)
