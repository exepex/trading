"""The snapshot at a due mark (story E8 rule 3): A16's copy of that mark, the one its ledger row names, hash checked;
or, when that mark is missing or failed, a recorded A4 capture that started inside the mark's 2-minute window (for
example E3's 15:15 execution capture). Never a neighbouring mark.

A16's quotes become E4's `ExecutionQuote`s through A4's own parser and validity rule (`parse_groww_quote_book`,
`quote_validity`), never a second copy of either; "a trade that session" is read from the quote's last trade time. A
quote requested before the mark is dropped: no fill uses a price from before T + R."""

from __future__ import annotations

import hashlib
import re
from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import date, datetime, timedelta
from pathlib import Path

from ...intraday.document import CallRecord, SnapshotDocument, utc_text
from ...intraday.groww_source import PARSE_ERRORS
from ...intraday.ledger import SlotLedger
from ...intraday.slots import ON_TIME_SECONDS
from ...intraday.status import GOOD, INCOMPLETE, STALE
from ...models import IST
from ...providers.groww import parse_groww_quote_book
from ...quotes.recorder import quote_validity
from ...storage.raw_store import RawFileStore
from ..snapshot import ExecutionQuote, ExecutionSnapshot, ExecutionSnapshotSource, SnapshotError

USABLE = (GOOD, INCOMPLETE, STALE)  # a late copy was taken minutes after its mark: never used for that mark
CAPTURE_NAME = re.compile(r"nifty_(\d{8})_(\d{6})\.meta\.json")


class MarkSnapshots(ABC):
    @abstractmethod
    def at(self, day: date, mark: datetime) -> ExecutionSnapshot | None:
        """The snapshot of that mark, None when there is none; `SnapshotError` when one exists but fails its checks."""


class IntradayMarkSnapshots(MarkSnapshots):
    def __init__(self, store: RawFileStore, ledger: SlotLedger):
        self.store, self.ledger = store, ledger

    def at(self, day: date, mark: datetime) -> ExecutionSnapshot | None:
        row = next((r for r in self.ledger.rows(day) if r["mark"] == utc_text(mark)), None)
        if row is None or row["status"] not in USABLE or not row["raw_path"]:
            return None
        data = self.store.get(row["raw_path"])
        if not data:
            return None
        if hashlib.sha256(data).hexdigest() != row["raw_sha256"]:
            raise SnapshotError(f"A16 copy {row['raw_path']} does not match its ledger hash")
        doc = SnapshotDocument.from_bytes(data)
        if doc.session != day or doc.mark != mark:
            raise SnapshotError(f"A16 copy {row['raw_path']} is not the {day} {mark:%H:%M} mark")
        quotes = [q for q in (_quote(call, day, mark) for call in doc.quotes) if q is not None]
        return ExecutionSnapshot(
            day, Path(row["raw_path"]).name, row["raw_sha256"], "", mark, doc.finished_at or mark,
            not doc.failures, {(q.expiry, q.strike, q.kind): q for q in quotes},
        )  # fmt: skip


def _quote(call: CallRecord, day: date, mark: datetime) -> ExecutionQuote | None:
    if call.failure or not isinstance(call.payload, dict) or call.request_sent_at < mark:
        return None
    meta = call.meta
    try:
        book = parse_groww_quote_book(meta["symbol"], call.payload)
        expiry, strike, kind = date.fromisoformat(meta["expiry"]), float(meta["strike"]), meta["type"]
    except PARSE_ERRORS:
        return None  # an unreadable answer is a missing quote, never a guessed one
    reason = quote_validity(book, day)
    return ExecutionQuote(
        book.symbol, expiry, strike, kind, book.bid, book.ask, book.bid_qty, book.ask_qty, not reason, reason,
        book.quote_time is None,
    )  # fmt: skip


class CaptureStandIn(MarkSnapshots):
    """A recorded A4 capture whose start lies inside the mark's on-time window (A16's 2 minutes)."""

    def __init__(self, captures: ExecutionSnapshotSource, capture_names: Callable[[date], list[str]]):
        self.captures, self.capture_names = captures, capture_names

    def at(self, day: date, mark: datetime) -> ExecutionSnapshot | None:
        window_end = mark + timedelta(seconds=ON_TIME_SECONDS)
        for name in sorted(self.capture_names(day)):
            found = CAPTURE_NAME.fullmatch(name)
            started = datetime.strptime("".join(found.groups()), "%Y%m%d%H%M%S").replace(tzinfo=IST) if found else None
            if started is not None and mark <= started <= window_end:
                snapshot = self.captures.snapshot(day, name.removesuffix(".meta.json"))
                if mark <= snapshot.started_at <= window_end:
                    return snapshot
        return None


class FirstAvailable(MarkSnapshots):
    """A16's mark first, then the stand-in."""

    def __init__(self, *sources: MarkSnapshots):
        self.sources = sources

    def at(self, day: date, mark: datetime) -> ExecutionSnapshot | None:
        for source in self.sources:
            found = source.at(day, mark)
            if found is not None:
                return found
        return None
