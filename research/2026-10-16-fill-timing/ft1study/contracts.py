"""NIFTY monthly expiries, their listed strikes, Groww symbols and final settlement prices, all from the A3 panel
(`research/data/nifty-panel`; study FT1, PROTOCOL.md section 3). A monthly expiry is one with a NIFTY future: NSE
lists futures only on monthly expiries. "The last expiry of the month" is wrong twice in the window (probe, 15 Oct
2026): the weekly of 30 Apr 2025 fell after the 24 Apr monthly, and the March 2026 monthly moved from the 31st (a
holiday) to the 30th. An expiry date the panel covers but on which nothing expired is dropped: NSE re-dated those
contracts (25 Sep 2025 became 30 Sep with the move to Tuesday expiries). Weekly expiries are never used."""

from __future__ import annotations

import csv
import gzip
from collections import defaultdict
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[3]
PANEL = REPOSITORY / "research" / "data" / "nifty-panel"
OPTION_SYMBOL = "NSE-NIFTY-{expiry:%d%b%y}-{strike}-{kind}"
FUTURE_SYMBOL = "NSE-NIFTY-{expiry:%d%b%y}-FUT"


def option_symbol(expiry: date, strike: float, kind: str) -> str:
    return OPTION_SYMBOL.format(expiry=expiry, strike=_strike_text(strike), kind=kind)


def future_symbol(expiry: date) -> str:
    return FUTURE_SYMBOL.format(expiry=expiry)


def _strike_text(strike: float) -> str:
    return str(int(strike)) if float(strike).is_integer() else f"{strike:g}"


@dataclass
class MonthlyContracts:
    """Per monthly expiry: the contracts listed on each session, the index close of each session and the settlement."""

    listed: dict[date, dict[date, frozenset]] = field(default_factory=lambda: defaultdict(dict))  # expiry, day: chain
    closes: dict[date, float] = field(default_factory=dict)  # session -> Nifty 50 close (panel `underlying`)
    settlement: dict[date, float] = field(default_factory=dict)  # expiry -> final settlement price

    @property
    def expiries(self) -> list[date]:
        return sorted(self.listed)

    def nearest(self, day: date, sessions_after, min_sessions: int) -> date | None:
        """The nearest monthly expiry with more than `min_sessions` sessions after `day` up to and including it."""
        return next((e for e in self.expiries if e > day and sessions_after(day, e) > min_sessions), None)


def read_panel(years: Iterable[int], folder: Path = PANEL) -> MonthlyContracts:
    years = tuple(years)
    rows = [r for year in years for r in _rows(folder / f"options_{year}.csv.gz")]
    monthly = {date.fromisoformat(r["expiry"]) for year in years for r in _rows(folder / f"futures_{year}.csv.gz")}
    found = MonthlyContracts()
    chains: dict[tuple[date, date], set] = defaultdict(set)
    for r in rows:
        day, expiry = date.fromisoformat(r["date"]), date.fromisoformat(r["expiry"])
        found.closes[day] = float(r["underlying"])
        if expiry not in monthly:
            continue
        chains[(expiry, day)].add((float(r["strike"]), r["type"]))
        if day == expiry:
            found.settlement.setdefault(expiry, set()).add(float(r["settle"]))
    last_day = max(found.closes)
    dead = {e for e in monthly if e <= last_day and e not in found.settlement}
    for (expiry, day), chain in chains.items():
        if expiry in dead:
            continue
        found.listed[expiry][day] = frozenset(chain)
    found.settlement = {e: _one_price(e, prices) for e, prices in found.settlement.items()}
    return found


def _rows(path: Path) -> Iterator[dict[str, str]]:
    if path.is_file():
        with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
            yield from csv.DictReader(handle)


class SettlementDisagrees(ValueError):
    """The expiry day's rows give more than one settlement price: refused, never guessed (E7's rule)."""


def _one_price(expiry: date, prices: set[float]) -> float:
    if len(prices) != 1:
        raise SettlementDisagrees(f"{expiry}: {len(prices)} different settlement prices")
    return prices.pop()
