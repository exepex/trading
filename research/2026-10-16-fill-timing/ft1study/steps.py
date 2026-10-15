"""The study's steps (PROTOCOL.md section 19), free of any outside service: the decision days and entries, the fetch
plan and its dry-run share, and the results document."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from .analysis import analyse, observe_all, registered_keys
from .contracts import MonthlyContracts, future_symbol, option_symbol
from .days import DecisionDay, Schedule
from .entries import Entry, IndexLevels, build_entries
from .handcheck import hand_check
from .observe import Observer
from .plan import FetchItem, fetch_plan
from .spreads import spread_caveat
from .times import DECISIONS

TRIAL = "54"
DRY_RUN_DAYS = 5


@dataclass(frozen=True)
class Prepared:
    days: list[DecisionDay]
    days_left_out: Counter
    entries: list[Entry]
    index_missing: Counter  # (decision time, reason) -> days

    def eligible(self) -> dict:
        """Decision time -> days eligible for it (section 4)."""
        return {at: len(self.days) - sum(n for (t, _), n in self.index_missing.items() if t == at) for at in DECISIONS}

    def left_out_lines(self) -> dict[str, int]:
        lines = dict(self.days_left_out)
        lines |= {f"{at:%H:%M} decision: {reason}": n for (at, reason), n in self.index_missing.items()}
        return lines | {"decision days kept": len(self.days)}


def prepare(calendar, contracts: MonthlyContracts, structures: Sequence, index: IndexLevels, first: date,
            last: date) -> Prepared:  # fmt: skip
    days, left_out = Schedule(calendar, contracts).decision_days(first, last)
    entries, missing = build_entries(days, DECISIONS, structures, contracts, index)
    return Prepared(days, left_out, entries, missing)


def dry_run_items(prepared: Prepared) -> list[FetchItem]:
    """The full plan's windows for the contracts of 5 decision days spread over the window, so the full fetch reuses
    them."""
    step = max(1, len(prepared.days) // DRY_RUN_DAYS)
    chosen = {d.day for d in prepared.days[::step][:DRY_RUN_DAYS]}
    wanted = set()
    for e in prepared.entries:
        if e.day.day in chosen:
            wanted.add(future_symbol(e.day.expiry))
            wanted.update(option_symbol(e.day.expiry, leg.strike, leg.kind) for leg in e.legs or ())
    return [item for item in fetch_plan(prepared.entries) if item.symbol in wanted]


def results(prepared: Prepared, observer: Observer, families: Sequence[str], lot: int, snapshots: Sequence[str],
            window: str, run_commit: str) -> dict:  # fmt: skip
    observations = observe_all(prepared.entries, observer, registered_keys(families))
    return {
        "trial": TRIAL, "window": window, "lot": lot, "run_commit": run_commit,
        "days_left_out": prepared.left_out_lines(),
        "analysis": analyse(observations, families, prepared.eligible(), lot),
        "spreads": spread_caveat(snapshots, families),
        "hand_check": hand_check(prepared.days, prepared.entries, observer),
    }  # fmt: skip
