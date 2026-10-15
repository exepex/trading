"""The snapshot's legs, rebuilt by the run from the raw Drive file and the previous session's F&O file (judge 109
addendum 2, should-fixes 2-3): the run applies amendment 2 item 10's 20% "no previous-session row" rule itself, and
names the snapshot it used by its Drive path and SHA-256."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import date, datetime

from fno.providers.groww import parse_groww_quote_book

from .bhav import Chain
from .spreads import QuotedLeg

MAX_NO_PREVIOUS_ROW_SHARE = 0.20  # amendment 2 item 10: above this the capture is not used


class SnapshotMismatch(RuntimeError):
    """The raw file's SHA-256 is not the one `snapshot.py` printed when it was taken."""


@dataclass
class SnapshotLegs:
    path: str
    sha256: str
    taken: str  # the capture's start time (IST)
    legs: list[QuotedLeg] = field(default_factory=list)
    no_previous_row: int = 0
    stocks: int = 0
    skipped_stocks: int = 0

    @property
    def no_row_share(self) -> float:
        return self.no_previous_row / len(self.legs) if self.legs else 1.0

    @property
    def usable(self) -> bool:
        """Some legs, and at most 20% of them without a previous-session row."""
        return bool(self.legs) and self.no_row_share <= MAX_NO_PREVIOUS_ROW_SHARE

    def record(self) -> dict:
        return {
            "drive_path": self.path,
            "sha256": self.sha256,
            "taken": self.taken,
            "stocks": self.stocks,
            "stocks_skipped": self.skipped_stocks,
            "legs": len(self.legs),
            "legs_without_previous_row": self.no_previous_row,
            "no_row_share": self.no_row_share,
            "used": self.usable,
        }


def taken_on(raw_bytes: bytes) -> date:
    return datetime.fromisoformat(json.loads(raw_bytes)["started"]).date()


def rebuild(raw_bytes: bytes, path: str, expected_sha256: str, chains: dict[str, dict[date, Chain]]) -> SnapshotLegs:
    """Legs from every quoted payload; `chains` is the previous session's option rows (symbol -> expiry -> chain)."""
    sha = hashlib.sha256(raw_bytes).hexdigest()
    if sha != expected_sha256:
        raise SnapshotMismatch(f"{path}: SHA-256 {sha} is not the one recorded when it was taken")
    raw = json.loads(raw_bytes)
    out = SnapshotLegs(path, sha, raw["started"])
    for stock in raw["stocks"]:
        if "skipped" in stock:
            out.skipped_stocks += 1
            continue
        out.stocks += 1
        chain = chains.get(stock["symbol"], {}).get(date.fromisoformat(stock["expiry"]), {})
        for quote in stock["quotes"]:
            book = parse_groww_quote_book(quote["trading_symbol"], quote["payload"])
            row = chain.get((float(quote["strike"]), quote["kind"]))
            out.no_previous_row += row is None
            out.legs.append(
                QuotedLeg(abs(quote["steps"]), row.contracts if row else 0.0, book.bid, book.ask, book.bid_qty,
                          book.ask_qty, stock["lot"])
            )  # fmt: skip
    return out


def symbols(raw_bytes: bytes) -> set[str]:
    return {s["symbol"] for s in json.loads(raw_bytes)["stocks"] if "skipped" not in s}
