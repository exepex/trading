"""Book 3's entry orders at the fill (story F6 design item 8, E3's `OrderBuilder` seam). Book 1's `ReplayedOrders` does
the work: D3's replay of the committed run (refused under other code; any difference refuses every order), then only
the records whose committed `chosen_action` is "trade", so a C4 block is never ordered. Book 3's run was decided with
its picks, so the replay's evaluator is rebuilt from the picks stored in that run's `inputs.json`, never from today's
answer or files; the specs come from the run's own playbook snapshot."""

from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

from ..books.book1_orders import ReplayedOrders
from ..desk.daily_ports import OrderBuilder
from ..desk.entries import EntryOrder
from ..playbook.code_tree import CodeTree
from ..playbook.decision_inputs import DayInputs
from ..playbook.decision_store import INPUTS_FILE
from ..playbook.decision_validity import TradeValidator
from .evaluation import Book3Evaluators


class Book3Orders(OrderBuilder):
    def __init__(self, evaluators: Book3Evaluators, code: CodeTree, validator: TradeValidator | None = None):
        self.evaluators, self.code, self.validator = evaluators, code, validator

    def orders(self, book: str, run: Path, decided_at: datetime) -> Sequence[EntryOrder]:
        stored = DayInputs.from_json(json.loads((run / INPUTS_FILE).read_bytes())).selection
        replayed = ReplayedOrders(self.evaluators.from_stored(stored), self.code, self.validator)
        return replayed.orders(book, run, decided_at)
