"""The one Groww bid/ask snapshot (PROTOCOL.md section 6.2, amendment 1 section D8). Read-only quotes; no order code.

`capture` returns the raw record (every payload, for Drive only) and the derived legs (for the study's buckets). The
repository gets neither: only the counts and bucket statistics the study reports.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import date, datetime, time
from typing import Protocol

from fno.providers.groww import parse_groww_quote_book

from .bhav import Chain, DaySummary
from .events import RESULTS_PURPOSE
from .rules import SNAPSHOT_LOOKAHEAD_SESSIONS, SNAPSHOT_STEPS
from .sessions import Sessions, choose_expiry
from .spreads import QuotedLeg
from .structures import CALL, PUT, atm_strikes

WINDOW = (time(14, 0), time(15, 0))  # IST
EVENT_DATE_FORMAT = "%d-%b-%Y"


class OutsideWindow(RuntimeError):
    """The snapshot is taken only between 14:00 and 15:00 IST on a session."""


class QuoteSource(Protocol):
    """What the capture needs from Groww: listed expiries, the chain (strikes, symbols, last price), one quote."""

    def expiries(self, symbol: str) -> list[date]: ...
    def chain_symbols(self, symbol: str, expiry: date) -> tuple[float, dict[tuple[float, str], str]]: ...
    def quote(self, trading_symbol: str) -> dict: ...


@dataclass(frozen=True)
class Candidate:
    symbol: str
    results_day: date


def candidates(calendar_rows: list[dict], today: date, sessions: Sessions, previous: DaySummary) -> list[Candidate]:
    """F&O stocks (on the previous session's file) with a results meeting in the next 10 sessions."""
    ahead = sessions.ahead(today, SNAPSHOT_LOOKAHEAD_SESSIONS)
    if not ahead:
        return []
    found = {}
    for row in calendar_rows:
        text = f"{row.get('purpose') or ''} | {row.get('bm_desc') or ''}".lower()
        symbol = (row.get("symbol") or "").strip()
        if RESULTS_PURPOSE not in text or not symbol or not previous.is_fo_stock(symbol):
            continue
        day = datetime.strptime(row["date"].strip(), EVENT_DATE_FORMAT).date()
        if today < day <= ahead[-1]:
            found.setdefault(symbol, Candidate(symbol, day))
    return sorted(found.values(), key=lambda c: (c.results_day, c.symbol))


def snapshot_strikes(chain_strikes: list[float], spot: float) -> list[tuple[int, float]]:
    """(steps from K0, strike) for K0 - 3 steps to K0 + 3 steps that are listed."""
    strikes = atm_strikes({(k, CALL): None for k in chain_strikes}, spot)
    if strikes is None:
        return []
    listed = set(chain_strikes)
    out = []
    for steps in range(-SNAPSHOT_STEPS, SNAPSHOT_STEPS + 1):
        strike = strikes.strike(steps)
        if strike is not None and strike in listed:
            out.append((steps, strike))
    return out


COUNTS = ("stocks_skipped", "not_listed", "after_window", "errors", "no_previous_row")


def capture(
    source: QuoteSource,
    found: list[Candidate],
    sessions: Sessions,
    previous: DaySummary,
    previous_chains: dict[str, dict[date, Chain]],
    clock,
) -> tuple[dict, list[QuotedLeg]]:
    """Quotes every candidate's legs and counts every leg or stock not quoted, by reason. A quote that comes back at
    or after 15:00 IST is dropped (counted), and nothing is requested after it."""
    raw = {"started": clock().isoformat(), "stocks": [], **dict.fromkeys(COUNTS, 0)}
    legs: list[QuotedLeg] = []
    for candidate in found:
        raw["stocks"].append(_stock(source, candidate, sessions, previous, previous_chains, clock, legs, raw))
    raw["finished"] = clock().isoformat()
    return raw, legs


def contract_lot(previous: DaySummary, chain: Chain, symbol: str, expiry: date) -> int | None:
    """The chosen expiry's own lot on the previous session: its future's lot column, else any of its option rows'."""
    future = previous.future(symbol, expiry)
    if future is not None and future.lot:
        return future.lot
    return next((leg.lot for leg in chain.values() if leg.lot), None)


def _stock(source, candidate, sessions, previous, previous_chains, clock, legs, counts) -> dict:
    record = {"symbol": candidate.symbol, "results_day": candidate.results_day.isoformat()}
    try:
        reaction = sessions.after(candidate.results_day)
        expiry, pushed = choose_expiry(sessions, source.expiries(candidate.symbol), reaction)
        old_chain = previous_chains.get(candidate.symbol, {}).get(expiry, {}) if expiry else {}
        lot = contract_lot(previous, old_chain, candidate.symbol, expiry) if expiry else None
        spot, symbols = source.chain_symbols(candidate.symbol, expiry) if lot else (0.0, {})
    except Exception as exc:  # noqa: BLE001 - one stock's failure is counted, never the end of the capture
        counts["stocks_skipped"] += 1
        return {**record, "skipped": f"error {type(exc).__name__}"}
    strikes = snapshot_strikes(sorted({k for k, _ in symbols}), spot)
    if not strikes:
        counts["stocks_skipped"] += 1
        return {**record, "skipped": "no expiry, no lot or no listed strikes"}
    record.update(expiry=expiry.isoformat(), pushed=pushed, spot=spot, lot=lot, quotes=[])
    for steps, strike in strikes:
        for kind in (CALL, PUT):
            reason = _quote_leg(source, symbols.get((strike, kind)), steps, strike, kind, clock, record)
            if reason:
                counts[reason] += 1
                continue
            book = parse_groww_quote_book(record["quotes"][-1]["trading_symbol"], record["quotes"][-1]["payload"])
            old = old_chain.get((strike, kind))
            counts["no_previous_row"] += old is None
            legs.append(QuotedLeg(abs(steps), old.contracts if old else 0.0, book.bid, book.ask, book.bid_qty,
                                  book.ask_qty, lot))  # fmt: skip
    return record


def _quote_leg(source, trading_symbol, steps, strike, kind, clock, record) -> str:
    """'' when quoted (appended to the record), else the reason it was not."""
    if trading_symbol is None:
        return "not_listed"
    if clock().time() >= WINDOW[1]:
        return "after_window"
    try:
        payload = source.quote(trading_symbol)
    except Exception:  # noqa: BLE001 - a failed quote is counted as an error leg, never a one-sided quote
        return "errors"
    at = clock()
    if at.time() >= WINDOW[1]:
        return "after_window"
    record["quotes"].append({"steps": steps, "strike": strike, "kind": kind, "at": at.isoformat(),
                             "trading_symbol": trading_symbol, "payload": payload})  # fmt: skip
    return ""


def check_window(moment: datetime, sessions: Sessions) -> None:
    if moment.date() not in sessions or not WINDOW[0] <= moment.time() < WINDOW[1]:
        raise OutsideWindow(f"{moment:%Y-%m-%d %H:%M} IST is outside 14:00-15:00 on a session")


def legs_file(legs: list[QuotedLeg]) -> bytes:
    return "".join(json.dumps(asdict(leg)) + "\n" for leg in legs).encode()


def raw_file(raw: dict) -> tuple[bytes, str]:
    data = json.dumps(raw, sort_keys=True, default=str).encode()
    return data, hashlib.sha256(data).hexdigest()
