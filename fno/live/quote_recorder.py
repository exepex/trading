"""Records real bid/ask quotes of NIFTY monthly options near the money at about 3 pm IST (story A4).

Only time builds this history: daily NSE files have no bid or ask. Each run is an immutable *attempt* saved under its
capture time; an incomplete attempt may be retried inside the window, and the day's canonical snapshot is the first
complete attempt (or "none"). Quotes are not fills. Never places, modifies or cancels orders.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import time as clock
from dataclasses import dataclass
from datetime import date, datetime, time

from ..models import IST, OptionChain, QuoteBook, now_ist
from ..providers.base import Provider
from ..research_data.expiries import monthly_expiries as last_expiry_of_each_month
from ..storage.raw_store import RawFileStore
from .expiry_listing import ListedExpiries

UNDERLYING = "NIFTY"
DATASET = "groww/derivatives/quote-snapshots"
WINDOW_START, WINDOW_END = time(14, 55), time(15, 10)
MAX_EARLY_WAIT_SECONDS = 20 * 60  # a run started up to 20 minutes early waits for the window
RETRY_GAP_SECONDS = 60
SPOT_BAND = 0.05  # strikes within 5% of spot
MONTHLY_EXPIRIES = 2
WEEKEND_START = 5
NONE_MARKER = "none"
COLUMNS = (
    "snapshot_id", "request_sent_at", "response_received_at", "quote_time", "age_basis", "freshness_proxy",
    "last_trade_time",
    "provider", "contract_id", "expiry", "strike", "type", "bid", "ask", "last", "bid_qty", "ask_qty", "spot",
    "book_source", "valid", "invalid_reason", "raw_sha256",
)  # fmt: skip


def monthly_expiries(expiries: list[date], today: date, count: int = MONTHLY_EXPIRIES) -> list[date]:
    """The nearest `count` monthly contracts: the last listed expiry of each calendar month, from today on."""
    return sorted(last_expiry_of_each_month({e for e in expiries if e >= today}))[:count]


NO_QUOTE_TIME = "unknown: provider gives no quote timestamp"
FRESHNESS_PROXY = "same-day trade (market active; quote age unknown)"


def quote_validity(book: QuoteBook | None, today: date) -> str:
    """Empty when the quote is usable as a two-sided market; otherwise the reason it is not. Groww gives no quote
    timestamp, so the only freshness evidence is a trade in the contract today: without one the book is not valid.
    Even when valid, the quote's age is unknown (not proven to be seconds old)."""
    if book is None:
        return "no quote"
    if not book.bid or not book.ask:
        return "one-sided or empty book"
    if book.bid > book.ask:
        return "crossed (bid above ask)"
    if not book.bid_qty or not book.ask_qty:
        return "no size"
    if book.last_trade_time is None or book.last_trade_time.date() != today:
        return "no trade today (quote age unknown, possibly stale)"
    return ""


@dataclass
class RecordResult:
    status: str  # recorded, already recorded, not a trading day, window closed, too early
    snapshot_id: str = ""
    complete: bool = False
    rows: int = 0


