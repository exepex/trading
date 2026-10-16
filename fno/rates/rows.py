"""The rates table's rows (story A21): one per auction yield and one per repo-rate change, each with the time it was
first seen (the response's arrival, judge 355 addendum 1). Rows only grow: a value already recorded is never written
again."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime

from .constants import HOME_NOTE, LIVE, POLICY_REPO, RBI_HOME, RBI_RELEASE, TBILL_RATES
from .pages import CurrentRates, TbillAuction


@dataclass(frozen=True)
class RateRow:
    rate: str
    value_date: str  # the auction date, or the day the repo rate was first seen
    value_pct: str
    release_no: str
    source_url: str
    source_sha256: str
    first_seen_at: str  # ISO time with offset
    provenance: str
    note: str

    def as_dict(self) -> dict:
        return asdict(self)

    @property
    def seen_at(self) -> datetime:
        return datetime.fromisoformat(self.first_seen_at)

    @property
    def value(self) -> float:
        return float(self.value_pct)


def from_dicts(rows: list[dict]) -> list[RateRow]:
    return [RateRow(**row) for row in rows]


def auction_rows(auction: TbillAuction, sha256: str, seen_at: datetime) -> list[RateRow]:
    url = RBI_RELEASE.format(prid=auction.prid)
    return [RateRow(rate, auction.auction_date.isoformat(), f"{value:.4f}", auction.release_no, url, sha256,
                    seen_at.isoformat(), LIVE, f"prid={auction.prid}")
            for rate, value in zip(TBILL_RATES, auction.yields_pct, strict=True)]  # fmt: skip


def repo_row(current: CurrentRates, sha256: str, seen_at: datetime) -> RateRow:
    return RateRow(POLICY_REPO, seen_at.date().isoformat(), f"{current.policy_repo_pct:.2f}", "", RBI_HOME, sha256,
                   seen_at.isoformat(), LIVE, HOME_NOTE)  # fmt: skip


def recorded_prids(rows: list[RateRow]) -> set[int]:
    return {int(row.note.removeprefix("prid=")) for row in rows if row.note.startswith("prid=")}


def latest(rows: list[RateRow], rate: str) -> RateRow | None:
    mine = [row for row in rows if row.rate == rate]
    return max(mine, key=lambda row: (row.seen_at, row.value_date)) if mine else None
