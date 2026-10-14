"""What Book 1's committed decision records fix for its trades (story E5, judge 84): each chosen book trade's terms
(structure, width, lots), for C2's view of the book, and its time exit, fixed at the decision. The exit day comes from
the run's own inputs, never today's playbook folder: the version file as the run read it (`inputs.json`), and the
trade's expiry from its opportunity ID, through D2's `OpportunityFinder.exit_day`. So no later edit to a version file,
and no unrelated file that no longer parses, can stop or move an open trade's exit."""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from ..playbook.decision_store import INPUTS_FILE, DecisionStore
from ..playbook.documents import strategy_from_text
from ..playbook.opportunities import OpportunityFinder
from ..risk.inputs import TradeTerms

BOOK_MODE, TRADE = "book", "trade"


@dataclass(frozen=True)
class DecidedTrade:
    trade_id: str
    version: str  # "<name>-v<n>"
    expiry: date
    terms: TradeTerms
    run: Path


def decided_trades(root: Path, book: str) -> Iterator[DecidedTrade]:
    """Every trade the book's committed records chose (book mode; shadow trades included when `mode` says so)."""
    for record_path in sorted(DecisionStore(root, book).folder.glob("*/*/*.json")):
        if record_path.name == INPUTS_FILE:
            continue
        record = json.loads(record_path.read_text(encoding="utf-8"))
        trade = record.get("structure")
        if record.get("chosen_action") != TRADE or not trade:
            continue
        version, _, expiry = record["opportunity_id"].rpartition(":")
        terms = TradeTerms(trade["structure"], trade["width"], trade["lots"])
        yield DecidedTrade(trade["trade_id"], version, date.fromisoformat(expiry), terms, record_path.parent)


def recorded_terms(root: Path, book: str) -> dict[str, TradeTerms]:
    """Every trade the book's committed records chose, by trade ID, with its structure, width and lots."""
    return {t.trade_id: t.terms for t in decided_trades(root, book)}


def decided_exit_days(root: Path, book: str, finder: OpportunityFinder) -> dict[str, tuple[date, str]]:
    """Each chosen trade's time exit as fixed at its decision, by trade ID: (exit day, version)."""
    exits, files = {}, {}
    for trade in decided_trades(root, book):
        if trade.run not in files:
            files[trade.run] = json.loads((trade.run / INPUTS_FILE).read_text(encoding="utf-8"))["playbook"]["files"]
        name = f"{trade.version}.yaml"
        strategy = strategy_from_text(files[trade.run][name], name)
        exits[trade.trade_id] = (finder.exit_day(strategy, trade.expiry), trade.version)
    return exits
