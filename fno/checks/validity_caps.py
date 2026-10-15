"""Story C5's caps as C4 recomputes them (judge 83: every C2 limit, with C4's own arithmetic): the paper account size,
and the bucket, open-risk and new-risk-per-day caps on sums of maximum losses.

Nothing here comes from C2 (`fno.risk`). A position's bucket is its contracts' underlying (the symbol's letters before
its first digit, NIFTY or BANKNIFTY) and its structure's side from `bucket_sides` in config.yaml. A held position's
maximum loss is C4's own: its cash so far plus its worst value at expiry on C4's one-point grid between its outer
strikes, plus each leg's exit pad and exit charges at that level (where levels tie, the larger charges), never below
zero; a tail with more options sold than bought is not defined risk and fails. The proposal's is `validity_money`'s.
Contract strikes come from the committed snapshot, so an open contract missing from it fails the check."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date

from ..constants import BUCKET_INDEX_GROUPS
from .validity_account import AccountFacts, Position
from .validity_chain import PricedChain
from .validity_money import BUY, PAD, SELL, ProposedLeg, expiry_grid, order_charge
from .validity_pricing import PricingProblem
from .validity_proposal import CheckResult
from .validity_settings import CapLimits

LOSS_DECIMALS = 6


class CapProblem(ValueError):
    """A position C4 cannot place in a bucket or measure: the cap check fails closed."""


@dataclass(frozen=True)
class Exposure:
    trade_id: str
    bucket: tuple[str, str]  # (underlying group, side)
    max_loss: float
    opened_on: date | None


def _underlying(contract: str) -> str:
    digits = [i for i, char in enumerate(contract) if char.isdigit()]
    return contract[: digits[0]] if digits else contract


def bucket_of(structure: str | None, contracts, sides: Mapping[str, str]) -> tuple[str, str]:
    groups = {_underlying(c) for c in contracts}
    if len(groups) != 1 or next(iter(groups)) not in BUCKET_INDEX_GROUPS or structure not in sides:
        raise CapProblem(f"unmapped bucket: structure {structure!r} on underlyings {sorted(groups)}")
    return next(iter(groups)), sides[structure]


def held_max_loss(position: Position, chain: PricedChain, table: Mapping[str, float]) -> float:
    legs = []
    for contract, units in position.units.items():
        if contract not in chain.quotes:
            raise PricingProblem(f"{contract} is not in the snapshot: its strike is unknown")
        _, strike, kind = chain.quotes[contract][0]
        legs.append((ProposedLeg(strike, kind, 1 if units > 0 else -1, 0.0), abs(units)))
    if not legs:
        return 0.0
    for kind in ("CE", "PE"):
        if sum(leg.side * n for leg, n in legs if leg.kind == kind) < 0:
            raise CapProblem(f"{position.trade_id}: more {kind} sold than bought, its loss is not capped")

    def exit_charges(level: float) -> float:
        return sum(
            order_charge(leg.value_at_expiry(level) + (PAD if leg.side < 0 else -PAD), n, BUY if leg.side < 0 else SELL,
                         table)
            for leg, n in legs
        )  # fmt: skip

    worst = max(
        (round(-sum(leg.side * n * leg.value_at_expiry(level) for leg, n in legs), LOSS_DECIMALS), exit_charges(level))
        for level in expiry_grid([leg for leg, _ in legs])
    )
    return max(worst[0] - position.cash_flow + PAD * sum(n for _, n in legs) + worst[1], 0.0)


def _cap(name: str, counted: Sequence[Exposure], limit: float, what: str) -> CheckResult:
    total = sum(e.max_loss for e in counted)
    numbers = {"what": what, "total_rs": round(total, 2), "limit_rs": limit,
               "counted_rs": {e.trade_id: round(e.max_loss, 2) for e in counted}}  # fmt: skip
    reason = f"{what}: maximum losses Rs {total:,.2f} against the cap Rs {limit:,.0f}"
    return CheckResult(name, total <= limit, reason, numbers)


class CapChecks:
    def __init__(self, caps: CapLimits, rules: Sequence[str], table: Mapping[str, float]):
        self.caps, self.rules, self.table = caps, tuple(rules), dict(table)

    def exposure(self, position: Position, chain: PricedChain) -> Exposure:
        structure = position.terms[0] if position.terms else None
        bucket = bucket_of(structure, position.units, self.caps.sides)
        return Exposure(position.trade_id, bucket, held_max_loss(position, chain, self.table), position.opened_on)

    def checks(self, held: Sequence[Position], own: Exposure, chain: PricedChain, day: date) -> list[CheckResult]:
        """`held`: open trades and those chosen earlier the same day; `own`: the proposal's bucket and maximum loss."""
        others = [self.exposure(p, chain) for p in held]
        if any(e.opened_on is None for e in others):
            raise CapProblem("an open trade has no recorded first fill day")
        results = []
        if "bucket_cap" in self.rules:
            same = [e for e in others if e.bucket == own.bucket] + [own]
            results.append(_cap("bucket_cap", same, self.caps.bucket, f"bucket {'/'.join(own.bucket)}"))
        if "open_risk_cap" in self.rules:
            results.append(_cap("open_risk_cap", [*others, own], self.caps.open_risk, "all open positions"))
        if "new_risk_per_day" in self.rules:
            today = [e for e in others if e.opened_on == day] + [own]
            results.append(_cap("new_risk_per_day", today, self.caps.new_risk_per_day, "trades opened this session"))
        return results


def paper_account_check(account: AccountFacts, paper_account: float) -> CheckResult:
    opened = account.closed_equity[0][1]
    reason = f"the account opened with Rs {opened:,.2f}; the profile's paper account is Rs {paper_account:,.2f}"
    return CheckResult("paper_account", opened == paper_account, reason, {"opened_with_rs": opened})
