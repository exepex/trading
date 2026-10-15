"""The account-level caps of design 6.2 (story C5), one rule class each, on the account's maximum losses.

Each cap adds the proposal's maximum loss to the maximum losses already open (or opened today) and passes at its limit,
refusing beyond it, as C2's rules do. A cap only refuses: it never resizes a proposal, so it can never enlarge a trade.
An unmapped bucket, a held position that is not defined risk or an open trade with no known first-fill day is an input
error, and the trade is refused (design 6.1a: fail closed). The paper-account rule refuses every trade of a book that
opened with any other cash than `risk.paper_account_rs`, so an account opened on the old Rs 5 lakh is never traded on
silently.
"""

from __future__ import annotations

from collections.abc import Callable

from .inputs import Market, Proposal, RiskBook, RiskInputError
from .open_risk import PositionRisk, PositionRisks
from .verdict import RiskRule, RiskVerdict, rupees

Selector = Callable[[PositionRisk, PositionRisk, Market], bool]  # (open position, proposal, market) -> counted?


class MaxLossCap(RiskRule):
    """The maximum losses of the positions a selector counts, the proposal's included, at most the limit."""

    what: str
    selector: Selector

    def __init__(self, risks: PositionRisks, limit_rs: float):
        self.risks, self.limit_rs = risks, limit_rs

    def counted(self, proposal: Proposal, book: RiskBook, market: Market) -> list[PositionRisk]:
        *held, own = self.risks.all(proposal, book, market)
        return [p for p in held if self.selector(p, own, market)] + [own]

    def check(self, proposal: Proposal, book: RiskBook, market: Market) -> RiskVerdict:
        counted = self.counted(proposal, book, market)
        own, total = counted[-1], sum(p.max_loss_rs for p in counted)
        ok = total <= self.limit_rs
        where = self.what.format(bucket=own.bucket)
        reason = (
            f"{where}: maximum losses {rupees(total)} with this trade's {rupees(own.max_loss_rs)} are "
            f"{'within' if ok else 'above'} the cap {rupees(self.limit_rs)}"
        )
        return self.verdict(
            ok,
            reason,
            bucket=str(own.bucket),
            proposal_max_loss_rs=own.max_loss_rs,
            counted_max_loss_rs={p.trade_id: p.max_loss_rs for p in counted},
            total_rs=total,
            limit_rs=self.limit_rs,
        )


def _same_bucket(held: PositionRisk, own: PositionRisk, market: Market) -> bool:
    return held.bucket == own.bucket


def _any(held: PositionRisk, own: PositionRisk, market: Market) -> bool:
    return True


def _opened_today(held: PositionRisk, own: PositionRisk, market: Market) -> bool:
    if held.opened_on is None:
        raise RiskInputError(f"open trade {held.trade_id} has no recorded first-fill day")
    return held.opened_on == market.day


class BucketCap(MaxLossCap):
    """One bucket's open maximum losses (design 6.2: Rs 30,000, the old 3-trade limit applied per correlated group)."""

    name, what, selector = "bucket_cap", "bucket {bucket}", staticmethod(_same_bucket)


class OpenRiskCap(MaxLossCap):
    """The whole book's open maximum losses (Rs 1.5 lakh): a cap on new entries, never a stop on open trades."""

    name, what, selector = "open_risk_cap", "all open positions", staticmethod(_any)


class NewRiskPerDay(MaxLossCap):
    """The maximum losses of the trades opened this session (Rs 50,000), the proposal's included."""

    name, what, selector = "new_risk_per_day", "trades opened this session", staticmethod(_opened_today)


class PaperAccountSize(RiskRule):
    """The book opened with the owner's paper account (Rs 20 lakh, owner 14 Oct 2026) and with no other amount."""

    name = "paper_account"

    def __init__(self, paper_account_rs: float):
        self.paper_account_rs = paper_account_rs

    def check(self, proposal: Proposal, book: RiskBook, market: Market) -> RiskVerdict:
        opened = book.state.starting_cash
        ok = opened == self.paper_account_rs
        reason = f"{book.name} opened with {rupees(opened)}; the paper account is {rupees(self.paper_account_rs)}" + (
            "" if ok else ": no trade until the owner decides how this account is reopened"
        )
        return self.verdict(ok, reason, opened_with_rs=opened, paper_account_rs=self.paper_account_rs)
