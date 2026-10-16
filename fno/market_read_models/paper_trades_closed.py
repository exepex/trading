"""The paper books page's closed trades (story P2c part 2; contract `FnoPaperTrades.closed`), each from its own book's
records only: E1's fills and C1's trade line for the money, E4's desk records for the version, the opening decision
and the exit, and D3's committed decision record for the structure. Mapped as agreed with the screens lead (16 Oct):

- **Strategy:** "Strategy <k>, version <n>", k being the order in which the strategy's name first appears in the
  append-only `playbook/registry.csv`: a version tag can name a filter (strategy internals stay private).
- **Structure:** the code's shape in plain words (never a strike rule).
- **Exit:** the desk's own rule name (profit_target, stop_loss, time_exit), a settlement fill for expiry settlement,
  anything else `other`; `safety_stop` is never sent until S1's stop exists.
- **Fills:** null for every trade until E8 records all three reaction times.
A trade whose strategy or structure cannot be named holds the page (story P11), never a guessed label."""

from __future__ import annotations

import csv
import io
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

from ..accounting.ledgers import trade_line
from ..books.equity import TradePosition
from ..constants import FILL_SETTLE, OUTCOME_EXIT_ORDERED
from ..desk.records import DeskRecords
from ..desk.trade_counts import version_key
from ..playbook.fields import PlaybookError

STRUCTURE_WORDS = {  # the code's own definition: fno/research_engine/structures.py and fno/constants.py
    "SF": "sold iron butterfly", "SC": "sold iron condor", "BF": "bought iron butterfly", "LC": "bought call",
    "LP": "bought put", "CDS": "call debit spread (bull call spread)", "CCS": "call credit spread (bear call spread)",
    "PDS": "put debit spread (bear put spread)", "PCS": "put credit spread (bull put spread)",
}  # fmt: skip
EXITS = {"profit_target": "take_profit", "stop_loss": "max_loss_exit", "time_exit": "time_exit"}
EXPIRY_SETTLEMENT, OTHER_EXIT = "expiry_settlement", "other"
STRATEGY_LABEL = "Strategy {k}, version {n}"
# Story P11 hold reasons of this page: fixed sentences shown on screen (contract 2.13.0: no value, no digit, no book id)
NOT_IN_REGISTRY = (
    "A trade or shadow account belongs to a strategy with no row in the playbook registry, so it is never given a label"
)
NO_STRUCTURE = "A trade has no committed decision record naming a known structure, so it is never given one"


class PageCannotBeBuilt(Exception):
    """The paper books page cannot be built today, for `reason` (one of the page's hold reasons): only this page is
    held (story P11), every other page publishes."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


Structures = Callable[[str, date, str], str]  # (book, day, decision id) -> the structure code its record names


@dataclass(frozen=True)
class ClosedTrade:
    trade_id: str
    book: str
    strategy: str
    structure: str
    opened_on: date
    closed_on: date
    gross: float
    costs: float
    net: float
    exit: str


def strategy_order(registry_csv: str) -> dict[str, int]:
    """Each strategy's k: the order its name first appears in the append-only registry (1 is the first)."""
    order: dict[str, int] = {}
    for row in csv.DictReader(io.StringIO(registry_csv)):
        order.setdefault(row["name"], len(order) + 1)
    return order


class ClosedTrades:
    def __init__(self, registry: Callable[[], str], structures: Structures, charges: dict):
        """`registry`: the registry's text, read when the page is built (no file yet: no strategy has a label)."""
        self.registry, self.structures, self.charges = registry, structures, dict(charges)
        self._order: dict[str, int] | None = None

    @property
    def order(self) -> dict[str, int]:
        if self._order is None:
            self._order = strategy_order(self.registry())
        return self._order

    def of(self, records: DeskRecords, trade: TradePosition) -> ClosedTrade:
        book, rows = records.account.book, records.fill_rows(trade.trade_id)
        first = rows[0]
        opened_on = min(f.filled_at.date() for f in trade.fills)
        line = trade_line(trade.as_ledger_trade(), self.charges)
        costs = line.pads + sum(line.charges.values())
        return ClosedTrade(
            trade.trade_id, book, self._strategy(book, trade.trade_id, first["strategy"]),
            self._structure(book, trade.trade_id, opened_on, first["decision_id"]), opened_on, trade.closed_on,
            round(line.gross, 2), round(costs, 2), round(line.net, 2), _exit(records, trade.trade_id, rows),
        )  # fmt: skip

    def _strategy(self, book: str, trade_id: str, tag: str) -> str:
        name, version = version_key(tag)
        if name not in self.order:
            raise PageCannotBeBuilt(NOT_IN_REGISTRY)
        return STRATEGY_LABEL.format(k=self.order[name], n=version)

    def _structure(self, book: str, trade_id: str, day: date, decision_id: str) -> str:
        words = STRUCTURE_WORDS.get(self.structures(book, day, decision_id))
        if words is None:
            raise PageCannotBeBuilt(NO_STRUCTURE)
        return words


def _exit(records: DeskRecords, trade_id: str, fills: list[dict]) -> str:
    if any(r["action"] == FILL_SETTLE for r in fills):
        return EXPIRY_SETTLEMENT
    ordered = [e["reason"] for e in records.event_rows(trade_id) if e["outcome"] == OUTCOME_EXIT_ORDERED]
    rule = ordered[-1].partition(":")[0] if ordered else ""
    return EXITS.get(rule, OTHER_EXIT)


def result(net: float) -> str:
    return "won" if net > 0 else "lost" if net < 0 else "flat"


class CommittedStructures:
    """The structure code each committed D3 decision record names, by (book, day, opportunity id): the record the desk
    opened the trade from (`fno.scoreboard.committed_runs.CommittedRuns`, the books' own records, never a shadow's)."""

    def __init__(self, runs):
        self.runs, self._codes = runs, None

    def __call__(self, book: str, day: date, decision_id: str) -> str:
        if self._codes is None:
            self._codes = {(run.book, run.day, r["opportunity_id"]): (r.get("structure") or {}).get("structure", "")
                           for run in self.runs.runs() for r in self.runs.records(run)}  # fmt: skip
        return self._codes.get((book, day, decision_id), "")


class PlaybookVersions:
    """Each version's playbook file by (name, version), read once (D1's loader); None when the playbook or the file
    cannot be read, so the page holds rather than guess a shadow's label."""

    def __init__(self, load):
        self.load, self._playbook = load, None

    def __call__(self, name: str, version: int):
        try:
            if self._playbook is None:
                self._playbook = self.load()
            return self._playbook.get(name, version)
        except PlaybookError:
            return None
