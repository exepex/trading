"""Cause 8's market-wide move (story MS-INS, part c): each of the four index underlyings' `z` over the same sessions,
from its own monthly road's recorded snapshots and its own ATM volatility. NIFTY's weekly road shares NIFTY's move."""

from datetime import date

from ...constants import RoadCode
from ..attribution.points import forward_of, years_left
from ..ports import SnapshotArchive
from .terms import atm_volatility, move_z

MARKET_ROADS = (RoadCode.NIFTY_MONTHLY, RoadCode.BANKNIFTY_MONTHLY, RoadCode.FINNIFTY_MONTHLY,
                RoadCode.MIDCPNIFTY_MONTHLY)  # fmt: skip


def market_moves(archive: SnapshotArchive, first: date, last: date, rate: float) -> tuple[float, ...]:
    """The `z` of every underlying measurable from `first` to `last` (both recorded, a positive time apart)."""
    moves = []
    for road in MARKET_ROADS:
        start, end = archive.snapshot(road, first), archive.snapshot(road, last)
        if start is None or end is None or not start.expiries:
            continue
        expiry = start.expiries[0]
        sigma = atm_volatility(start, expiry, forward_of(start, expiry, rate), rate)
        held = years_left(start.finished_at, expiry) - years_left(end.finished_at, expiry)
        z = move_z(start.spot, end.spot, sigma, held)
        moves += [z] if z is not None else []
    return tuple(moves)
