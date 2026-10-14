"""C4 inside the decision run (story D3's `validity.c4`, story C4): every trade D2 chose for the book is checked by
an independent validator before its record is written. A failure blocks the trade: its record keeps D2's outcome
and says "no trade, blocked by C4", and the day's chosen list leaves it out. Shadow outcomes and unchosen candidates
are not trades, so they are not checked. The same function runs in a replay, so the result is reproduced too."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING, Protocol

from ..constants import Decision

if TYPE_CHECKING:  # C4's validator imports this module and must not load D2's cost and structure code (story C4)
    from ..risk.inputs import Market, RiskBook
    from .loader import Playbook
    from .outcomes import DayEvaluation, Outcome

BLOCKED = "blocked by C4 hard validity"


@dataclass(frozen=True)
class ValidityResult:
    ok: bool
    record: dict  # every check with its numbers
    reason: str  # the failed checks, empty when it passed


class TradeValidator(Protocol):
    def validate(
        self, day: date, outcome: Outcome, market: Market, playbook: Playbook, open_before: int
    ) -> ValidityResult: ...


def validate_chosen(
    evaluation: DayEvaluation, validator: TradeValidator | None, market: Market, playbook: Playbook, book: RiskBook
) -> Mapping[str, ValidityResult]:
    """Each chosen book trade's C4 result by opportunity ID (empty without a validator). The day is the evaluation's
    own, never the market's: a stale market is then checked against the day's capture and fails."""
    if validator is None:
        return {}
    chosen = sorted(
        (o for o in evaluation.outcomes if o.decision == Decision.CHOSEN), key=lambda o: o.opportunity.opportunity_id
    )
    day, opened = date.fromisoformat(evaluation.day), len(book.open_trades)
    return {
        o.opportunity.opportunity_id: validator.validate(day, o, market, playbook, opened + n)
        for n, o in enumerate(chosen)
    }
