"""Book 3's day sheet in the pack step (story F6 criterion 13, E2e's `BookSheet`): D2 over Book 3's tradable
strategies on the pack's own cutoff inputs, nothing chosen, with each common opportunity's widths. It goes into Book
3's private pack under "evaluation"; the decider gives it again from the same inputs and refuses the day when it
differs."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import date

from ..books.book1 import Book1Day
from ..desk.book_sheet import BookSheet
from ..desk.common_pack import CommonPack
from ..desk.opportunity_set import NO_TRADE_OPPORTUNITY
from .evaluation import Book3Evaluators, day_sheet
from .shadow_file import Widths
from .strategies import Book3Strategies


def common_widths(common: CommonPack, widths: Widths) -> dict[str, list[float]]:
    """Each common opportunity's version widths (the only widths a shadow take may name); one whose version cannot be
    read is left out, as the shadow file then records "no decision" for it."""
    found = {}
    for opportunity in common.body.get("opportunities", ()):
        if opportunity["opportunity_id"] == NO_TRADE_OPPORTUNITY["opportunity_id"]:
            continue
        allowed = widths(opportunity["strategy"], opportunity["version"])
        if allowed is not None:
            found[opportunity["opportunity_id"]] = [float(w) for w in allowed]
    return found


class Book3Sheet(BookSheet):
    def __init__(self, strategies: Book3Strategies, evaluators: Book3Evaluators,
                 inputs: Callable[[date, CommonPack], Book1Day], head: Callable[[], str], widths: Widths):  # fmt: skip
        """`inputs(day, common)`: D2's inputs at the cutoff from the pack's own snapshot and Book 3's account."""
        self.strategies, self.evaluators, self.inputs, self.head, self.widths = (
            strategies,
            evaluators,
            inputs,
            head,
            widths,
        )

    def sheet(self, book: str, day: date, common: CommonPack) -> Mapping:
        tradable = self.strategies.on(day, self.head())
        today = self.inputs(day, common)
        evaluator, _ = self.evaluators.with_picks(())
        evaluation = evaluator.evaluate(day, tradable.snapshot.playbook(), today.market, today.features, today.book,
                                        today.counts, today.shadow)  # fmt: skip
        return day_sheet(day, evaluation, tradable.snapshot.commit, common_widths(common, self.widths))
