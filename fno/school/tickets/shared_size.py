"""Shared displayed size (327 item 10): many paper accounts do not share one order book. Each account's fill is
priced on its own against the full displayed size (E4d per account), so a report must never sum fills that the same
displayed size could not have served together.

`allocate` serves whole fills, never part of one (fills are all legs or none): in a fixed order (owner, then the
order given), each fill is servable only if every leg's units still fit in what its contract and side showed. A
report sums only the servable fills and names the rest."""

from collections.abc import Iterable
from dataclasses import dataclass

from ...constants import SIDE_BUY
from ..contracts.accounts import FillResult
from ..contracts.snapshot import ContractKey, SlotSnapshot


@dataclass(frozen=True)
class OwnedFill:
    owner: str  # the driver version (or a ticket ledger's label) whose fill it is
    fill: FillResult


@dataclass(frozen=True)
class SizeAllocation:
    servable: tuple[OwnedFill, ...]
    unservable: tuple[OwnedFill, ...]  # each would need size an earlier fill already used

    @property
    def contended(self) -> bool:
        return bool(self.unservable)


def allocate(fills: Iterable[OwnedFill], snapshot: SlotSnapshot) -> SizeAllocation:
    """`fills`: every filled entry or exit at this snapshot (an exit and a re-entry of one owner may both be there);
    refusals and states use no size and are left out."""
    left: dict[tuple[ContractKey, str], int] = {}
    servable, unservable = [], []
    filled = [owned for owned in fills if owned.fill.filled]
    for owned in sorted(filled, key=lambda o: o.owner):  # stable: one owner's fills keep their given order
        needs = [((leg.key, leg.side), leg.units) for leg in owned.fill.legs]
        for place, _ in needs:
            left.setdefault(place, _displayed(snapshot, *place))
        if all(units <= left[place] for place, units in needs):
            for place, units in needs:
                left[place] -= units
            servable.append(owned)
        else:
            unservable.append(owned)
    return SizeAllocation(tuple(servable), tuple(unservable))


def _displayed(snapshot: SlotSnapshot, key: ContractKey, side: str) -> int:
    quote = snapshot.quote(key)
    size = None if quote is None else (quote.ask_qty if side == SIDE_BUY else quote.bid_qty)
    return size or 0
