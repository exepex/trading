"""One opportunity on 2 Nov 2026 (exit 3 Nov, expiry 24 Nov): a long NIFTY 25000 call bought at the ask of Rs 100
and sold at the bid of Rs 120, one lot of 75, Rs 20 brokerage an order: (120 - 100) x 75 - 2 x 20 = Rs 1,460 net."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from fno.constants import NIFTY_SYMBOL
from fno.risk.open_risk import HeldMaxLoss
from fno.scoreboard.committed_runs import CommittedRuns
from fno.scoreboard.matched_days import CommonPacks
from fno.scoreboard.sources import DaySnapshots
from fno.scoreboard.standard_unit import StandardUnit
from tests.scoreboard.matched_builders import (
    CHARGES,
    LOT,
    Calendar,
    Settlements,
    Snapshots,
    quote,
    write_day,
    write_pack,
)

DAY, EXIT = date(2026, 11, 2), date(2026, 11, 3)
NET = 1460.0
QUOTES = {DAY: [quote(25000, "CE", 98, 100)], EXIT: [quote(25000, "CE", 120, 122)]}


def setup(root: Path, real_run: str | None = None) -> str:
    """The day's common pack and run logs; returns the common pack's SHA-256."""
    pack = write_pack(root, DAY, ("o1", EXIT))
    write_day(root, DAY, {"book2_hybrid": real_run})
    write_day(root, EXIT, {})
    return pack


def unit(root: Path, quotes=None) -> StandardUnit:
    ids = CommittedRuns(root).snapshot_ids()
    return StandardUnit(DaySnapshots(Snapshots(quotes or QUOTES), ids), Calendar().sessions, Settlements(),
                        HeldMaxLoss(CHARGES), CHARGES, LOT)  # fmt: skip


def common(root: Path):
    return CommonPacks(root).day(DAY)


LOTS = {"charges": CHARGES, "lot_sizes": {NIFTY_SYMBOL: LOT}}
