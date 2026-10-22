"""Story MS-P1m: C2's stressed margin for the market school's trades, each on its own legs (the pilot's shorts sit
one expected move out, where A14's ATM rows read up to 24% too low; the measure is in the story).

A trade's terms carry its index, expiry, legs and lot (`RoadTradeTerms`, a `TradeTerms`), so C2's `MarginRoom` asks
the margin of every open trade and of the proposal through this one `StressedMargin`, unchanged. Each figure comes from
the session's beginning-of-day SPAN file as A14 reads it: A9's first-archived copy (its SHA-256 equal to the
manifest's), written before 09:00 IST, A14's calculator and exposure rule, C2's STR1 cap and the factor in force from
A14c's file. Anything else refuses by name (`RiskInputError`), so law 3 refuses the trade: no guess, no fallback."""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date

from ..constants import NIFTY_SYMBOL, RECORDED_INDEX_OPTIONS, STRUCTURES_ONE_SIDE
from ..fo_bhavcopy import BadFile
from ..research_engine.structures import Leg
from ..risk.capital import stress_cap_per_lot
from ..risk.inputs import RiskInputError, TradeTerms
from ..risk.margins import MarginParts, StressedMargin
from ..risk.stress_factor import FactorRow
from .calculator import ExposureRule, MarginOutsideModel, SpanMarginCalculator
from .span_file import SpanFile, read_span_file

METHOD = "archived_span_per_trade"
ROAD_UNDERLYINGS = (NIFTY_SYMBOL, *RECORDED_INDEX_OPTIONS)
FACTOR_LABEL = "k measured on NIFTY monthly only [reasoning only]"  # orchestrator, 22 Oct 2026, for every record
NOT_A_ROAD_TRADE = "school margin: {terms} carries no legs (RoadTradeTerms is required)"
REFUSED = "school margin {what}: {why}"


@dataclass(frozen=True)
class RoadTradeTerms(TradeTerms):
    """A school trade: C2's terms plus the index, the expiry, the legs and the units per lot it was entered with."""

    underlying: str
    expiry: date
    legs: tuple[Leg, ...]
    lot: int

    def __post_init__(self):
        super().__post_init__()
        if self.underlying not in ROAD_UNDERLYINGS or self.lot <= 0 or not self.legs:
            raise RiskInputError(f"school margin: {self.underlying} lot {self.lot} with {len(self.legs)} legs")
        strikes = sorted({leg.strike for leg in self.legs})
        if self.structure in STRUCTURES_ONE_SIDE and strikes[-1] - strikes[0] != self.width:
            raise RiskInputError(f"school margin: {self.structure} legs are {strikes[-1] - strikes[0]:g} wide, not "
                                 f"{self.width:g} (C2's cap reads the width)")  # fmt: skip

    @property
    def what(self) -> str:
        return f"{self.underlying} {self.structure} {self.width:g} {self.expiry}"


@dataclass(frozen=True)
class ArchivedSpanSource:
    day_file: Callable[[date], tuple[str, bytes | None]]  # the session's first-archived beginning-of-day file
    manifest: Callable[[], Mapping[date, str]]  # A9's manifest: session -> SHA-256
    exposure: ExposureRule
    factor: Callable[[date], FactorRow]  # C2's factor in force on the day (A14c's file)


class ArchivedSpanMargin(StressedMargin):
    method = METHOD

    def __init__(self, source: ArchivedSpanSource):
        self.source = source
        self._files: dict[date, tuple[str, str, bytes]] = {}
        self._spans: dict[tuple[date, str], SpanFile] = {}

    def margin(self, terms: TradeTerms, day: date) -> float:
        return self.parts(terms, day).stressed(self.source.factor(day).factor) * terms.lots

    def margin_at_entry(self, terms: TradeTerms, day: date) -> float:
        return self.parts(terms, day).at_entry(self.source.factor(day).factor) * terms.lots

    def broker_margin(self, terms: TradeTerms, day: date) -> float:
        return self.parts(terms, day).at_entry(1.0) * terms.lots

    def record(self, day: date | None = None) -> dict[str, str]:
        """The method, the factor row in force and its label; with a day, the file it reads."""
        found = {"method": self.method, "factor_label": FACTOR_LABEL}
        if day is None:
            return found
        name, sha256, _ = self._file(day)
        return found | self.source.factor(day).record() | {"span_file": name, "span_sha256": sha256}

    def trade_record(self, terms: TradeTerms, day: date) -> dict[str, str]:
        """What the dashcam seals for one trade: its legs and lot, the per-lot figures and the file they came from."""
        road, parts = _road(terms), self.parts(terms, day)
        legs = " ".join(f"{leg.side:+d}x{leg.strike:g}{leg.kind}" for leg in road.legs)
        return self.record(day) | {"underlying": road.underlying, "expiry": road.expiry.isoformat(), "legs": legs,
                                   "lot": str(road.lot), "scan_per_lot_rs": f"{parts.scan:.2f}",
                                   "nov_per_lot_rs": f"{parts.nov:.2f}",
                                   "exposure_per_lot_rs": f"{parts.exposure:.2f}"}  # fmt: skip

    def parts(self, terms: TradeTerms, day: date) -> MarginParts:
        road = _road(terms)
        try:
            figure = SpanMarginCalculator(self.source.exposure, road.lot).per_lot(
                self._span(day, road.underlying), road.expiry, road.legs, day
            )
        except MarginOutsideModel as exc:  # expiry day, beyond 9 months, a leg not in the file, two scan tiers
            raise RiskInputError(REFUSED.format(what=road.what, why=exc)) from exc
        cap = stress_cap_per_lot(road.structure, road.width, figure.nov, road.lot)
        return MarginParts(figure.span, figure.nov, figure.exposure, road.what, road.bought_only, cap)

    def _span(self, day: date, underlying: str) -> SpanFile:
        if (day, underlying) not in self._spans:
            name, _, data = self._file(day)
            try:
                span = read_span_file(data, name, symbol=underlying, allow_short_option_minimum=True)
            except BadFile as exc:  # damaged, or the index's margin method is not the one modelled
                raise RiskInputError(REFUSED.format(what=name, why=exc)) from exc
            if not span.written_in_time(day):
                raise RiskInputError(REFUSED.format(what=name, why=f"written {span.created:%Y-%m-%d %H:%M}, not "
                                                                    f"before 09:00 on {day}"))  # fmt: skip
            self._spans[(day, underlying)] = span
        return self._spans[(day, underlying)]

    def _file(self, day: date) -> tuple[str, str, bytes]:
        """The day's file once per session, proved to be the first-archived copy."""
        if day not in self._files:
            try:
                name, data = self.source.day_file(day)
            except OSError as exc:  # Drive unreachable or refusing: the class name only
                raise RiskInputError(
                    REFUSED.format(what=day, why=f"the archive could not be read ({type(exc).__name__})")
                ) from exc
            if data is None:
                raise RiskInputError(REFUSED.format(what=name, why="not in the archive"))
            sha256, expected = hashlib.sha256(data).hexdigest(), self.source.manifest().get(day)
            if sha256 != expected:
                raise RiskInputError(REFUSED.format(what=name, why="differs from its manifest SHA-256"))
            self._files[day] = (name, sha256, data)
        return self._files[day]


def _road(terms: TradeTerms) -> RoadTradeTerms:
    if not isinstance(terms, RoadTradeTerms):
        raise RiskInputError(NOT_A_ROAD_TRADE.format(terms=terms))
    return terms
