"""Records real bid/ask quotes of NIFTY monthly options near the money at about 3 pm IST (story A4).

Only time builds this history: daily NSE files have no bid or ask. Each run is an immutable *attempt* saved under its
capture time; an incomplete attempt may be retried inside the window, and the day's canonical snapshot is the first
complete attempt (or "none"). Quotes are not fills. Never places, modifies or cancels orders.

Whether today is a session comes from NSE's session calendar (story A7), never from the weekday or from the quotes: a
special weekend session is recorded, a weekday holiday is not, and a session day with no same-day trade is a failure
to report (calendar says session, quotes say closed), not a quiet "not a trading day".
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import time as clock
from dataclasses import dataclass
from datetime import date, datetime, time

from ..constants import SESSION_MUHURAT, SESSION_REGULAR, SESSION_SPECIAL
from ..models import IST, OptionChain, QuoteBook, now_ist
from ..providers.base import Provider
from ..research_data.calendar import SessionCalendar
from ..research_data.expiries import MONTHLY_LISTING_DAYS
from ..research_data.expiries import monthly_expiries as last_expiry_of_each_month
from ..storage.raw_store import RawFileStore
from .expiry_listing import ExpiryHistory, ListedExpiries
from .market_levels import LevelSource
from .monthly_contracts import PointInTimeMonthlies

UNDERLYING = "NIFTY"
DATASET = "groww/derivatives/quote-snapshots"
NSE_DATASET = "nse/derivatives/quote-snapshots"  # story O6: NSE's public chain, never mixed with Groww's
WINDOW_START, WINDOW_END = time(14, 55), time(15, 10)
MAX_EARLY_WAIT_SECONDS = 20 * 60  # a run started up to 20 minutes early waits for the window
RETRY_GAP_SECONDS = 60
SPOT_BAND = 0.05  # strikes within 5% of spot
MONTHLY_EXPIRIES = 2
WEEKEND_START = 5  # only when built without a calendar (the A4 tests): weekends closed, no same-day trade = holiday
RECORDED_SESSION_KINDS = (SESSION_REGULAR, SESSION_SPECIAL)  # a muhurat session is one evening hour, not 14:55-15:10
MUHURAT_ONLY = "muhurat session only: the market is closed from 14:55 to 15:10"
NO_SAME_DAY_TRADES = "calendar says session, no same-day trades"
VERIFIED, UNVERIFIED = "verified", "unverified"  # status of meta.json's monthly_check
POINT_IN_TIME_RULE = f"listed more than {MONTHLY_LISTING_DAYS} days ahead by that day (A5 monthly_as_of)"
FALLBACK_RULE = "last listed expiry of month"
NONE_MARKER = "none"
RAW_FILE_NOT_SAVED = "raw quote file not saved"
MESSAGE_WITHHELD = "provider message withheld"
RAW_FILE_SAVED = "raw_file_saved"  # sidecar key, written (false) only when the save failed: absent means saved (A4b)
COLUMNS = (
    "snapshot_id", "request_sent_at", "response_received_at", "quote_time", "age_basis", "freshness_proxy",
    "last_trade_time",
    "provider", "contract_id", "expiry", "strike", "type", "bid", "ask", "last", "bid_qty", "ask_qty", "spot",
    "book_source", "valid", "invalid_reason", "raw_sha256",
)  # fmt: skip


def monthly_expiries(expiries: list[date], today: date, count: int = MONTHLY_EXPIRIES) -> list[date]:
    """The nearest `count` monthly contracts: the last listed expiry of each calendar month, from today on. Used only
    by a recorder built without NSE's expiry history (the A4 tests); the app uses `PointInTimeMonthlies` (A5's rule)."""
    return sorted(last_expiry_of_each_month({e for e in expiries if e >= today}))[:count]


NO_QUOTE_TIME = "unknown: provider gives no quote timestamp"
PAGE_TIME = "provider's snapshot timestamp (NSE page time, one for the whole chain)"
FRESHNESS_PROXY = "same-day trade (market active; quote age unknown)"
VOLUME_PROXY = "day volume above zero (NSE gives no last trade time)"
GROWW_NOTE = "quotes, not fills; Groww gives no quote timestamp: quote age unknown, valid needs a trade today"
NSE_NOTE = "quotes, not fills; NSE public option chain: quote_time is its page timestamp, traded today = day volume > 0"
PROVIDER_NOTES = {"nse": NSE_NOTE}


def traded_today(book: QuoteBook | None, today: date) -> bool:
    """A trade in the contract today: its last trade time (Groww) or, when the provider gives none, its day volume
    (NSE). Either proves the market was active in it today; neither proves the quote is seconds old."""
    if book is None:
        return False
    if book.last_trade_time is not None:
        return book.last_trade_time.date() == today
    return bool(book.traded_today)


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
    if not traded_today(book, today):
        return "no trade today (quote age unknown, possibly stale)"
    if book.quote_time is not None and book.quote_time.date() != today:
        return "quote not from today"
    return ""


@dataclass
class RecordResult:
    status: str  # recorded, already recorded, not a trading day, window closed, too early
    snapshot_id: str = ""
    complete: bool = False
    rows: int = 0
    reason: str = ""  # why a session day was skipped or failed the calendar cross-check
    monthly_unverified: str = ""  # why the monthly contracts were chosen by the fallback rule (alerted, never hidden)
    raw_file_error: str = ""  # why the quote file was not saved (A4b: Drive only; alerted, never saved elsewhere)
    raw_file_detail: str = ""  # the error's own text: for the private alert only, never in a committed file


class QuoteSnapshotRecorder:
    def __init__(self, provider: Provider, store: RawFileStore, clock_now=now_ist, sleep=clock.sleep,
                 fallback: ListedExpiries | None = None, calendar: SessionCalendar | None = None,
                 history: ExpiryHistory | None = None, levels: LevelSource | None = None,
                 dataset: str = DATASET):  # fmt: skip
        """The app always passes `calendar` and `history` (fno/composition.py). Without them (the A4 tests and
        byte-identical baseline), A4's rules stay: weekends are closed, a day with no same-day trade is a holiday, and
        the monthly is the last listed expiry of each month."""
        self.provider, self.store, self.now, self.sleep = provider, store, clock_now, sleep
        self.fallback, self.calendar, self.levels, self.dataset = fallback, calendar, levels, dataset
        self.monthly_check = PointInTimeMonthlies(history) if history else None

    @staticmethod
    def path(day: date, name: str, dataset: str = DATASET) -> str:
        return f"{dataset}/{day:%Y}/{day:%m}/{name}"

    def _path(self, day: date, name: str) -> str:
        return self.path(day, name, self.dataset)

    def canonical(self, day: date) -> str | None:
        data = self.store.get(self._path(day, f"nifty_{day:%Y%m%d}.canonical"))
        return data.decode().strip() if data else None

    def record(self, outside_window: bool = False) -> RecordResult:
        """One day's recording: waits for the window if early, retries incomplete attempts until the window ends.
        `outside_window` (testing only) makes one attempt now; such an attempt is never canonical.
        Raises `CalendarError` for a day outside the calendar's years (never guesses)."""
        now = self.now()
        day = now.date()
        kind = self._session_kind(day)
        if kind not in RECORDED_SESSION_KINDS:
            return RecordResult("not a trading day", reason=MUHURAT_ONLY if kind == SESSION_MUHURAT else "")
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
            self.store.put(self._path(day, f"nifty_{day:%Y%m%d}.canonical"), NONE_MARKER.encode())
        return result

    def capture(self) -> RecordResult:
        """One more capture now, never canonical, by A4's own rules (story E3's execution snapshot at about 15:15).
        Records nothing on a day that is not a recorded session."""
        day = self.now().date()
        if self._session_kind(day) not in RECORDED_SESSION_KINDS:
            return RecordResult("not a trading day")
        return self._attempt(day, canonical_allowed=False)

    def _session_kind(self, day: date) -> str | None:
        """The calendar's answer; without a calendar (A4 tests), every weekday is a regular session."""
        if self.calendar is None:
            return SESSION_REGULAR if day.weekday() < WEEKEND_START else None
        return self.calendar.session_kind(day)

    def _nearest_monthlies(self, listed: list[date], day: date, check: dict) -> list[date]:
        """The nearest monthly contracts by A5's point-in-time rule, with the NSE files that proved them in `check`.
        If that history cannot be read, the last-of-month rule is used and `check` says so: a lost day of quotes can
        never be recorded later, while a flagged contract choice can be verified later. Without a history (the A4
        tests), the last-of-month rule is A4's own and nothing is flagged."""
        if self.monthly_check is None:
            return monthly_expiries(listed, day)
        try:
            monthly, used = self.monthly_check.monthlies(UNDERLYING, listed, day)
        except Exception as exc:
            check.update(status=UNVERIFIED, rule=FALLBACK_RULE, reason=withheld("expiry history", exc))
            return monthly_expiries(listed, day)
        if check.get("status") != UNVERIFIED:
            check.update(status=VERIFIED, rule=POINT_IN_TIME_RULE)
            files = check.setdefault("files", [])
            files += [source for source in used if source not in files]
        return sorted(monthly)[:MONTHLY_EXPIRIES]

    def _attempt(self, day: date, canonical_allowed: bool) -> RecordResult:
        started = self.now()
        snapshot_id = f"nifty_{started:%Y%m%d_%H%M%S}"
        failures, rows, chains, expiry_source, check = [], [], [], {"source": self.provider.name}, {}
        try:
            months = self._nearest_monthlies(self.provider.expiries(UNDERLYING), day, check)
            if len(months) < MONTHLY_EXPIRIES and self.fallback:  # late December: Groww lists no next-year dates
                try:
                    listed, expiry_source = self.fallback.listed(UNDERLYING, day)
                    months = self._nearest_monthlies(listed, day, check)
                except Exception as exc:
                    failures.append(withheld("expiry fallback", exc))
            if len(months) < MONTHLY_EXPIRIES:
                failures.append(f"only {len(months)} monthly expiries found")
            for expiry in months:
                chains.append(self.provider.chain(UNDERLYING, expiry))
        except Exception as exc:  # recorded, never hidden: the attempt is incomplete
            failures.append(withheld("chain", exc))
        levels = self.levels.levels(UNDERLYING) if self.levels else None  # inside the capture: before finished_at
        expected, traded = sum(len(self._contracts(c)) for c in chains), False
        for chain in chains:
            for strike, kind in self._contracts(chain):
                sent = self.now()
                try:
                    book = self.provider.quote_book(chain, strike, kind)
                except Exception as exc:
                    failures.append(withheld(f"{chain.expiry} {strike:g} {kind}", exc))
                    continue
                rows.append(self._row(snapshot_id, sent, self.now(), chain, strike, kind, book, day))
                traded = traded or traded_today(book, day)
        if rows and not traded:
            if self.calendar is None:
                return RecordResult("not a trading day", snapshot_id)  # A4 inference: no contract traded, closed
            failures.append(NO_SAME_DAY_TRADES)  # kept and retried; the day ends "none" if it persists to 15:10
        csv_bytes = self._csv(rows)
        raw_file_error, raw_file_detail = self._save_quote_file(self._path(day, f"{snapshot_id}.csv"), csv_bytes)
        if raw_file_error:
            failures.append(raw_file_error)
        complete = bool(chains) and not failures and len(rows) == expected
        meta = {
            "snapshot_id": snapshot_id, "underlying": UNDERLYING, "provider": self.provider.name,
            "started_at": started.isoformat(), "finished_at": self.now().isoformat(),
            "expiries": [c.expiry.isoformat() for c in chains], "spot": chains[0].spot if chains else None,
            "expiry_source": expiry_source,
            "expected_contracts": expected, "recorded_contracts": len(rows), "failures": failures,
            "complete": complete, "in_window": canonical_allowed, "csv_sha256": hashlib.sha256(csv_bytes).hexdigest(),
            "note": PROVIDER_NOTES.get(self.provider.name, GROWW_NOTE),
        }  # fmt: skip
        if raw_file_error:
            meta[RAW_FILE_SAVED] = False
        if self.monthly_check is not None:
            meta["monthly_check"] = check  # verified with the NSE files that proved it, or unverified and why
        if levels is not None:
            meta.update(levels.meta(), levels_source=self.levels.name)  # India VIX and futures for live features
        self.store.put(self._path(day, f"{snapshot_id}.meta.json"), json.dumps(meta, indent=1, sort_keys=True).encode())
        if complete and canonical_allowed and self.canonical(day) is None:
            self.store.put(self._path(day, f"nifty_{day:%Y%m%d}.canonical"), snapshot_id.encode())
        reason = NO_SAME_DAY_TRADES if NO_SAME_DAY_TRADES in failures else ""
        unverified = check["reason"] if check.get("status") == UNVERIFIED else ""
        return RecordResult("recorded", snapshot_id, complete, len(rows), reason, unverified, raw_file_error,
                            raw_file_detail)  # fmt: skip

    def _save_quote_file(self, path: str, data: bytes) -> tuple[str, str]:
        """("", "") when saved; otherwise (the reason for the public sidecar, the error's own text). The quote rows are
        then kept nowhere (A4b: never in the repository instead), and the attempt is incomplete, so it is never
        canonical and the window retries. The sidecar gets the error's type only: a Drive error's text can hold the
        request URL with the private folder's ID."""
        try:
            self.store.put(path, data)
        except Exception as exc:
            return f"{RAW_FILE_NOT_SAVED}: {type(exc).__name__}", str(exc)
        return "", ""

    @staticmethod
    def _contracts(chain: OptionChain) -> list[tuple[float, str]]:
        low, high = chain.spot * (1 - SPOT_BAND), chain.spot * (1 + SPOT_BAND)
        return sorted((k, t) for k, t in chain.quotes if low <= k <= high)

    def _row(self, snapshot_id, sent, received, chain, strike, kind, book: QuoteBook | None, day) -> dict:
        reason = quote_validity(book, day)
        leg = chain.get(strike, kind)
        return {
            "snapshot_id": snapshot_id, "request_sent_at": sent.isoformat(),
            "response_received_at": received.isoformat(),
            "quote_time": book.quote_time.isoformat() if book and book.quote_time else "",
            "age_basis": PAGE_TIME if book and book.quote_time else NO_QUOTE_TIME,
            "freshness_proxy": _freshness_proxy(book),
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


def withheld(where: str, exc: Exception) -> str:
    """A public sidecar's failure entry (A4b): the exception's type only. Its message can carry a request URL, a private
    Drive folder ID or a quoted value, and the sidecar is committed to the public repository."""
    return f"{where}: {type(exc).__name__} ({MESSAGE_WITHHELD})"


def _freshness_proxy(book: QuoteBook | None) -> str:
    return VOLUME_PROXY if book and book.last_trade_time is None and book.traded_today else FRESHNESS_PROXY


def _num(value) -> str:
    return "" if value is None or value is False else f"{float(value):g}"
