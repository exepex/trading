"""Shared displayed size (327 item 10): many paper accounts do not share one order book. Each account's fill is
priced on its own against the full displayed size (E4d per account), so a report must never sum fills that the same
displayed size could not have served together. This counts, per contract and side at one snapshot, the units all
accounts took against the size shown."""

from collections.abc import Mapping
from dataclasses import dataclass

from ...constants import SIDE_BUY
from ..contracts.accounts import FillResult
from ..contracts.snapshot import ContractKey, SlotSnapshot


@dataclass(frozen=True)
class SizeClaim:
    key: ContractKey
    side: str
    displayed: int  # the ask size for a buy, the bid size for a sell
    wanted: int  # units every account filled there
    accounts: tuple[str, ...]

    @property
    def servable(self) -> int:
        return min(self.wanted, self.displayed)

    @property
    def excess(self) -> int:
        return self.wanted - self.servable


def size_claims(fills: Mapping[str, FillResult], snapshot: SlotSnapshot) -> tuple[SizeClaim, ...]:
    """`fills`: each driver version's filled entries or exits at this snapshot (refusals add nothing)."""
    taken: dict[tuple, tuple[int, list[str]]] = {}
    for driver_id in sorted(fills):
        for leg in fills[driver_id].legs:
            units, who = taken.get((leg.key, leg.side), (0, []))
            taken[(leg.key, leg.side)] = (units + leg.units, [*who, driver_id])
    return tuple(SizeClaim(key, side, _displayed(snapshot, key, side), units, tuple(dict.fromkeys(who)))
                 for (key, side), (units, who) in sorted(taken.items()))  # fmt: skip


def servable_units(claims: tuple[SizeClaim, ...]) -> int:
    """The fleet's units a report may sum: never more than each contract and side showed."""
    return sum(claim.servable for claim in claims)


def _displayed(snapshot: SlotSnapshot, key: ContractKey, side: str) -> int:
    quote = snapshot.quote(key)
    size = None if quote is None else (quote.ask_qty if side == SIDE_BUY else quote.bid_qty)
    return size or 0
