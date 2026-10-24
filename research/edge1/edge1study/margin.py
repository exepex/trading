"""Return on margin at entry (protocol section 9), never a pass condition. One lot's SPAN plus exposure on the entry
day comes from that day's archived SPAN file and C2/A14's calculator, read only:
- the file must be the archive's first copy (SHA-256 equal to A9's manifest) and written before 09:00 IST that day,
  as A14's own runs check;
- it is read with the short-option minimum allowed (history mode);
- the trade's own lot is used, with NSE's index exposure rule and C2's `MarginParts.initial`;
- a missing series or a refused file is a named reason, never a filled figure.
SPAN files start on 2 Jan 2020, so earlier entries have no margin figure."""

from __future__ import annotations

import csv
import hashlib
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from fno.constants import SPAN_BOD_CREATED_BEFORE
from fno.nse_margins.calculator import MarginOutsideModel, NseIndexOptionExposure, SpanMarginCalculator
from fno.nse_margins.span_file import read_span_file
from fno.risk.margins import MarginParts

from .trade import Trade

MANIFEST = Path(__file__).resolve().parents[3] / "research" / "data" / "manifests" / "span-bod.csv"
FIRST_SPAN = date(2020, 1, 2)
NO_FILE, NOT_FIRST_COPY, TOO_LATE, BEFORE_SPAN = "no SPAN file", "not the first-archived copy", "written after 09:00", \
    "before SPAN files (2 Jan 2020)"  # fmt: skip


@dataclass(frozen=True)
class EntryMargin:
    initial: float | None  # rupees per lot, C2's initial margin
    reason: str | None = None


def manifest(path: Path = MANIFEST) -> dict[date, str]:
    with path.open(encoding="utf-8") as f:
        return {date.fromisoformat(r["date"]): r["sha256"] for r in csv.DictReader(f) if r["sha256"]}


def span_on(day_file: Callable[[date], tuple[str, bytes | None]], day: date, sha256: Mapping[date, str],
            symbol: str):  # fmt: skip
    """The day's SPAN file for `symbol`, or the reason it cannot be used."""
    if day < FIRST_SPAN:
        return None, BEFORE_SPAN
    filename, data = day_file(day)
    if data is None or day not in sha256:
        return None, NO_FILE
    if hashlib.sha256(data).hexdigest() != sha256[day]:
        return None, NOT_FIRST_COPY
    span = read_span_file(data, filename, symbol, allow_short_option_minimum=True)
    if span.created >= datetime.combine(day, SPAN_BOD_CREATED_BEFORE, tzinfo=span.created.tzinfo):
        return None, TOO_LATE
    return span, None


def entry_margin(trade: Trade, span, reason: str | None) -> EntryMargin:
    if span is None:
        return EntryMargin(None, reason)
    try:
        figure = SpanMarginCalculator(NseIndexOptionExposure(), trade.lot).per_lot(
            span, trade.cycle.expiry, trade.legs, trade.cycle.entry_day
        )
    except MarginOutsideModel as error:
        return EntryMargin(None, str(error))
    parts = MarginParts(figure.span, figure.nov, figure.exposure, f"{trade.cycle.expiry} {trade.cycle.entry_day}")
    return EntryMargin(parts.initial())


def trade_margins(trades: Iterable[Trade], spans: Mapping[date, tuple]) -> list[EntryMargin]:
    """Each taken trade's entry margin, in order; `spans`: entry day -> (span, reason)."""
    return [entry_margin(t, *spans.get(t.cycle.entry_day, (None, NO_FILE))) for t in trades if t.taken]
