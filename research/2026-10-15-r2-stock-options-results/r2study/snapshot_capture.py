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


def capture(
    source: QuoteSource,
    found: list[Candidate],
    sessions: Sessions,
    previous: DaySummary,
    previous_chains: dict[str, dict[date, Chain]],
    clock,
) -> tuple[dict, list[QuotedLeg]]:
    """Quotes every candidate's legs; stops at 15:00 IST (legs left are counted as not quoted)."""
    raw = {"started": clock().isoformat(), "stocks": [], "not_quoted": 0}
    legs: list[QuotedLeg] = []
    for candidate in found:
        record = _stock(source, candidate, sessions, previous, previous_chains, clock, legs)
        raw["stocks"].append(record)
        raw["not_quoted"] += record.get("not_quoted", 0)
    raw["finished"] = clock().isoformat()
    return raw, legs


def _stock(source, candidate, sessions, previous, previous_chains, clock, legs) -> dict:
    record = {"symbol": candidate.symbol, "results_day": candidate.results_day.isoformat()}
    reaction = sessions.after(candidate.results_day)
    future = previous.near_future(candidate.symbol)
    expiry, pushed = choose_expiry(sessions, source.expiries(candidate.symbol), reaction) if reaction else (None, False)
    if expiry is None or future is None or not future.lot:
        return {**record, "skipped": "no expiry or no lot"}
    spot, symbols = source.chain_symbols(candidate.symbol, expiry)
    strikes = snapshot_strikes(sorted({k for k, _ in symbols}), spot)
    record.update(expiry=expiry.isoformat(), pushed=pushed, spot=spot, lot=future.lot, quotes=[], not_quoted=0)
    old_chain = previous_chains.get(candidate.symbol, {}).get(expiry, {})
    for steps, strike in strikes:
        for kind in (CALL, PUT):
            trading_symbol = symbols.get((strike, kind))
            if trading_symbol is None or clock().time() >= WINDOW[1]:
                record["not_quoted"] += 1
                continue
            payload = source.quote(trading_symbol)
            book = parse_groww_quote_book(trading_symbol, payload)
            record["quotes"].append({"steps": steps, "strike": strike, "kind": kind, "at": clock().isoformat(),
                                     "trading_symbol": trading_symbol, "payload": payload})  # fmt: skip
            old = old_chain.get((strike, kind))
            legs.append(QuotedLeg(abs(steps), old.contracts if old else 0.0, book.bid, book.ask, book.bid_qty,
                                  book.ask_qty, future.lot))  # fmt: skip
    return record


def check_window(moment: datetime, sessions: Sessions) -> None:
    if moment.date() not in sessions or not WINDOW[0] <= moment.time() < WINDOW[1]:
        raise OutsideWindow(f"{moment:%Y-%m-%d %H:%M} IST is outside 14:00-15:00 on a session")


def legs_file(legs: list[QuotedLeg]) -> bytes:
    return "".join(json.dumps(asdict(leg)) + "\n" for leg in legs).encode()


def raw_file(raw: dict) -> tuple[bytes, str]:
    data = json.dumps(raw, sort_keys=True, default=str).encode()
    return data, hashlib.sha256(data).hexdigest()
