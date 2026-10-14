"""What C4 checks (story C4): one proposed trade as plain values, and the result of one check with its numbers."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date, datetime

from .validity_money import ProposedLeg


@dataclass(frozen=True)
class ValidityLeg:
    contract: str
    expiry: str  # ISO date
    leg: ProposedLeg  # strike, type, side and the entry price the proposal used


@dataclass(frozen=True)
class ValidityProposal:
    book: str
    opportunity_id: str
    day: date
    cutoff: datetime  # the decision cutoff, time zone aware
    expiry: str  # the opportunity's expiry, ISO
    structure: str  # SF, SC or BF
    width: float
    lots: int
    lot_size: int
    legs: tuple[ValidityLeg, ...]
    claimed_max_loss: float
    risk_verdicts_ok: bool  # every C2 verdict recorded for the trade passed
    open_before: int  # the book's open trades before this one, counting trades chosen earlier the same day
    rule_sha256: str  # the version fingerprint the decision used
    strategy: object | None = None  # the playbook version (playbook mode)
    approved: frozenset[tuple[str, int]] = field(default_factory=frozenset)  # versions tradable on the day

    @property
    def units(self) -> int:
        return self.lots * self.lot_size


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    reason: str
    numbers: Mapping[str, object] = field(default_factory=dict)

    def record(self) -> dict:
        return {"check": self.name, "ok": self.ok, "reason": self.reason, "numbers": dict(self.numbers)}
