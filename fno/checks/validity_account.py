"""A book's account as C4 reads it (story C4, judge 83): straight from its committed E1 cash ledger and the owner's
restart rows, not through E1's or C2's code. Only ledger rows filled by the decision cutoff count, so a replay later
reads the same account. What C4 derives here:
- cash (every amount so far);
- each trade's units and cash flow;
- each trade's first fill day;
- the opening cash, and closed equity at each day's close (the start, then each day a trade went flat);
- the brake restart days."""

from __future__ import annotations

import csv
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from datetime import date, datetime
from pathlib import Path

from ..books.paths import account_folder, book_folder
from ..constants import CASH_LEDGER_FILE, LEDGER_OPENING, OVERRIDE_RESTART_BRAKE, OWNER_OVERRIDES_FILE, SIDE_BUY


@dataclass(frozen=True)
class Position:
    trade_id: str
    units: Mapping[str, int]  # contract -> signed units held (long +, short -)
    cash_flow: float  # premium received minus paid, minus charges, so far
    terms: tuple[str, float, int] | None = None  # structure, width, lots (what its margin row is found by)
    opened_on: date | None = None  # the trade's first fill day (C5's new risk per day)


@dataclass(frozen=True)
class AccountFacts:
    cash: float
    closed_equity: tuple[tuple[date, float], ...]  # (day, closed equity at that day's close), oldest first
    restarts: tuple[date, ...]
    positions: tuple[Position, ...] = field(default_factory=tuple)

    def after_entry(self, position: Position) -> AccountFacts:
        """The account once `position` (a trade chosen earlier the same day) is entered."""
        return replace(self, cash=self.cash + position.cash_flow, positions=(*self.positions, position))


class AccountProblem(ValueError):
    """The account cannot be read: the trade fails closed."""


def _rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise AccountProblem(f"{path.name} is missing: the account has not been started")
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _filled_by(row: dict[str, str], cutoff: datetime) -> bool:
    when = datetime.fromisoformat(row["filled_at"])
    return (when.date() <= cutoff.date()) if when.tzinfo is None else when <= cutoff


def _trades(rows: list[dict[str, str]]) -> tuple[dict[str, dict], dict[str, float], dict[str, date | None], dict]:
    units: dict[str, dict[str, int]] = {}
    flows: dict[str, float] = {}
    flat_on: dict[str, date | None] = {}
    first: dict[str, date] = {}
    for row in rows:
        trade, sign = row["trade_id"], 1 if row["side"] == SIDE_BUY else -1
        filled = datetime.fromisoformat(row["filled_at"]).date()
        first[trade] = min(filled, first.get(trade, filled))
        held = units.setdefault(trade, {})
        held[row["contract"]] = held.get(row["contract"], 0) + sign * int(row["units"])
        flows[trade] = flows.get(trade, 0.0) + float(row["amount_rs"])
        flat = not any(held.values())
        flat_on[trade] = datetime.fromisoformat(row["filled_at"]).date() if flat else None
    return units, flows, flat_on, first


def account_facts(rows: list[dict[str, str]], restarts: tuple[date, ...], cutoff: datetime) -> AccountFacts:
    rows = [r for r in rows if _filled_by(r, cutoff)]
    if not rows or rows[0]["kind"] != LEDGER_OPENING:
        raise AccountProblem("the ledger has no opening balance by the decision cutoff")
    start, fills = rows[0], rows[1:]
    units, flows, flat_on, first = _trades(fills)
    by_day: dict[date, float] = {}
    for trade, day in flat_on.items():
        if day is not None:
            by_day[day] = by_day.get(day, 0.0) + flows[trade]
    equity = float(start["amount_rs"])
    series = [(datetime.fromisoformat(start["filled_at"]).date(), equity)]
    for day in sorted(by_day):
        equity += by_day[day]
        series.append((day, equity))
    positions = tuple(
        Position(t, {c: n for c, n in held.items() if n}, flows[t], None, first[t])
        for t, held in units.items()
        if flat_on[t] is None
    )
    return AccountFacts(sum(float(r["amount_rs"]) for r in rows), tuple(series), restarts, positions)


def restart_days(rows: list[dict[str, str]], day: date) -> tuple[date, ...]:
    """The owner's restart rows dated on or before `day`; any other action is malformed and fails closed."""
    days = []
    for row in rows:
        if row.get("action") != OVERRIDE_RESTART_BRAKE or not (row.get("reason") or "").strip():
            raise AccountProblem(f"{OWNER_OVERRIDES_FILE}: malformed row {row}")
        days.append(date.fromisoformat(row["date"]))
    return tuple(sorted(d for d in days if d <= day))


class LedgerAccounts:
    def __init__(self, root: Path):
        self.root = Path(root)

    def facts(self, book: str, cutoff: datetime) -> AccountFacts:
        overrides = book_folder(self.root, book) / OWNER_OVERRIDES_FILE
        restarts = restart_days(_rows(overrides), cutoff.date()) if overrides.is_file() else ()
        return account_facts(_rows(account_folder(self.root, book) / CASH_LEDGER_FILE), restarts, cutoff)
