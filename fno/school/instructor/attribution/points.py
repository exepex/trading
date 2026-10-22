"""The market state of a held position at each recorded point (story MS-INS, part b): each leg's mid and implied
volatility, each expiry's forward and the time left, read from a verified snapshot or, for a settled position, from
the settlement price at the expiry's 15:30 close (mid = intrinsic value, no time and no volatility left)."""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime, time

from ....models import IST
from ....price_distribution.forward import averaged_forward
from ...constants import OptionKind
from ...contracts.snapshot import ContractKey, SlotSnapshot
from .greeks import implied_vol

EXPIRY_CLOSE = time(15, 30)
MINUTES_PER_YEAR = 365 * 24 * 60


@dataclass(frozen=True)
class Point:
    years: dict[date, float]  # time to each expiry's close
    forwards: dict[date, float | None]  # None: no call and put pair to read it from
    mids: dict[ContractKey, float | None]  # None: no two-sided quote
    sigmas: dict[ContractKey, float | None]  # None: no quote, no forward, or no solvable volatility

    def complete(self, keys: Iterable[ContractKey]) -> bool:
        return all(self.mids.get(k) is not None for k in keys)


def years_left(at: datetime, expiry: date) -> float:
    close = datetime.combine(expiry, EXPIRY_CLOSE, IST)
    return max((close - at).total_seconds() / 60, 0.0) / MINUTES_PER_YEAR


def snapshot_point(snapshot: SlotSnapshot, keys: tuple[ContractKey, ...], rate: float) -> Point:
    expiries = sorted({k.expiry for k in keys})
    years = {e: years_left(snapshot.finished_at, e) for e in expiries}
    forwards = {e: averaged_forward(_pairs(snapshot, e), rate, (e - snapshot.session).days) for e in expiries}
    mids = {k: q.mid if (q := snapshot.quote(k)) else None for k in keys}
    sigmas = {k: _sigma(mids[k], forwards[k.expiry], k, years[k.expiry], rate) for k in keys}
    return Point(years, forwards, mids, sigmas)


def settlement_point(settlement: float, keys: tuple[ContractKey, ...]) -> Point:
    expiries = {k.expiry for k in keys}
    return Point({e: 0.0 for e in expiries}, {e: settlement for e in expiries},
                 {k: intrinsic(k, settlement) for k in keys}, {k: None for k in keys})  # fmt: skip


def intrinsic(key: ContractKey, level: float) -> float:
    return max(level - key.strike, 0.0) if key.kind == OptionKind.CALL else max(key.strike - level, 0.0)


def _sigma(mid, forward, key: ContractKey, years: float, rate: float) -> float | None:
    if mid is None or forward is None:
        return None
    return implied_vol(mid, forward, key.strike, key.kind.value, years, rate)


def _pairs(snapshot: SlotSnapshot, expiry: date) -> list[tuple[float, float, float]]:
    """(strike, call mid, put mid) for every strike of the expiry with both sides two-sided: G13's parity input."""
    mids = {(k.strike, k.kind): q.mid for k, q in snapshot.quotes.items() if k.expiry == expiry and q.mid is not None}
    return [(s, c, mids[(s, OptionKind.PUT)]) for (s, kind), c in sorted(mids.items())
            if kind == OptionKind.CALL and (s, OptionKind.PUT) in mids]  # fmt: skip
