"""A book's account as C4 reads it (story C4, judge 83): straight from its committed E1 cash ledger and the owner's
restart rows, not through E1's or C2's code. Only ledger rows filled by the decision cutoff count, so a replay later
reads the same account. What C4 derives here:
- cash (every amount so far);
- each trade's units and cash flow;
- the trades first filled on the decision day, with their state after each fill time (story C5);
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


State = tuple[Mapping[str, int], float]  # units held and cash flow so far, after one fill time


@dataclass(frozen=True)
class AccountFacts:
    cash: float
    closed_equity: tuple[tuple[date, float], ...]  # (day, closed equity at that day's close), oldest first
    restarts: tuple[date, ...]
    positions: tuple[Position, ...] = field(default_factory=tuple)
    session: tuple[tuple[str, tuple[State, ...]], ...] = ()  # trades first filled on the decision day, open or closed

    def after_entry(self, position: Position) -> AccountFacts:
        """The account once `position` (a trade chosen earlier the same day) is entered."""
        entered = (position.trade_id, ((dict(position.units), position.cash_flow),))
        return replace(
            self, cash=self.cash + position.cash_flow, positions=(*self.positions, position),
            session=(*self.session, entered),
        )  # fmt: skip


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


def _trades(rows: list[dict[str, str]]) -> tuple[dict[str, dict], dict[str, float], dict[str, date | None]]:
    units: dict[str, dict[str, int]] = {}
    flows: dict[str, float] = {}
    flat_on: dict[str, date | None] = {}
    for row in rows:
        trade, sign = row["trade_id"], 1 if row["side"] == SIDE_BUY else -1
        held = units.setdefault(trade, {})
        held[row["contract"]] = held.get(row["contract"], 0) + sign * int(row["units"])
        flows[trade] = flows.get(trade, 0.0) + float(row["amount_rs"])
        flat = not any(held.values())
        flat_on[trade] = datetime.fromisoformat(row["filled_at"]).date() if flat else None
    return units, flows, flat_on


def _session(fills: list[dict[str, str]], day: date) -> tuple[tuple[str, tuple[State, ...]], ...]:
    """Each trade first filled on `day`: its units and cash after each of that day's fill times (story C5)."""
    by_trade: dict[str, list[dict[str, str]]] = {}
    for row in sorted(fills, key=lambda r: datetime.fromisoformat(r["filled_at"])):
        by_trade.setdefault(row["trade_id"], []).append(row)
    out = []
    for trade, rows in by_trade.items():
        if datetime.fromisoformat(rows[0]["filled_at"]).date() != day:
            continue
        units, cash, states = {}, 0.0, {}
        for row in rows:
            sign = 1 if row["side"] == SIDE_BUY else -1
            units[row["contract"]] = units.get(row["contract"], 0) + sign * int(row["units"])
            cash += float(row["amount_rs"])
            states[row["filled_at"]] = ({c: n for c, n in units.items() if n}, cash)
        out.append((trade, tuple(states.values())))
    return tuple(out)


def account_facts(rows: list[dict[str, str]], restarts: tuple[date, ...], cutoff: datetime) -> AccountFacts:
    rows = [r for r in rows if _filled_by(r, cutoff)]
    if not rows or rows[0]["kind"] != LEDGER_OPENING:
        raise AccountProblem("the ledger has no opening balance by the decision cutoff")
    start, fills = rows[0], rows[1:]
    units, flows, flat_on = _trades(fills)
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
        Position(t, {c: n for c, n in held.items() if n}, flows[t]) for t, held in units.items() if flat_on[t] is None
    )
    cash = sum(float(r["amount_rs"]) for r in rows)
    return AccountFacts(cash, tuple(series), restarts, positions, _session(fills, cutoff.date()))


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
