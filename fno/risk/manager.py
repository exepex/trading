"""The risk manager (story C2): every rule checks the proposal against the proposal's own book only.

A trade may open only when every rule passes. Every rule runs, so a refusal shows all its reasons. An unusable input
(a missing quote or margin, an open trade without terms, a malformed owner override) refuses the trade with the input's
problem as the reason: the check fails closed, never open. The decision record carries the stressed-margin method in
force and any stale marks, so the judge can reproduce it.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from .inputs import Market, Proposal, RiskBook
from .verdict import RiskRule, RiskVerdict

INPUT_CHECK = "inputs"


@dataclass(frozen=True)
class RiskDecision:
    book: str
    trade_id: str
    day: str
    verdicts: tuple[RiskVerdict, ...]
    stressed_margin: Mapping[str, str]
    stale_marks: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return all(v.ok for v in self.verdicts)

    @property
    def reasons(self) -> list[str]:
        return [f"{v.rule}: {v.reason}" for v in self.verdicts if not v.ok]

    def record(self) -> dict:
        return {
            "book": self.book,
            "trade_id": self.trade_id,
            "day": self.day,
            "ok": self.ok,
            "stressed_margin": dict(self.stressed_margin),
            "stale_marks": list(self.stale_marks),
            "verdicts": [
                {"rule": v.rule, "ok": v.ok, "reason": v.reason, "numbers": dict(v.numbers)} for v in self.verdicts
            ],
        }


def _input_verdict(proposal: Proposal, book: RiskBook) -> RiskVerdict:
    if any(t.trade_id == proposal.trade_id for t in book.open_trades):
        return RiskVerdict(INPUT_CHECK, False, f"trade {proposal.trade_id} is already open in {book.name}")
    return RiskVerdict(INPUT_CHECK, True, "proposal is new to this book")


def _checked(rule: RiskRule, proposal: Proposal, book: RiskBook, market: Market) -> RiskVerdict:
    try:
        return rule.check(proposal, book, market)
    except ValueError as problem:  # every input error (RiskInputError, MissingMark, a malformed row) fails closed
        return RiskVerdict(rule.name, False, f"refused, input not usable: {problem}")


class RiskManager:
    def __init__(self, rules: Sequence[RiskRule], stressed_margin: Mapping[str, str]):
        self.rules, self.stressed_margin = tuple(rules), dict(stressed_margin)

    def evaluate(self, proposal: Proposal, book: RiskBook, market: Market) -> RiskDecision:
        verdicts = (_input_verdict(proposal, book), *(_checked(r, proposal, book, market) for r in self.rules))
        return RiskDecision(
            book.name, proposal.trade_id, market.day.isoformat(), verdicts, self.stressed_margin, book.state.stale_marks
        )
