"""Book 2's entry orders at the fill (story F5 part 3 step 7, E3's `OrderBuilder` seam). Book 1's `ReplayedOrders`
does the work: D3's replay of the committed run (refused under other code; any difference refuses every order), then
only the records whose committed `chosen_action` is "trade", so a C4 block or a shadow-only choice is never ordered.
The replay's evaluator is rebuilt from the picks stored in the run's `inputs.json` (a changed width is the rebuilt
candidate, never the default's), and its C4 validator from each pick's stored rule default and the recorded counts."""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from datetime import datetime
from pathlib import Path

from ..books.book1_orders import ReplayedOrders
from ..checks.validity_adapter import BookTradeValidator
from ..desk.daily_ports import OrderBuilder
from ..desk.entries import EntryOrder
from ..playbook.code_tree import CodeTree
from ..playbook.decision_inputs import DayInputs
from ..playbook.decision_store import INPUTS_FILE
from .evaluation import Book2Evaluators
from .slots import terms_from_json
from .validator import Book2TradeValidator


class Book2Orders(OrderBuilder):
    def __init__(self, evaluators: Book2Evaluators, code: CodeTree, validator: Callable[[], BookTradeValidator]):
        """`validator()`: C4's adapter for Book 2 that writes nothing (a replay never logs, judge 84)."""
        self.evaluators, self.code, self.validator = evaluators, code, validator

    def orders(self, book: str, run: Path, decided_at: datetime) -> Sequence[EntryOrder]:
        inputs = DayInputs.from_json(json.loads((run / INPUTS_FILE).read_bytes()))
        arguments = inputs.replay_arguments()
        market, counts = arguments[2], arguments[5]
        paired = {p["opportunity_id"]: terms_from_json(p["default"]) for p in inputs.selection}
        validator = Book2TradeValidator(self.validator(), paired, counts)
        replayed = ReplayedOrders(self.evaluators.from_stored(inputs.selection, market), self.code, validator)
        return replayed.orders(book, run, decided_at)
