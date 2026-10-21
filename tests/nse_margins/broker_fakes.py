"""Fakes for A14c part 2's broker check: the planted 14 Oct SPAN file and its A14 rows (SF, SC, BF at 100 and 200), a
broker whose answers can be set per basket, a clock that sleeps by moving on, and an in-memory record."""

from __future__ import annotations

import hashlib
from datetime import date, datetime, time, timedelta

from fno.models import IST
from fno.nse_margins.broker_basket import Basket, BasketBuilder
from fno.nse_margins.broker_check import BrokerCheckParts, BrokerMarginCheck
from fno.nse_margins.broker_port import BrokerMargins
from fno.nse_margins.calculator import NseIndexOptionExposure, SpanMarginCalculator
from fno.nse_margins.rows import MarginRowBuilder
from fno.nse_margins.span_file import read_span_file
from fno.research_engine.structures import LongIronFly, ShortCondor, ShortIronFly

from .span_builder import DAY, LOT, span_zip
from .test_job import Alerts

FILE = span_zip()
NAME = "nsccl.20261014.i1.zip"
LEVEL = 20_050.0  # the live NIFTY level the fake broker quotes (the file's close is 20,000)
BUILDER = MarginRowBuilder((ShortIronFly(), ShortCondor(), LongIronFly()), (100.0, 200.0),
                           SpanMarginCalculator(NseIndexOptionExposure(), LOT), 30)  # fmt: skip
SPAN = read_span_file(FILE, NAME, allow_short_option_minimum=True)
ROWS = [row.as_csv() for row in BUILDER.rows(SPAN, hashlib.sha256(FILE).hexdigest(), DAY).rows]
BASKETS = {(r["structure"], float(r["width"])): BasketBuilder(BUILDER).basket(r, SPAN, FILE, DAY) for r in ROWS}


def at(hour: int, minute: int, second: int = 0, day: date = DAY) -> datetime:
    return datetime.combine(day, time(hour, minute, second), IST)


def exposure_at(basket: Basket, level: float = LEVEL) -> float:
    return NseIndexOptionExposure().per_unit(basket.legs, level, basket.expiry, DAY) * LOT


class Clock:
    def __init__(self, start: datetime):
        self.now, self.slept = start, []

    def __call__(self) -> datetime:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.slept.append(seconds)
        self.now += timedelta(seconds=seconds)


class FakeBroker(BrokerMargins):
    """Answers every basket exactly (SPAN after NOV, exposure at LEVEL) unless `answers` or `fail` says otherwise."""

    def __init__(self, clock: Clock, level: float | Exception = LEVEL):
        self.clock, self.level, self.asked = clock, level, []
        self.answers: dict[tuple[str, float], tuple[float, float]] = {}
        self.fail: dict[tuple[str, float], Exception] = {}

    def index_level(self) -> float:
        self.asked.append(("NIFTY", self.clock()))
        if isinstance(self.level, Exception):
            raise self.level
        return self.level

    def basket(self, orders) -> tuple[float, float]:
        key = next(k for k, b in BASKETS.items() if b.orders(LOT) == list(orders))
        self.asked.append((key, self.clock()))
        if key in self.fail:
            raise self.fail[key]
        basket = BASKETS[key]
        return self.answers.get(key, (basket.span_expected, exposure_at(basket)))


class MemoryRecord:
    def __init__(self, done: set | Exception = frozenset(), refuse: Exception | None = None):
        self.done_keys, self.refuse, self.written = done, refuse, []

    def done(self, day: date) -> set:
        if isinstance(self.done_keys, Exception):
            raise self.done_keys
        return set(self.done_keys)

    def write(self, day: date, run: datetime, results) -> str:
        if self.refuse:
            raise self.refuse
        self.written.append(list(results))
        return f"data/margins/broker_checks/{day}/{run:%H%M%S}.csv"


def make_check(start: datetime, broker: FakeBroker | None = None, record: MemoryRecord | None = None,
               rows=None, file: bytes | None = FILE, session=lambda day: day.weekday() < 5):  # fmt: skip
    clock = Clock(start)
    broker = broker or FakeBroker(clock)
    broker.clock = clock
    record = record or MemoryRecord()
    alerts, printed = Alerts(), []
    parts = BrokerCheckParts(lambda: ROWS if rows is None else rows, lambda day: (NAME, file), BasketBuilder(BUILDER),
                             broker, NseIndexOptionExposure(), LOT, record)  # fmt: skip
    check = BrokerMarginCheck(parts, session, clock, clock.sleep, alerts, 2.0, printed.append)
    return check, broker, record, alerts, printed, clock
