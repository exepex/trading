"""The largest rise of a held position's whole margin, entry to exit (story A14c): the quantity the stress factor k
multiplies (story C2c; owner, 15 Oct 2026). Every trading day is an entry, for every structure and width C2 trades,
on A14's expiry rule (the first monthly expiry 30 or more days out); the position is held to the last trading day at
least 21 days before expiry (B2's exit). Each day's margin of the same legs is what C2 counts, at k = 1
(`MarginParts.initial`). Days are fed in order and each file is read once: open positions are carried forward.

A position whose margin cannot be computed on some day (a leg no longer listed, a method outside the model) is
dropped and named, never filled. A position with no margin at entry (a bought option) has no rise."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import date, timedelta

from ..research_engine.cycles import EXIT_MIN_DAYS
from ..research_engine.structures import Leg, Structure
from ..risk.inputs import RiskInputError
from ..risk.margins import MarginParts
from .calculator import MarginOutsideModel, SpanMarginCalculator
from .span_file import SpanFile

MIN_DAYS_TO_EXPIRY = 30  # A14's entry rule (the entry window's near edge)


@dataclass
class Holding:
    structure: str
    width: float
    entry: date
    expiry: date
    exit: date
    legs: Sequence[Leg]
    entry_margin: float
    peak_margin: float = 0.0
    peak_day: date | None = None

    @property
    def rise(self) -> float:
        return self.peak_margin / self.entry_margin


@dataclass
class HeldRises:
    """What a pass found: completed holdings, and the ones dropped with their reason."""

    completed: list[Holding] = field(default_factory=list)
    dropped: list[str] = field(default_factory=list)


class HeldRiseTracker:
    def __init__(self, structures: Sequence[Structure], widths_for: Callable[[Structure], Sequence[float]],
                 calculator: SpanMarginCalculator, is_trading_day: Callable[[date], bool]):  # fmt: skip
        self.structures, self.widths_for, self.calculator = tuple(structures), widths_for, calculator
        self.is_trading_day = is_trading_day
        self.open: list[Holding] = []
        self.found = HeldRises()

    def feed(self, day: date, span: SpanFile, open_new: bool = True) -> None:
        """One day's file: update every open holding, close those exiting today, then open today's entries."""
        for holding in list(self.open):
            self._mark(holding, day, span)
        self.open = [h for h in self.open if h.exit > day]
        if open_new:
            self._open(day, span)

    def _mark(self, holding: Holding, day: date, span: SpanFile) -> None:
        try:
            margin = self._whole(span, holding.expiry, holding.legs, day)
        except (MarginOutsideModel, RiskInputError) as exc:
            self.open.remove(holding)
            self.found.dropped.append(f"{holding.structure} {holding.width:g} entered {holding.entry}: {exc}")
            return
        if margin > holding.peak_margin:
            holding.peak_margin, holding.peak_day = margin, day
        if holding.exit == day:
            self.found.completed.append(holding)

    def _open(self, day: date, span: SpanFile) -> None:
        later = [e for e in span.monthly_expiries if (e - day).days >= MIN_DAYS_TO_EXPIRY]
        if not later:
            return
        expiry = min(later)
        exit_day = self._exit(expiry)
        if exit_day <= day:
            return
        chain = frozenset(span.series.get(expiry, {}))
        for structure in self.structures:
            for width in self.widths_for(structure):
                self._open_one(structure, width, day, span, expiry, exit_day, chain)

    def _open_one(self, structure: Structure, width: float, day: date, span: SpanFile, expiry: date, exit_day: date,
                  chain: frozenset) -> None:  # fmt: skip
        legs = structure.legs(chain, span.underlying, width)
        if legs is None:
            return  # not listed at entry: A14 writes no row for it either
        try:
            margin = self._whole(span, expiry, legs, day)
        except (MarginOutsideModel, RiskInputError):
            return  # no margin at entry (a bought option) or outside the model: nothing to hold
        self.open.append(Holding(structure.code, width, day, expiry, exit_day, legs, margin, margin, day))

    def _whole(self, span: SpanFile, expiry: date, legs: Sequence[Leg], day: date) -> float:
        figure = self.calculator.per_lot(span, expiry, legs, day)
        return MarginParts(figure.span, figure.nov, figure.exposure, "held position").initial()

    def _exit(self, expiry: date) -> date:
        day = expiry - timedelta(days=EXIT_MIN_DAYS)
        while not self.is_trading_day(day):
            day -= timedelta(days=1)
        return day
