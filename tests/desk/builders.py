"""Fixture execution snapshots in A4's own file format, and entry orders, for the fill-model tests (story E4)."""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, time

from fno.books.files import csv_text
from fno.checks.data_checks import CheckReport
from fno.config import ROOT, load_config
from fno.constants import BOOK1_RULES, OPTION_CALL, OPTION_PUT, STRUCTURE_SHORT_IRON_FLY
from fno.desk.entries import EntryOrder
from fno.desk.wiring import open_desk_journal
from fno.models import IST
from fno.quotes.recorder import COLUMNS, QuoteSnapshotRecorder
from fno.research_data.panel_reader import FutureQuote
from fno.research_engine.structures import BOUGHT, SOLD, Leg
from fno.risk.inputs import ContractQuote, Market, Proposal, ProposedLeg, TradeTerms
from fno.risk.manager import RiskDecision
from fno.risk.trade_costs import SimulatorTradeCosts
from fno.risk.verdict import RiskVerdict
from fno.storage.raw_store import RawFileStore

DAY = date(2026, 10, 14)
EXPIRY = date(2026, 10, 27)
LOT = 65
CHARGES = load_config(ROOT / "config.yaml")["charges"]
STRATEGY = "fixture-fly-v1"
DECIDED_AT = datetime(2026, 10, 14, 15, 5, tzinfo=IST)
# The short iron fly every test trades: bid, ask for (strike, type)
FLY_QUOTES = {
    (25000, OPTION_CALL): (150.0, 151.0),
    (25000, OPTION_PUT): (140.0, 141.5),
    (25200, OPTION_CALL): (70.0, 71.0),
    (24800, OPTION_PUT): (60.0, 60.5),
}
FLY_LEGS = (
    (25000, OPTION_CALL, SOLD),
    (25000, OPTION_PUT, SOLD),
    (25200, OPTION_CALL, BOUGHT),
    (24800, OPTION_PUT, BOUGHT),
)


class DictStore(RawFileStore):
    def __init__(self):
        self.files: dict[str, bytes] = {}

    def get(self, path):
        return self.files.get(path)

    def put(self, path, data):
        self.files[path] = data


def contract(strike: float, kind: str, expiry: date = EXPIRY) -> str:
    return f"NIFTY{expiry:%y%m%d}{strike:g}{kind}"


def at(hour: int, minute: int, second: int = 0, day: date = DAY) -> datetime:
    return datetime.combine(day, time(hour, minute, second), IST)


def row(strike, kind, bid, ask, size=1000.0, valid=True, reason="", last="999", expiry=EXPIRY, bid_qty=None):
    values = {name: "" for name in COLUMNS}
    values |= {
        "contract_id": contract(strike, kind, expiry), "expiry": expiry.isoformat(), "strike": f"{strike:g}",
        "type": kind, "bid": "" if bid is None else f"{bid:g}", "ask": "" if ask is None else f"{ask:g}",
        "bid_qty": f"{size if bid_qty is None else bid_qty:g}", "ask_qty": f"{size:g}", "last": last,
        "valid": "true" if valid else "false", "invalid_reason": reason,
    }  # fmt: skip
    return values


def fly_rows(changes: dict | None = None, **kwargs) -> list[dict]:
    """The fly's four quotes; `changes` replaces a (strike, type)'s keyword arguments, or drops it when None."""
    rows = []
    for (strike, kind), (bid, ask) in FLY_QUOTES.items():
        change = (changes or {}).get((strike, kind), {})
        if change is not None:
            rows.append(row(strike, kind, **({"bid": bid, "ask": ask} | kwargs | change)))
    return rows


def drop(rows: list[dict], strike: float, kind: str) -> list[dict]:
    return [r for r in rows if (float(r["strike"]), r["type"]) != (strike, kind)]


def write_snapshot(store, snapshot_id, rows, started, finished, complete=True, day=DAY, sha=None) -> None:
    for r in rows:
        r["snapshot_id"] = snapshot_id
    csv_bytes = csv_text(COLUMNS, rows, header=True).encode()
    meta = {
        "snapshot_id": snapshot_id, "started_at": started.isoformat(), "finished_at": finished.isoformat(),
        "complete": complete, "csv_sha256": sha or hashlib.sha256(csv_bytes).hexdigest(),
    }  # fmt: skip
    store.put(QuoteSnapshotRecorder.path(day, f"{snapshot_id}.csv"), csv_bytes)
    store.put(QuoteSnapshotRecorder.path(day, f"{snapshot_id}.meta.json"), json.dumps(meta).encode())


def passed(snapshot, legs=()) -> CheckReport:
    """C3's report when every data check passed on this snapshot (and these legs)."""
    return CheckReport(snapshot.day, snapshot.snapshot_id, tuple(legs), ())


def enter(root, snapshots, desk, order, snapshot_id="exec", day=DAY, checks=None):
    """Fill one entry order against a recorded snapshot, under the book's lock; the data checks passed unless given."""
    snapshot = snapshots.snapshot(day, snapshot_id)
    with open_desk_journal(order.book, root) as journal:
        return desk.enter(order, snapshot, journal, checks or passed(snapshot, order.contracts()))


def approved(proposal: Proposal, book: str = BOOK1_RULES, day: date = DAY, entry_cash=None) -> RiskDecision:
    """An ok C2 decision on this proposal; its entry cash is C2's own computation unless a test plants one."""
    cash = approved_entry(proposal) if entry_cash is None else entry_cash
    verdicts = (RiskVerdict("inputs", True, "new"),)
    return RiskDecision(book, proposal.trade_id, day.isoformat(), verdicts, {}, (), cash, proposal)


def fly_proposal(trade_id: str = "t1", lots: int = 1, legs=FLY_LEGS) -> Proposal:
    proposed = tuple(ProposedLeg(contract(k, kind), Leg(k, kind, side)) for k, kind, side in legs)
    return Proposal(trade_id, TradeTerms(STRUCTURE_SHORT_IRON_FLY, 200, lots), LOT, proposed)


def decision_market(quotes=FLY_QUOTES, day=DAY) -> Market:
    """C2's market at the decision: the mids of these (bid, ask) quotes, one implied volatility, the future at spot."""
    mids = {(k, kind): (bid + ask) / 2 for (k, kind), (bid, ask) in quotes.items()}
    prices = {contract(k, kind): ContractQuote(k, kind, EXPIRY, mid, 0.15) for (k, kind), mid in mids.items()}
    return Market(day, 25000.0, 0.065, prices, {EXPIRY: FutureQuote(EXPIRY, 25000.0, 25000.0, 1, 1)})


def approved_entry(proposal: Proposal, quotes=FLY_QUOTES) -> float:
    """The entry C2 modelled and approved: B2's cost model (mid +- Rs 1 pad, entry charges) at the decision mids."""
    return SimulatorTradeCosts(CHARGES).entry_cash_flow(proposal, decision_market(quotes))


def fly_order(trade_id="t1", book=BOOK1_RULES, risk=None, decided_at=DECIDED_AT, lots=1, limit=None,
              strategy=STRATEGY) -> EntryOrder:  # fmt: skip
    proposal = fly_proposal(trade_id, lots)
    risk = risk or approved(proposal, book, decided_at.date(), limit)
    return EntryOrder(book, strategy, f"d-{trade_id}", decided_at, proposal, EXPIRY, risk)
