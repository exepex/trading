"""Margin room as C4 recomputes it (story C4, judge 83), on A14's three-part margins file. Each row holds, per lot, a
structure and width's SPAN scan, net option value (NOV) and exposure margin, with source and date.

- Stressed margin per lot: max(0, k x scan - NOV) + min(0, NOV) + exposure, with k the owner's stressed-margin
  multiplier (which needs its source and date). A total not above 0 is refused, except 0 for a bought-only
  structure (LC, LP: NSE blocks no margin on a paid-up long option; story STR1).
- Needed: every open trade's stressed margin, plus those of the trades chosen earlier the same day, plus the
  proposal's.
- Available after the entry: the least of
  - cash + the entry's cash flow;
  - marked equity + the entry's cash flow + its marked value;
  - cash + the entry's cash flow + every trade's own liability (the value of each trade worth less than zero);
  then less the premium reserved for pending orders.

A missing, stale or unsourced row, or factor, fails closed. So does a method other than `multiplier`: C4 has no
scenario-lookup arithmetic.
"""

from __future__ import annotations

import csv
from collections.abc import Sequence
from datetime import date
from pathlib import Path

from ..constants import STRESSED_MARGIN_MULTIPLIER, STRUCTURES_BOUGHT_ONLY
from .validity_account import Position
from .validity_chain import PricedChain
from .validity_proposal import CheckResult
from .validity_settings import MarginSettings
from .validity_stress import marked

COLUMNS = ("structure", "width", "scan_per_lot_rs", "nov_per_lot_rs", "exposure_per_lot_rs", "source", "as_of")
NAME = "margin_room"


class MarginProblem(ValueError):
    """No usable margin: the trade fails closed."""


class MarginFile:
    def __init__(self, path: Path):
        self.path = path

    def rows(self) -> list[dict[str, str]]:
        if not self.path.is_file():
            raise MarginProblem(f"{self.path.name} is missing")
        with open(self.path, encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            if tuple(reader.fieldnames or ()) != COLUMNS:
                raise MarginProblem(f"{self.path.name}: columns must be A14's {', '.join(COLUMNS)}")
            return list(reader)


def multiplier(settings: MarginSettings, day: date) -> float:
    if settings.method != STRESSED_MARGIN_MULTIPLIER:
        raise MarginProblem(f"stressed margin method {settings.method!r}: C4 checks the multiplier method only")
    if settings.multiplier is None or not settings.source or settings.as_of is None:
        raise MarginProblem("stressed margin multiplier is not set (factor, source and as_of are all required)")
    if settings.as_of > day or (day - settings.as_of).days > settings.multiplier_max_age_days:
        raise MarginProblem(f"stressed margin multiplier of {settings.as_of} is not valid on {day}")
    return settings.multiplier


def stressed_per_lot(rows, terms: tuple[str, float, int], day: date, settings: MarginSettings) -> float:
    structure, width, _ = terms
    usable = [
        r for r in rows
        if r["structure"] == structure and float(r["width"]) == width and r["source"].strip()
        and date.fromisoformat(r["as_of"]) <= day
    ]  # fmt: skip
    if not usable:
        raise MarginProblem(f"no margin row for {structure} {width:g} on or before {day}")
    row = max(usable, key=lambda r: r["as_of"])
    if not settings.fresh(date.fromisoformat(row["as_of"]), day):
        raise MarginProblem(f"margin for {structure} {width:g} is from {row['as_of']}, too old on {day}")
    scan, nov, exposure = (float(row[k]) for k in ("scan_per_lot_rs", "nov_per_lot_rs", "exposure_per_lot_rs"))
    per_lot = max(0.0, multiplier(settings, day) * scan - nov) + min(0.0, nov) + exposure
    if per_lot < 0 or (per_lot == 0 and structure not in STRUCTURES_BOUGHT_ONLY):
        raise MarginProblem(f"margin for {structure} {width:g} on {row['as_of']} is not above 0")
    return per_lot


def _terms(position: Position) -> tuple[str, float, int]:
    if position.terms is None:
        raise MarginProblem(f"open trade {position.trade_id} has no recorded terms (structure, width, lots)")
    return position.terms


def margin_check(
    held: Sequence[Position], proposal: Position, cash: float, premium_reserved: float, chain: PricedChain,
    rows, settings: MarginSettings, day: date,
) -> CheckResult:  # fmt: skip
    """`held`: the open trades and the trades chosen earlier the same day; `cash` already holds their entries."""
    needed = {p.trade_id: stressed_per_lot(rows, _terms(p), day, settings) * _terms(p)[2] for p in (*held, proposal)}
    values = [marked(p, chain) for p in held]
    own = marked(proposal, chain)
    entry = cash + proposal.cash_flow
    liabilities = sum(min(0.0, v) for v in values) + min(0.0, own)
    after = min(entry, entry + sum(values) + own, entry + liabilities) - premium_reserved
    total = sum(needed.values())
    numbers = {"stressed_margin_rs": {k: round(v, 2) for k, v in needed.items()}, "needed_rs": round(total, 2),
               "available_after_entry_rs": round(after, 2)}  # fmt: skip
    reason = f"stressed margin Rs {total:,.2f} against Rs {after:,.2f} available after entry"
    return CheckResult(NAME, total <= after, reason, numbers)