class QuoteSnapshotRecorder:
    def __init__(self, provider: Provider, store: RawFileStore, clock_now=now_ist, sleep=clock.sleep,
                 fallback: ListedExpiries | None = None):  # fmt: skip
        self.provider, self.store, self.now, self.sleep = provider, store, clock_now, sleep
        self.fallback = fallback

    @staticmethod
    def path(day: date, name: str) -> str:
        return f"{DATASET}/{day:%Y}/{day:%m}/{name}"

    def canonical(self, day: date) -> str | None:
        data = self.store.get(self.path(day, f"nifty_{day:%Y%m%d}.canonical"))
        return data.decode().strip() if data else None

    def record(self, outside_window: bool = False) -> RecordResult:
        """One day's recording: waits for the window if early, retries incomplete attempts until the window ends.
        `outside_window` (testing only) makes one attempt now; such an attempt is never canonical."""
        now = self.now()
        day = now.date()
        if now.weekday() >= WEEKEND_START:
            return RecordResult("not a trading day")
        if self.canonical(day) is not None:
            return RecordResult("already recorded", self.canonical(day))
        if outside_window:
            return self._attempt(day, canonical_allowed=False)
        start, end = (datetime.combine(day, t, IST) for t in (WINDOW_START, WINDOW_END))
        if now < start:
            if (start - now).total_seconds() > MAX_EARLY_WAIT_SECONDS:
                return RecordResult("too early")
            self.sleep((start - now).total_seconds())
        result = RecordResult("window closed")
        while self.now() <= end:
            result = self._attempt(day, canonical_allowed=True)
            if result.complete or result.status == "not a trading day":
                return result
            self.sleep(RETRY_GAP_SECONDS)
        if self.canonical(day) is None:
            self.store.put(self.path(day, f"nifty_{day:%Y%m%d}.canonical"), NONE_MARKER.encode())
        return result

    def _attempt(self, day: date, canonical_allowed: bool) -> RecordResult:
        started = self.now()
        snapshot_id = f"nifty_{started:%Y%m%d_%H%M%S}"
        failures, rows, chains, expiry_source = [], [], [], {"source": self.provider.name}
        try:
            months = monthly_expiries(self.provider.expiries(UNDERLYING), day)
            if len(months) < MONTHLY_EXPIRIES and self.fallback:  # late December: Groww lists no next-year dates
                try:
                    listed, expiry_source = self.fallback.listed(UNDERLYING, day)
                    months = monthly_expiries(listed, day)
                except Exception as exc:
                    failures.append(f"expiry fallback: {type(exc).__name__}: {exc}")
            if len(months) < MONTHLY_EXPIRIES:
                failures.append(f"only {len(months)} monthly expiries found")
            for expiry in months:
                chains.append(self.provider.chain(UNDERLYING, expiry))
        except Exception as exc:  # recorded, never hidden: the attempt is incomplete
            failures.append(f"chain: {type(exc).__name__}: {exc}")
        expected = sum(len(self._contracts(c)) for c in chains)
        for chain in chains:
            for strike, kind in self._contracts(chain):
                sent = self.now()
                try:
                    book = self.provider.quote_book(chain, strike, kind)
                except Exception as exc:
                    failures.append(f"{chain.expiry} {strike:g} {kind}: {type(exc).__name__}: {exc}")
                    continue
                rows.append(self._row(snapshot_id, sent, self.now(), chain, strike, kind, book, day))
        if rows and not any(r["last_trade_time"].startswith(day.isoformat()) for r in rows):
            return RecordResult("not a trading day", snapshot_id)  # no contract traded today: market closed
        complete = bool(chains) and not failures and len(rows) == expected
        csv_bytes = self._csv(rows)
        meta = {
            "snapshot_id": snapshot_id, "underlying": UNDERLYING, "provider": self.provider.name,
            "started_at": started.isoformat(), "finished_at": self.now().isoformat(),
            "expiries": [c.expiry.isoformat() for c in chains], "spot": chains[0].spot if chains else None,
            "expiry_source": expiry_source,
            "expected_contracts": expected, "recorded_contracts": len(rows), "failures": failures,
            "complete": complete, "in_window": canonical_allowed, "csv_sha256": hashlib.sha256(csv_bytes).hexdigest(),
            "note": "quotes, not fills; Groww gives no quote timestamp: quote age unknown, valid needs a trade today",
        }  # fmt: skip
        self.store.put(self.path(day, f"{snapshot_id}.csv"), csv_bytes)
        self.store.put(self.path(day, f"{snapshot_id}.meta.json"), json.dumps(meta, indent=1, sort_keys=True).encode())
        if complete and canonical_allowed and self.canonical(day) is None:
            self.store.put(self.path(day, f"nifty_{day:%Y%m%d}.canonical"), snapshot_id.encode())
        return RecordResult("recorded", snapshot_id, complete, len(rows))

    @staticmethod
    def _contracts(chain: OptionChain) -> list[tuple[float, str]]:
        low, high = chain.spot * (1 - SPOT_BAND), chain.spot * (1 + SPOT_BAND)
        return sorted((k, t) for k, t in chain.quotes if low <= k <= high)

    def _row(self, snapshot_id, sent, received, chain, strike, kind, book: QuoteBook | None, day) -> dict:
        reason = quote_validity(book, day)
        leg = chain.get(strike, kind)
        return {
            "snapshot_id": snapshot_id, "request_sent_at": sent.isoformat(),
            "response_received_at": received.isoformat(), "quote_time": "", "age_basis": NO_QUOTE_TIME,
            "freshness_proxy": FRESHNESS_PROXY,
            "provider": self.provider.name,
            "last_trade_time": book.last_trade_time.isoformat() if book and book.last_trade_time else "",
            "contract_id": book.symbol if book else (leg.symbol if leg else ""), "expiry": chain.expiry.isoformat(),
            "strike": f"{strike:g}", "type": kind, "bid": _num(book and book.bid), "ask": _num(book and book.ask),
            "last": _num(book and book.last), "bid_qty": _num(book and book.bid_qty),
            "ask_qty": _num(book and book.ask_qty), "spot": f"{chain.spot:.2f}",
            "book_source": book.book_source if book else "", "valid": "false" if reason else "true",
            "invalid_reason": reason, "raw_sha256": book.raw_sha256 if book else "",
        }  # fmt: skip

    @staticmethod
    def _csv(rows: list[dict]) -> bytes:
        out = io.StringIO()
        writer = csv.DictWriter(out, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
        return out.getvalue().encode()


def _num(value) -> str:
    return "" if value is None or value is False else f"{float(value):g}"
