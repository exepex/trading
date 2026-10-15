"""Story S3 fixtures: execution snapshots with chosen quotes, E2 common packs, D3 records in the form
`decision_record.py` writes them, E3 run logs (S2's builder), a weekday calendar and E7 settlement prices. Charges are
brokerage only (Rs 20 an order), so every one-lot result can be checked by hand."""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from fno.constants import BOOK1_RULES, BOOK2_HYBRID, BOOK3_AI, Decision
from fno.desk.pack_store import PackStore
from fno.desk.settlement import FinalSettlement, SettlementPrices
from fno.desk.snapshot import ExecutionQuote, ExecutionSnapshot, ExecutionSnapshotSource
from fno.playbook.decision_record import NO_TRADE_ID
from fno.playbook.decision_store import DecisionStore, record_file
from fno.scoreboard.ports import ProtocolStatus
from fno.scoreboard.wiring import matched_board_from
from tests.scoreboard.builders import SERVED, versions, write_log

CHARGES = {"brokerage_per_order": 20.0, "exchange_txn_pct": 0.0, "sebi_per_crore": 0.0, "ipft_per_crore": 0.0,
           "stt_sell_pct": 0.0, "stamp_duty_buy_pct": 0.0, "gst_pct": 0.0, "stt_exercise_pct": 0.0}  # fmt: skip
LOT = 75
EXPIRY = date(2026, 11, 24)
BOOKS = (BOOK1_RULES, BOOK2_HYBRID, BOOK3_AI)
CALL = {"contract": "NIFTY-C-25000", "strike": 25000.0, "type": "CE", "side": 1}
SHORT_PUT = {"contract": "NIFTY-P-24900", "strike": 24900.0, "type": "PE", "side": -1}
LONG_PUT = {"contract": "NIFTY-P-24800", "strike": 24800.0, "type": "PE", "side": 1}
IST = timezone(timedelta(hours=5, minutes=30))


def weekdays(first: date, last: date) -> list[date]:
    return [first + timedelta(n) for n in range((last - first).days + 1) if (first + timedelta(n)).weekday() < 5]


class Calendar:
    def sessions(self, first: date, last: date) -> list[date]:
        return weekdays(first, last)


def quote(strike: float, kind: str, bid: float, ask: float, size: float = 1000.0, expiry: date = EXPIRY):
    return ExecutionQuote("", expiry, strike, kind, bid, ask, size, size, True, "", True)


class Snapshots(ExecutionSnapshotSource):
    """Each day's capture, keyed by day: the run logs name `snap-<day>`."""

    def __init__(self, by_day: dict[date, list[ExecutionQuote]]):
        self.by_day = by_day

    def snapshot(self, day: date, snapshot_id: str) -> ExecutionSnapshot:
        quotes = {(q.expiry, q.strike, q.kind): q for q in self.by_day.get(day, [])}
        at = datetime(day.year, day.month, day.day, 15, 15, tzinfo=IST)
        return ExecutionSnapshot(day, snapshot_id, "sha", "meta", at, at, True, quotes)


class Settlements(SettlementPrices):
    def __init__(self, prices: dict[date, float] | None = None):
        self.prices = prices or {}

    def final_settlement(self, underlying: str, expiry: date) -> FinalSettlement | None:
        price = self.prices.get(expiry)
        return None if price is None else FinalSettlement(underlying, expiry, price, "file", "sha")


def write_pack(root: Path, day: date, *opportunities: tuple[str, date]) -> str:
    """E2's common pack for `day`: each (opportunity ID, exit day), monthly expiry EXPIRY, then "no trade"."""
    entries = [
        {
            "opportunity_id": o,
            "strategy": "s",
            "version": 1,
            "rule_sha256": "r",
            "expiry": EXPIRY.isoformat(),
            "entry_day": day.isoformat(),
            "exit_day": exit_day.isoformat(),
        }
        for o, exit_day in opportunities
    ]
    entries.append({"opportunity_id": NO_TRADE_ID})  # fmt: skip
    path = PackStore(root).common_path(day)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"opportunities": entries}, sort_keys=True))
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record(opportunity_id: str, outcome: str = Decision.CHOSEN, reason: str = "rank 1", legs=(CALL,),
           failed: tuple[tuple[str, str], ...] = (), pack: str = "", action: str | None = None,
           capital: float | None = None) -> dict:  # fmt: skip
    """A D3 opportunity record as `decision_record.py` writes it (only the fields scoreboard A reads, plus `served`)."""
    verdicts = [{"rule": rule, "ok": False, "reason": why, "numbers": {}} for rule, why in failed]
    if capital is not None:  # C2's margin verdict: capital tied for the record's 2 lots
        numbers = {"capital_rs": {f"t-{opportunity_id}": {"capital_tied": capital, "stress_reserve": 0.0}}}
        verdicts.append({"rule": "margin_room", "ok": True, "reason": "room", "numbers": numbers})
    acted = action or ("trade" if outcome == Decision.CHOSEN else "no trade")
    return {"opportunity_id": opportunity_id, "common_pack_sha256": pack, "served": dict(SERVED),
            "structure": {"structure": "LC", "lots": 2, "legs": [dict(leg) for leg in legs]} if legs else None,
            "risk": {"trade_id": f"t-{opportunity_id}", "verdicts": verdicts} if verdicts else None,
            "decision": {"action": acted, "outcome": str(outcome), "reason": reason}}  # fmt: skip


def write_run(root: Path, book: str, day: date, *records: dict, pack: str) -> str:
    run_id = f"{day.isoformat()}-{book}"
    folder = DecisionStore(root, book).day_folder(day) / run_id
    folder.mkdir(parents=True, exist_ok=True)
    day_record = record(NO_TRADE_ID, Decision.NO_TRADE, "day", legs=(), pack=pack)
    for body in (*records, day_record):
        body = {**body, "run_id": run_id, "book": book}
        (folder / record_file(body["opportunity_id"])).write_text(json.dumps(body, sort_keys=True))
    (folder / "inputs.json").write_text("{}")
    return run_id


def write_day(root: Path, day: date, runs: dict[str, str | None], snapshot: bool = True) -> None:
    write_log(root, day, runs)
    if not snapshot:
        path = root / "journal" / "runs" / f"{day.isoformat()}.json"
        log = json.loads(path.read_text())
        log["steps"]["snapshot"]["result"]["valid"] = False
        path.write_text(json.dumps(log))


def board(root: Path, quotes: dict[date, list[ExecutionQuote]], settlements: Settlements | None = None, start=None,
          against=None):  # fmt: skip
    """Scoreboard A over the fixture records; the books' versions are registered from `start`."""
    start = start or date(2026, 10, 1)
    registry = versions(*((book, f"{book}-v1", start) for book in BOOKS))
    return matched_board_from(root, {"charges": CHARGES, "lot_sizes": {"NIFTY": LOT}}, Calendar(), registry,
                              Snapshots(quotes), settlements or Settlements(), ProtocolStatus(None, False),
                              against)  # fmt: skip
